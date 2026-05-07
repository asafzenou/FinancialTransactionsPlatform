"""
File validation and parsing for transaction uploads.

Handles:
- File type validation
- File content parsing (CSV, Excel)
- Column validation
"""

from io import BytesIO
import pandas as pd
from fastapi import HTTPException


def validate_file_type(filename: str) -> None:
    """Validate that file has an acceptable extension."""
    filename_lower = filename.lower()
    if not (filename_lower.endswith('.xlsx') or filename_lower.endswith('.xls') or filename_lower.endswith('.csv')):
        raise HTTPException(
            status_code=400,
            detail="File must be .xlsx, .xls, or .csv"
        )


def parse_file_content(content: bytes, filename: str) -> pd.DataFrame:
    """Parse file content into DataFrame based on file type."""
    filename_lower = filename.lower()
    if filename_lower.endswith('.csv'):
        return pd.read_csv(BytesIO(content))
    else:
        return pd.read_excel(BytesIO(content))


def validate_required_columns(df: pd.DataFrame) -> None:
    """Validate that DataFrame contains all required columns."""
    required_cols = ['ClientId', 'TransactionId', 'ISIN', 'Action', 'Quantity', 'Price', 'Timestamp']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise HTTPException(
            status_code=400,
            detail=f"Missing columns: {', '.join(missing_cols)}"
        )
