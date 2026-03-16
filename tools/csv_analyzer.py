import os
import json
import pandas as pd
from pathlib import Path
from typing import Optional
from datetime import datetime


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_csv(file_path: str) -> tuple[pd.DataFrame | None, str | None]:
    """Load CSV and return (dataframe, error_message)"""
    path = Path(file_path)
    if not path.exists():
        return None, f"File not found: {file_path}"
    if path.suffix.lower() != ".csv":
        return None, f"File must be a .csv, got: {path.suffix}"
    try:
        df = pd.read_csv(file_path)
        return df, None
    except Exception as e:
        return None, f"Failed to read CSV: {e}"


def _df_to_text(df: pd.DataFrame, max_rows: int = 5) -> str:
    """Convert a DataFrame to a readable text table"""
    return df.head(max_rows).to_string(index=False)


# ── Tool functions ─────────────────────────────────────────────────────────────

def csv_preview(file_path: str, num_rows: int = 5) -> dict:
    """
    Load and preview a CSV file.

    Args:
        file_path: Path to the CSV file
        num_rows:  Number of rows to preview (default 5)

    Returns:
        dict with shape, columns, dtypes, and preview rows
    """
    df, error = _load_csv(file_path)
    if error:
        return {"error": error}

    return {
        "file": Path(file_path).name,
        "shape": {"rows": int(df.shape[0]), "columns": int(df.shape[1])},
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "missing_values": df.isnull().sum().to_dict(),
        "preview": _df_to_text(df, max_rows=num_rows),
        "message": f"Loaded {df.shape[0]} rows × {df.shape[1]} columns",
    }


def csv_summary_stats(file_path: str, columns: Optional[list] = None) -> dict:
    """
    Generate summary statistics for numeric columns in a CSV.

    Args:
        file_path: Path to the CSV file
        columns:   Optional list of column names to analyze (default: all numeric)

    Returns:
        dict with mean, min, max, std, count per column
    """
    df, error = _load_csv(file_path)
    if error:
        return {"error": error}

    # Select columns
    if columns:
        missing = [c for c in columns if c not in df.columns]
        if missing:
            return {"error": f"Columns not found: {missing}. Available: {list(df.columns)}"}
        df = df[columns]

    numeric_df = df.select_dtypes(include="number")
    if numeric_df.empty:
        return {"error": "No numeric columns found for statistics."}

    stats = numeric_df.describe().round(4)
    result = {}
    for col in stats.columns:
        result[col] = {
            "count": int(stats[col]["count"]),
            "mean": float(stats[col]["mean"]),
            "std": float(stats[col]["std"]),
            "min": float(stats[col]["min"]),
            "25%": float(stats[col]["25%"]),
            "50%": float(stats[col]["50%"]),
            "75%": float(stats[col]["75%"]),
            "max": float(stats[col]["max"]),
        }

    # Value counts for categorical columns
    cat_df = df.select_dtypes(exclude="number")
    cat_summary = {}
    for col in cat_df.columns:
        top = df[col].value_counts().head(5).to_dict()
        cat_summary[col] = {"top_values": top, "unique": int(df[col].nunique())}

    return {
        "file": Path(file_path).name,
        "numeric_stats": result,
        "categorical_summary": cat_summary,
        "total_rows": int(df.shape[0]),
    }


def csv_filter(
    file_path: str,
    column: str,
    operator: str,
    value: str,
    export_path: Optional[str] = None,
) -> dict:
    """
    Filter rows in a CSV by a condition.

    Args:
        file_path:   Path to the CSV file
        column:      Column name to filter on
        operator:    One of: '==', '!=', '>', '<', '>=', '<=', 'contains'
        value:       Value to compare against (always passed as string, auto-cast)
        export_path: Optional path to save filtered results as CSV

    Returns:
        dict with filtered row count, preview, and optional saved file path
    """
    df, error = _load_csv(file_path)
    if error:
        return {"error": error}

    if column not in df.columns:
        return {"error": f"Column '{column}' not found. Available: {list(df.columns)}"}

    try:
        col_dtype = df[column].dtype

        # Auto-cast value to match column dtype
        if pd.api.types.is_numeric_dtype(col_dtype):
            cast_value = float(value)
        else:
            cast_value = value

        if operator == "==":
            filtered = df[df[column] == cast_value]
        elif operator == "!=":
            filtered = df[df[column] != cast_value]
        elif operator == ">":
            filtered = df[df[column] > cast_value]
        elif operator == "<":
            filtered = df[df[column] < cast_value]
        elif operator == ">=":
            filtered = df[df[column] >= cast_value]
        elif operator == "<=":
            filtered = df[df[column] <= cast_value]
        elif operator == "contains":
            filtered = df[df[column].astype(str).str.contains(str(value), case=False, na=False)]
        else:
            return {"error": f"Unknown operator '{operator}'. Use: ==, !=, >, <, >=, <=, contains"}

    except Exception as e:
        return {"error": f"Filter failed: {e}"}

    result = {
        "original_rows": int(df.shape[0]),
        "filtered_rows": int(filtered.shape[0]),
        "condition": f"{column} {operator} {value}",
        "preview": _df_to_text(filtered, max_rows=10),
    }

    if export_path:
        Path(export_path).parent.mkdir(parents=True, exist_ok=True)
        filtered.to_csv(export_path, index=False)
        result["saved_to"] = export_path

    return result


