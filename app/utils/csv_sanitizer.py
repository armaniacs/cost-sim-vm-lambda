"""
CSV sanitization utilities for security enhancement
PBI-SEC-ESSENTIAL implementation
"""

from typing import Any


def sanitize_csv_field(field: Any) -> str:
    """
    Sanitize field for safe CSV output to prevent CSV injection attacks

    CSV injection occurs when malicious formulas are embedded in CSV files.
    When opened in spreadsheet applications, these formulas can execute arbitrary
    commands.

    Args:
        field: Field value to sanitize

    Returns:
        Sanitized string safe for CSV output
    """
    if field is None:
        return ""

    # Convert to string
    field_str = str(field)

    # Remove dangerous CSV injection characters from the beginning
    dangerous_chars = ["=", "+", "-", "@", "\t", "\r"]
    while field_str and field_str[0] in dangerous_chars:
        field_str = field_str[1:]

    # Additional sanitization for formula indicators
    # Remove potential formula patterns
    formula_patterns = ["=cmd", "=system", "=shell", "=exec"]
    field_lower = field_str.lower()
    for pattern in formula_patterns:
        if field_lower.startswith(pattern):
            field_str = field_str[1:]  # Remove leading =
            break

    # Escape quotes and add quotes if contains special characters
    if "," in field_str or "\n" in field_str or "\r" in field_str or '"' in field_str:
        # Escape existing quotes by doubling them
        field_str = field_str.replace('"', '""')
        # Wrap in quotes
        field_str = f'"{field_str}"'

    return field_str


def sanitize_csv_row(row: list) -> list:
    """
    Sanitize an entire CSV row

    Args:
        row: List of field values

    Returns:
        List of sanitized field values
    """
    return [sanitize_csv_field(field) for field in row]


def create_safe_csv_content(headers: list, rows: list) -> str:
    """
    Create safe CSV content with sanitized headers and data

    Args:
        headers: List of header strings
        rows: List of row data (each row is a list of values)

    Returns:
        Complete CSV content as string
    """
    csv_lines = []

    # Sanitize and add headers
    sanitized_headers = sanitize_csv_row(headers)
    csv_lines.append(",".join(sanitized_headers))

    # Sanitize and add data rows
    for row in rows:
        sanitized_row = sanitize_csv_row(row)
        csv_lines.append(",".join(sanitized_row))

    return "\n".join(csv_lines)
