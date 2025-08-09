"""
Unit tests for CSV sanitization utilities
Tests security-critical CSV injection prevention functions
"""

import pytest

try:
    from app.utils.csv_sanitizer import (
        create_safe_csv_content,
        sanitize_csv_field,
        sanitize_csv_row,
    )
except ImportError as e:
    pytest.skip(f"CSV sanitizer module not available: {e}", allow_module_level=True)


class TestCSVFieldSanitization:
    """Test CSV field sanitization"""

    def test_sanitize_csv_field_none(self):
        """Test sanitization of None values"""
        result = sanitize_csv_field(None)
        assert result == ""

    def test_sanitize_csv_field_empty_string(self):
        """Test sanitization of empty string"""
        result = sanitize_csv_field("")
        assert result == ""

    def test_sanitize_csv_field_normal_string(self):
        """Test sanitization of normal string"""
        result = sanitize_csv_field("normal text")
        assert result == "normal text"

    def test_sanitize_csv_field_number(self):
        """Test sanitization of number"""
        result = sanitize_csv_field(123.45)
        assert result == "123.45"

    def test_sanitize_csv_field_integer(self):
        """Test sanitization of integer"""
        result = sanitize_csv_field(42)
        assert result == "42"

    def test_sanitize_csv_field_boolean(self):
        """Test sanitization of boolean"""
        result = sanitize_csv_field(True)
        assert result == "True"

        result = sanitize_csv_field(False)
        assert result == "False"


class TestCSVInjectionPrevention:
    """Test CSV injection attack prevention"""

    def test_sanitize_csv_field_formula_equals(self):
        """Test sanitization of formula starting with ="""
        result = sanitize_csv_field("=1+1")
        assert result == "1+1"
        assert not result.startswith("=")

    def test_sanitize_csv_field_formula_plus(self):
        """Test sanitization of formula starting with +"""
        result = sanitize_csv_field("+123-45")
        assert result == "123-45"
        assert not result.startswith("+")

    def test_sanitize_csv_field_formula_minus(self):
        """Test sanitization of formula starting with -"""
        result = sanitize_csv_field("-cmd /c calc")
        assert result == "cmd /c calc"
        assert not result.startswith("-")

    def test_sanitize_csv_field_formula_at(self):
        """Test sanitization of formula starting with @"""
        result = sanitize_csv_field("@SUM(1,2)")
        # The @ is removed, but SUM(1,2) contains parentheses so gets quoted
        assert result == '"SUM(1,2)"'
        # The dangerous @ character should be removed from the original content
        inner_content = result.strip('"')
        assert not inner_content.startswith("@")

    def test_sanitize_csv_field_formula_tab(self):
        """Test sanitization of formula starting with tab"""
        result = sanitize_csv_field("\t=1+1")
        assert result == "1+1"
        assert not result.startswith("\t")

    def test_sanitize_csv_field_formula_carriage_return(self):
        """Test sanitization of formula starting with carriage return"""
        result = sanitize_csv_field("\r=malicious")
        assert result == "malicious"
        assert not result.startswith("\r")

    def test_sanitize_csv_field_multiple_dangerous_chars(self):
        """Test sanitization of multiple dangerous characters"""
        result = sanitize_csv_field("+=@-dangerous")
        assert result == "dangerous"

    def test_sanitize_csv_field_cmd_formula(self):
        """Test sanitization of =cmd formula injection"""
        result = sanitize_csv_field("=cmd|'/c calc'!A0")
        assert result == "cmd|'/c calc'!A0"
        assert not result.startswith("=")

    def test_sanitize_csv_field_system_formula(self):
        """Test sanitization of =system formula injection"""
        result = sanitize_csv_field("=system('rm -rf /')")
        assert result == "system('rm -rf /')"
        assert not result.startswith("=")

    def test_sanitize_csv_field_shell_formula(self):
        """Test sanitization of =shell formula injection"""
        result = sanitize_csv_field("=shell('malicious')")
        assert result == "shell('malicious')"
        assert not result.startswith("=")

    def test_sanitize_csv_field_exec_formula(self):
        """Test sanitization of =exec formula injection"""
        result = sanitize_csv_field("=exec('dangerous')")
        assert result == "exec('dangerous')"
        assert not result.startswith("=")

    def test_sanitize_csv_field_case_insensitive_cmd(self):
        """Test sanitization is case insensitive for CMD"""
        result = sanitize_csv_field("=CMD|'/c calc'!A0")
        assert result == "CMD|'/c calc'!A0"
        assert not result.startswith("=")

    def test_sanitize_csv_field_case_insensitive_system(self):
        """Test sanitization is case insensitive for SYSTEM"""
        result = sanitize_csv_field("=SYSTEM('rm -rf /')")
        assert result == "SYSTEM('rm -rf /')"
        assert not result.startswith("=")