def csv_export_analysis(
    file_path: str,
    format: str = "pdf",
    save_dir: str = "data/reports",
) -> dict:
    """
    Run full analysis on a CSV and export it as PDF, DOCX, or TXT.

    Args:
        file_path: Path to the CSV file
        format:    'pdf', 'docx', or 'txt'
        save_dir:  Directory to save the report

    Returns:
        dict with saved file path and analysis summary
    """
    # Import here to avoid circular dependency
    from tools.summarize_export_tool import summarize_and_export

    df, error = _load_csv(file_path)
    if error:
        return {"error": error}

    filename = Path(file_path).name

    # Build analysis content
    lines = [
        f"## Dataset Overview",
        f"File: {filename}",
        f"Rows: {df.shape[0]}   Columns: {df.shape[1]}",
        f"Columns: {', '.join(df.columns)}",
        "",
        f"## Missing Values",
    ]

    missing = df.isnull().sum()
    for col, cnt in missing.items():
        if cnt > 0:
            lines.append(f"  {col}: {cnt} missing")
    if missing.sum() == 0:
        lines.append("  No missing values found.")

    # Numeric stats
    numeric_df = df.select_dtypes(include="number")
    if not numeric_df.empty:
        lines.append("")
        lines.append("## Numeric Column Statistics")
        stats = numeric_df.describe().round(4)
        for col in stats.columns:
            lines.append(f"\n{col}")
            lines.append(f"  Mean:  {stats[col]['mean']}")
            lines.append(f"  Min:   {stats[col]['min']}")
            lines.append(f"  Max:   {stats[col]['max']}")
            lines.append(f"  Std:   {stats[col]['std']}")

    # Categorical
    cat_df = df.select_dtypes(exclude="number")
    if not cat_df.empty:
        lines.append("")
        lines.append("## Categorical Columns")
        for col in cat_df.columns:
            top = df[col].value_counts().head(3)
            lines.append(f"\n{col} ({df[col].nunique()} unique values)")
            for val, cnt in top.items():
                lines.append(f"  {val}: {cnt}")

    lines.append("")
    lines.append(f"## Sample Data (first 5 rows)")
    lines.append(_df_to_text(df, max_rows=5))

    content = "\n".join(lines)
    title = f"CSV Analysis — {filename}"

    return summarize_and_export(content=content, title=title, format=format, save_dir=save_dir)


# ── Claude tool schemas ────────────────────────────────────────────────────────

CSV_PREVIEW_SCHEMA = {
    "name": "csv_preview",
    "description": "Load and preview a CSV file — shows shape, column names, data types, and first N rows.",
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to the CSV file"},
            "num_rows": {"type": "integer", "description": "Number of rows to preview (default 5)", "default": 5},
        },
        "required": ["file_path"],
    },
}

CSV_SUMMARY_STATS_SCHEMA = {
    "name": "csv_summary_stats",
    "description": "Generate summary statistics (mean, min, max, std, count) for numeric columns in a CSV. Also shows top values for categorical columns.",
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to the CSV file"},
            "columns": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional list of specific columns to analyze. Defaults to all numeric columns.",
            },
        },
        "required": ["file_path"],
    },
}

CSV_FILTER_SCHEMA = {
    "name": "csv_filter",
    "description": "Filter rows in a CSV file by a condition (e.g. age > 30, city == Lagos, name contains Victor). Optionally save filtered results.",
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to the CSV file"},
            "column": {"type": "string", "description": "Column name to filter on"},
            "operator": {
                "type": "string",
                "enum": ["==", "!=", ">", "<", ">=", "<=", "contains"],
                "description": "Comparison operator",
            },
            "value": {"type": "string", "description": "Value to compare against"},
            "export_path": {"type": "string", "description": "Optional: path to save filtered CSV"},
        },
        "required": ["file_path", "column", "operator", "value"],
    },
}

CSV_EXPORT_SCHEMA = {
    "name": "csv_export_analysis",
    "description": "Run a full analysis on a CSV file and export the report as a PDF, DOCX, or TXT file for download.",
    "input_schema": {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Path to the CSV file"},
            "format": {
                "type": "string",
                "enum": ["pdf", "docx", "txt"],
                "description": "Output format for the report (default: pdf)",
                "default": "pdf",
            },
            "save_dir": {
                "type": "string",
                "description": "Directory to save the report (default: data/reports)",
                "default": "data/reports",
            },
        },
        "required": ["file_path"],
    },
}

# All CSV schemas grouped for easy import
ALL_CSV_TOOL_SCHEMAS = [
    CSV_PREVIEW_SCHEMA,
    CSV_SUMMARY_STATS_SCHEMA,
    CSV_FILTER_SCHEMA,
    CSV_EXPORT_SCHEMA,
]