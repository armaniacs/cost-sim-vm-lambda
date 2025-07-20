"""
Unit tests for PBI-SEC-A Environment Validator

環境変数バリデーション機能の単体テスト
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock

from app.security.env_validator import (
    EnvironmentValidator,
    validate_environment_or_exit,
    get_environment_status,
    EnvVarRequirement
)


class TestEnvironmentValidator:
    """EnvironmentValidator クラスの単体テスト"""

    def setup_method(self):
        """各テストメソッド実行前のセットアップ"""
        self.validator = EnvironmentValidator()

    def test_env_var_requirement_creation(self):
        """EnvVarRequirement データクラスのテスト"""
        req = EnvVarRequirement(
            name="TEST_VAR",
            description="Test variable",
            required=True
        )
        
        assert req.name == "TEST_VAR"
        assert req.description == "Test variable"
        assert req.required is True
        assert req.default_value is None

    def test_validate_security_environment_success(self):
        """セキュリティ環境変数バリデーション成功ケース"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-enough-length',
            'CSRF_SECRET_KEY': 'test-csrf-secret-key-with-enough-length',
            'JWT_SECRET_KEY': 'test-jwt-secret-key-with-enough-length'
        }):
            result = self.validator.validate_security_environment()
            
            assert result is True
            assert len(self.validator.validation_errors) == 0

    def test_validate_security_environment_missing_variables(self):
        """必須環境変数が未設定の場合のテスト"""
        with patch.dict(os.environ, {}, clear=True):
            result = self.validator.validate_security_environment()
            
            assert result is False
            assert len(self.validator.validation_errors) == 3  # 3つの必須変数
            
            # エラーメッセージの確認
            error_messages = ' '.join(self.validator.validation_errors)
            assert 'SECRET_KEY' in error_messages
            assert 'CSRF_SECRET_KEY' in error_messages
            assert 'JWT_SECRET_KEY' in error_messages

    def test_validate_security_environment_dangerous_values(self):
        """危険なデフォルト値の検出テスト"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'dev-secret-key-change-in-production',
            'CSRF_SECRET_KEY': 'csrf-secret-key-change-in-production',
            'JWT_SECRET_KEY': 'your-secret-key-change-in-production'
        }):
            result = self.validator.validate_security_environment()
            
            assert result is False
            assert len(self.validator.validation_errors) >= 3
            
            # 危険な値の検出確認
            error_messages = ' '.join(self.validator.validation_errors)
            assert 'dangerous default value' in error_messages

    def test_validate_security_environment_short_values(self):
        """短すぎるシークレット値の検出テスト"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'short',  # 16文字未満
            'CSRF_SECRET_KEY': 'short',
            'JWT_SECRET_KEY': 'short'
        }):
            result = self.validator.validate_security_environment()
            
            assert result is False
            assert len(self.validator.validation_errors) >= 3
            
            # 短すぎる値の検出確認
            error_messages = ' '.join(self.validator.validation_errors)
            assert 'too short' in error_messages

    def test_has_low_entropy_detection(self):
        """低エントロピーシークレットの検出テスト"""
        # 同じ文字の繰り返し
        low_entropy_1 = "aaaaaaaaaaaaaaaa"  # 16文字、すべて同じ
        assert self.validator._has_low_entropy(low_entropy_1) is True
        
        # 連続文字
        low_entropy_2 = "abcdefghijklmnop"  # 連続した文字
        assert self.validator._has_low_entropy(low_entropy_2) is True
        
        # 適切なランダム文字列
        good_entropy = "g7x9K2mR8pQ4sL1n"
        assert self.validator._has_low_entropy(good_entropy) is False

    def test_get_validation_summary(self):
        """バリデーション結果サマリーのテスト"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-enough-length'
        }):
            self.validator.validate_security_environment()
            summary = self.validator.get_validation_summary()
            
            assert 'valid' in summary
            assert 'errors' in summary
            assert 'warnings' in summary
            assert 'environment' in summary
            assert 'checked_variables' in summary
            
            assert isinstance(summary['checked_variables'], list)
            assert 'SECRET_KEY' in summary['checked_variables']

    @patch('builtins.print')
    def test_print_validation_results_with_errors(self, mock_print):
        """エラーがある場合のバリデーション結果出力テスト"""
        with patch.dict(os.environ, {}, clear=True):
            self.validator.validate_security_environment()
            self.validator.print_validation_results()
            
            # print が呼ばれたことを確認
            assert mock_print.called
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            print_output = ' '.join(print_calls)
            
            assert 'SECURITY ENVIRONMENT VALIDATION FAILED' in print_output
            assert 'SECRET_KEY' in print_output

    @patch('builtins.print')
    def test_print_validation_results_success(self, mock_print):
        """成功時のバリデーション結果出力テスト"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-enough-length',
            'CSRF_SECRET_KEY': 'test-csrf-secret-key-with-enough-length',
            'JWT_SECRET_KEY': 'test-jwt-secret-key-with-enough-length'
        }):
            self.validator.validate_security_environment()
            self.validator.print_validation_results()
            
            # print が呼ばれたことを確認
            assert mock_print.called
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            print_output = ' '.join(print_calls)
            
            assert 'Security environment validation passed' in print_output

    @patch('sys.exit')
    @patch('builtins.print')
    def test_validate_and_exit_on_failure(self, mock_print, mock_exit):
        """バリデーション失敗時の終了処理テスト"""
        with patch.dict(os.environ, {}, clear=True):
            self.validator.validate_and_exit_on_failure()
            
            # sys.exit(1) が呼ばれたことを確認
            mock_exit.assert_called_once_with(1)

    def test_validate_and_exit_on_success(self):
        """バリデーション成功時は終了しないテスト"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-enough-length',
            'CSRF_SECRET_KEY': 'test-csrf-secret-key-with-enough-length',
            'JWT_SECRET_KEY': 'test-jwt-secret-key-with-enough-length'
        }):
            # 例外が発生しないことを確認
            try:
                self.validator.validate_and_exit_on_failure()
            except SystemExit:
                pytest.fail("validate_and_exit_on_failure should not exit on success")


class TestGlobalFunctions:
    """グローバル関数のテスト"""

    @patch('sys.exit')
    @patch('builtins.print')
    def test_validate_environment_or_exit_failure(self, mock_print, mock_exit):
        """グローバル関数での失敗時終了テスト"""
        with patch.dict(os.environ, {}, clear=True):
            validate_environment_or_exit()
            mock_exit.assert_called_once_with(1)

    def test_validate_environment_or_exit_success(self):
        """グローバル関数での成功時テスト"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-enough-length',
            'CSRF_SECRET_KEY': 'test-csrf-secret-key-with-enough-length',
            'JWT_SECRET_KEY': 'test-jwt-secret-key-with-enough-length'
        }):
            # 例外が発生しないことを確認
            try:
                validate_environment_or_exit()
            except SystemExit:
                pytest.fail("validate_environment_or_exit should not exit on success")

    def test_get_environment_status(self):
        """環境ステータス取得関数のテスト"""
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-enough-length',
            'CSRF_SECRET_KEY': 'test-csrf-secret-key-with-enough-length',
            'JWT_SECRET_KEY': 'test-jwt-secret-key-with-enough-length'
        }):
            status = get_environment_status()
            
            assert isinstance(status, dict)
            assert 'valid' in status
            assert 'errors' in status
            assert 'warnings' in status
            assert status['valid'] is True


class TestEdgeCases:
    """エッジケースのテスト"""

    def test_partial_environment_variables(self):
        """一部の環境変数のみ設定されている場合のテスト"""
        validator = EnvironmentValidator()
        
        with patch.dict(os.environ, {
            'SECRET_KEY': 'test-secret-key-with-enough-length'
            # CSRF_SECRET_KEY, JWT_SECRET_KEY は未設定
        }):
            result = validator.validate_security_environment()
            
            assert result is False
            assert len(validator.validation_errors) == 2  # 2つが未設定

    def test_environment_variables_with_whitespace(self):
        """空白文字のみの環境変数のテスト"""
        validator = EnvironmentValidator()
        
        with patch.dict(os.environ, {
            'SECRET_KEY': '   ',  # 空白のみ
            'CSRF_SECRET_KEY': '',  # 空文字列
            'JWT_SECRET_KEY': 'test-jwt-secret-key-with-enough-length'
        }):
            result = validator.validate_security_environment()
            
            assert result is False
            # 空白のみ、空文字列は未設定として扱われる