class TestCSVQuotingAndEscaping:
    """Test CSV field quoting and escaping"""

    def test_sanitize_csv_field_with_comma(self):
        """Test field containing comma gets quoted"""
        result = sanitize_csv_field("hello, world")
        assert result == '"hello, world"'
        assert result.startswith('"') and result.endswith('"')

    def test_sanitize_csv_field_with_newline(self):
        """Test field containing newline gets quoted"""
        result = sanitize_csv_field("line1\nline2")
        assert result == '"line1\nline2"'
        assert result.startswith('"') and result.endswith('"')

    def test_sanitize_csv_field_with_carriage_return(self):
        """Test field containing carriage return gets quoted"""
        result = sanitize_csv_field("line1\rline2")
        assert result == '"line1\rline2"'
        assert result.startswith('"') and result.endswith('"')

    def test_sanitize_csv_field_with_quotes(self):
        """Test field containing quotes gets escaped and quoted"""
        result = sanitize_csv_field('say "hello"')
        assert result == '"say ""hello"""'
        # Check that internal quotes are doubled
        assert '""hello""' in result

    def test_sanitize_csv_field_with_multiple_quotes(self):
        """Test field with multiple quotes gets properly escaped"""
        result = sanitize_csv_field('he said "no" and "yes"')
        assert result == '"he said ""no"" and ""yes"""'
        assert result.count('""') == 4  # Two pairs of doubled quotes

    def test_sanitize_csv_field_quotes_only(self):
        """Test field containing only quotes"""
        result = sanitize_csv_field('""""')
        # Four quotes become eight (doubled) plus outer quotes = ten total
        assert result == '""""""""""'

    def test_sanitize_csv_field_complex_case(self):
        """Test complex case with comma, newline, and quotes"""
        result = sanitize_csv_field('Name: "John, Jr.", Age: 30\nCity: NYC')
        expected = '"Name: ""John, Jr."", Age: 30\nCity: NYC"'
        assert result == expected


class TestCSVRowSanitization:
    """Test CSV row sanitization"""

    def test_sanitize_csv_row_empty(self):
        """Test sanitization of empty row"""
        result = sanitize_csv_row([])
        assert result == []

    def test_sanitize_csv_row_normal(self):
        """Test sanitization of normal row"""
        row = ["name", "age", 25, True]
        result = sanitize_csv_row(row)
        expected = ["name", "age", "25", "True"]
        assert result == expected

    def test_sanitize_csv_row_with_injection(self):
        """Test sanitization of row with injection attempts"""
        row = ["=cmd|calc", "+dangerous", "normal", "@formula"]
        result = sanitize_csv_row(row)
        expected = ["cmd|calc", "dangerous", "normal", "formula"]
        assert result == expected

    def test_sanitize_csv_row_with_special_chars(self):
        """Test sanitization of row with special characters"""
        row = ["hello, world", "line1\nline2", 'say "hello"']
        result = sanitize_csv_row(row)
        expected = ['"hello, world"', '"line1\nline2"', '"say ""hello"""']
        assert result == expected

    def test_sanitize_csv_row_mixed_types(self):
        """Test sanitization of row with mixed data types"""
        row = [None, "", 123, 45.67, True, False]
        result = sanitize_csv_row(row)
        expected = ["", "", "123", "45.67", "True", "False"]
        assert result == expected


class TestSafeCSVContentCreation:
    """Test safe CSV content creation"""

    def test_create_safe_csv_content_empty(self):
        """Test creation of CSV with no data"""
        headers = ["name", "age", "city"]
        rows = []
        result = create_safe_csv_content(headers, rows)
        assert result == "name,age,city"

    def test_create_safe_csv_content_normal(self):
        """Test creation of normal CSV content"""
        headers = ["name", "age", "active"]
        rows = [["John", 25, True], ["Jane", 30, False]]
        result = create_safe_csv_content(headers, rows)
        expected_lines = ["name,age,active", "John,25,True", "Jane,30,False"]
        assert result == "\n".join(expected_lines)

    def test_create_safe_csv_content_with_injection(self):
        """Test CSV creation with injection attempts in headers and data"""
        headers = ["=malicious_header", "normal_header", "+bad_header"]
        rows = [
            ["=cmd|calc", "safe_value", "@formula"],
            ["normal", "hello, world", "-dangerous"],
        ]
        result = create_safe_csv_content(headers, rows)
        # Expected format after sanitization
        # Check that dangerous characters are removed
        assert not any(line.startswith("=") for line in result.split("\n"))
        assert not any(line.startswith("+") for line in result.split("\n"))
        assert not any(line.startswith("@") for line in result.split("\n"))
        assert not any(line.startswith("-") for line in result.split("\n"))

    def test_create_safe_csv_content_with_quotes(self):
        """Test CSV creation with quotes in data"""
        headers = ["name", "description"]
        rows = [
            ['John "Johnny" Doe', 'He said "hello world"'],
            ["Jane's Shop", 'Product "A", very good'],
        ]
        result = create_safe_csv_content(headers, rows)
        lines = result.split("\n")

        # Check headers are not quoted (no special chars)
        assert lines[0] == "name,description"

        # Check that quoted fields are properly escaped
        assert 'John ""Johnny"" Doe' in lines[1]
        assert 'He said ""hello world""' in lines[1]
        assert 'Product ""A"", very good' in lines[2]

    def test_create_safe_csv_content_with_mixed_issues(self):
        """Test CSV creation with various security and formatting issues"""
        headers = ["=header1", "normal,header", "+header3"]
        rows = [
            ["=system('rm -rf')", "value, with comma", None],
            [123.45, True, "multi\nline\nvalue"],
            ['quotes"everywhere"here', "@dangerous", "normal"],
        ]
        result = create_safe_csv_content(headers, rows)
        lines = result.split("\n")

        # Verify dangerous characters are removed from field starts
        # Check that headers had dangerous chars removed
        assert "header1" in lines[0]  # =header1 -> header1
        assert "header3" in lines[0]  # +header3 -> header3

        # Check that data fields had dangerous chars removed
        assert "system('rm -rf')" in result  # =system('rm -rf') -> system('rm -rf')
        assert "dangerous" in result  # @dangerous -> dangerous

        # Verify no lines start with raw dangerous characters
        for line in lines:
            if line.strip():  # Skip empty lines
                assert not line.startswith("="), f"Line starts with =: {line}"
                assert not line.startswith("+"), f"Line starts with +: {line}"
                assert not line.startswith("@"), f"Line starts with @: {line}"
                assert not line.startswith("-"), f"Line starts with -: {line}"

        # Verify proper quoting of special content
        assert '"multi\nline\nvalue"' in result
        assert '"quotes""everywhere""here"' in result
        assert '"value, with comma"' in result


