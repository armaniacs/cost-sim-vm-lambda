"""
環境変数バリデーション機能

PBI-SEC-A: エンタープライズ認証・認可システムの一部として、
セキュリティ関連の必須環境変数をバリデーションする機能を提供。
"""

import os
import sys
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class EnvVarRequirement:
    """環境変数要件の定義"""
    name: str
    description: str
    required: bool = True
    default_value: Optional[str] = None
    validation_regex: Optional[str] = None


class EnvironmentValidator:
    """環境変数バリデーター"""
    
    # セキュリティ関連の必須環境変数定義
    SECURITY_ENV_VARS = [
        EnvVarRequirement(
            name="SECRET_KEY",
            description="Flask application secret key for session security",
            required=True
        ),
        EnvVarRequirement(
            name="CSRF_SECRET_KEY", 
            description="CSRF protection secret key",
            required=True
        ),
        EnvVarRequirement(
            name="JWT_SECRET_KEY",
            description="JWT token signing secret key", 
            required=True
        )
    ]
    
    # オプション環境変数
    OPTIONAL_ENV_VARS = [
        EnvVarRequirement(
            name="FLASK_ENV",
            description="Flask environment (development/testing/production)",
            required=False,
            default_value="development"
        ),
        EnvVarRequirement(
            name="PORT",
            description="Application server port",
            required=False,
            default_value="5001"
        ),
        EnvVarRequirement(
            name="HOST",
            description="Application server host",
            required=False,
            default_value="0.0.0.0"
        )
    ]
    
    def __init__(self):
        self.validation_errors: List[str] = []
        self.validation_warnings: List[str] = []
    
    def validate_security_environment(self) -> bool:
        """
        セキュリティ関連環境変数のバリデーション
        
        Returns:
            bool: バリデーション成功の場合True、失敗の場合False
        """
        self.validation_errors.clear()
        self.validation_warnings.clear()
        
        # 必須環境変数チェック
        for env_var in self.SECURITY_ENV_VARS:
            value = os.environ.get(env_var.name)
            
            if not value:
                self.validation_errors.append(
                    f"Required environment variable '{env_var.name}' is not set. "
                    f"Description: {env_var.description}"
                )
            else:
                # セキュリティチェック
                self._validate_security_value(env_var.name, value)
        
        # オプション環境変数の警告チェック
        for env_var in self.OPTIONAL_ENV_VARS:
            value = os.environ.get(env_var.name)
            if not value and env_var.default_value:
                self.validation_warnings.append(
                    f"Optional environment variable '{env_var.name}' not set, "
                    f"using default: '{env_var.default_value}'"
                )
        
        return len(self.validation_errors) == 0
    
    def _validate_security_value(self, name: str, value: str) -> None:
        """セキュリティ値のバリデーション"""
        # ハードコードされたデフォルト値チェック
        dangerous_values = [
            "dev-secret-key-change-in-production",
            "csrf-secret-key-change-in-production", 
            "your-secret-key-change-in-production",
            "secret",
            "password",
            "changeme",
            "default"
        ]
        
        if value.lower() in dangerous_values:
            self.validation_errors.append(
                f"Environment variable '{name}' contains a dangerous default value: '{value}'. "
                f"Please set a secure random value."
            )
        
        # 最小長チェック
        if len(value) < 16:
            self.validation_errors.append(
                f"Environment variable '{name}' is too short (minimum 16 characters required). "
                f"Current length: {len(value)}"
            )
        
        # エントロピーチェック（簡易）
        if self._has_low_entropy(value):
            self.validation_warnings.append(
                f"Environment variable '{name}' may have low entropy. "
                f"Consider using a more random value."
            )
    
    def _has_low_entropy(self, value: str) -> bool:
        """簡易エントロピーチェック"""
        # 同じ文字の繰り返しチェック
        if len(set(value)) < len(value) * 0.5:
            return True
        
        # 連続文字チェック  
        consecutive_count = 0
        for i in range(len(value) - 1):
            if ord(value[i+1]) == ord(value[i]) + 1:
                consecutive_count += 1
                if consecutive_count > 3:
                    return True
            else:
                consecutive_count = 0
        
        return False
    
    def get_validation_summary(self) -> Dict[str, any]:
        """バリデーション結果のサマリーを取得"""
        return {
            "valid": len(self.validation_errors) == 0,
            "errors": self.validation_errors,
            "warnings": self.validation_warnings,
            "environment": os.environ.get("FLASK_ENV", "development"),
            "checked_variables": [var.name for var in self.SECURITY_ENV_VARS]
        }
    
    def print_validation_results(self) -> None:
        """バリデーション結果をコンソールに出力"""
        if self.validation_errors:
            print("🔴 SECURITY ENVIRONMENT VALIDATION FAILED")
            print("=" * 50)
            for error in self.validation_errors:
                print(f"❌ {error}")
            print()
            print("Please set the required environment variables before starting the application.")
            print("Example:")
            print("export SECRET_KEY=$(openssl rand -hex 32)")
            print("export CSRF_SECRET_KEY=$(openssl rand -hex 32)")  
            print("export JWT_SECRET_KEY=$(openssl rand -hex 32)")
            print()
        
        if self.validation_warnings:
            print("⚠️  SECURITY WARNINGS")
            print("=" * 30)
            for warning in self.validation_warnings:
                print(f"⚠️  {warning}")
            print()
        
        if not self.validation_errors and not self.validation_warnings:
            print("✅ Security environment validation passed")
    
    def validate_and_exit_on_failure(self) -> None:
        """
        バリデーション実行し、失敗時はアプリケーション終了
        
        アプリケーション起動時に呼び出して、
        セキュリティ要件を満たさない場合は起動を停止する。
        """
        is_valid = self.validate_security_environment()
        
        if not is_valid:
            self.print_validation_results()
            print("🚫 Application startup aborted due to security validation failures.")
            sys.exit(1)
        
        # 警告がある場合は表示するが、アプリケーションは継続
        if self.validation_warnings:
            self.print_validation_results()


def validate_environment_or_exit() -> None:
    """
    環境変数バリデーション実行（失敗時は終了）
    
    アプリケーション起動時に呼び出す関数。
    セキュリティ関連の環境変数が適切に設定されていない場合、
    アプリケーションの起動を停止する。
    """
    validator = EnvironmentValidator()
    validator.validate_and_exit_on_failure()


def get_environment_status() -> Dict[str, any]:
    """現在の環境変数状態を取得"""
    validator = EnvironmentValidator()
    validator.validate_security_environment()
    return validator.get_validation_summary()


if __name__ == "__main__":
    # 単体テスト用のエントリーポイント
    validate_environment_or_exit()