class TestSecurityEdgeCases:
    """Test security edge cases and boundary conditions"""

    def test_sanitize_csv_field_only_dangerous_chars(self):
        """Test field containing only dangerous characters"""
        result = sanitize_csv_field("=+@-")
        assert result == ""

    def test_sanitize_csv_field_dangerous_chars_in_middle(self):
        """Test dangerous characters in middle of field (should be preserved)"""
        result = sanitize_csv_field("normal=middle+content@here")
        assert result == "normal=middle+content@here"

    def test_sanitize_csv_field_unicode_content(self):
        """Test field with unicode content"""
        result = sanitize_csv_field("こんにちは世界")
        assert result == "こんにちは世界"

    def test_sanitize_csv_field_unicode_with_injection(self):
        """Test unicode content with injection attempt"""
        result = sanitize_csv_field("=こんにちは")
        assert result == "こんにちは"
        assert not result.startswith("=")

    def test_sanitize_csv_field_very_long_content(self):
        """Test field with very long content"""
        long_content = "a" * 10000
        result = sanitize_csv_field(long_content)
        assert result == long_content
        assert len(result) == 10000

    def test_sanitize_csv_field_very_long_with_injection(self):
        """Test very long field with injection attempt"""
        long_content = "=" + "a" * 10000
        result = sanitize_csv_field(long_content)
        assert result == "a" * 10000  # = removed
        assert len(result) == 10000
        assert not result.startswith("=")

    def test_sanitize_csv_field_whitespace_variations(self):
        """Test various whitespace scenarios"""
        # Leading/trailing spaces should be preserved
        result = sanitize_csv_field("  spaced content  ")
        assert result == "  spaced content  "

        # Dangerous chars at beginning are removed, but spaces prevent detection
        result = sanitize_csv_field("  =dangerous  ")
        # The implementation only removes from the very beginning, so spaces block it
        assert result == "  =dangerous  "

        # But if dangerous char is at actual beginning, it gets removed
        result = sanitize_csv_field("=dangerous with spaces")
        assert result == "dangerous with spaces"

    def test_create_safe_csv_content_large_dataset(self):
        """Test CSV creation with large dataset"""
        headers = ["id", "name", "value"]
        rows = []
        for i in range(1000):
            rows.append([i, f"name_{i}", f"value_{i}"])

        result = create_safe_csv_content(headers, rows)
        lines = result.split("\n")

        # Should have header + 1000 data rows
        assert len(lines) == 1001
        assert lines[0] == "id,name,value"
        assert lines[1] == "0,name_0,value_0"
        assert lines[-1] == "999,name_999,value_999"

    def test_create_safe_csv_content_injection_in_large_dataset(self):
        """Test CSV creation with injection attempts in large dataset"""
        headers = ["id", "command"]
        rows = []
        dangerous_commands = ["=cmd|calc", "+system", "-rm", "@exec"]

        for i in range(100):
            command = dangerous_commands[i % len(dangerous_commands)]
            rows.append([i, f"{command}_{i}"])

        result = create_safe_csv_content(headers, rows)

        # Verify no line starts with dangerous characters
        for line in result.split("\n"):
            # Skip empty lines
            if line.strip():
                fields = line.split(",")
                for field in fields:
                    # Remove quotes to check actual content
                    content = field.strip('"')
                    if content:  # Skip empty fields
                        assert (
                            content[0] not in "=+-@\t\r"
                        ), f"Dangerous start found in: {content}"
