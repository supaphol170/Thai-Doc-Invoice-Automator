"""
exporter.py
───────────
Converts extracted invoice data into a formatted Excel file.
"""

import io
import pandas as pd


COLUMN_ORDER = [
    "File", "Page", "Invoice No", "Date",
    "Vendor", "Tax ID", "Customer",
    "Item Description", "Quantity", "Unit Price", "Amount",
    "Subtotal", "VAT", "Total", "Currency", "Raw Preview",
]


def _parse_items(items_str: str) -> list[dict]:
    """
    Split item strings like:
      'SHORT RUN DRY 500 | qty:1.00 | unit:350.00 | amt:350.00'
    into a list of dicts with keys: description, qty, unit_price, amount.
    Handles multiple items separated by ' / '.
    """
    parsed = []
    if not items_str or items_str == "—":
        return [{"description": "—", "qty": "—", "unit_price": "—", "amount": "—"}]

    for item in items_str.split(" / "):
        parts = [p.strip() for p in item.split("|")]
        desc  = parts[0] if len(parts) > 0 else "—"
        qty   = parts[1].replace("qty:", "").strip()   if len(parts) > 1 else "—"
        unit  = parts[2].replace("unit:", "").strip()  if len(parts) > 2 else "—"
        amt   = parts[3].replace("amt:", "").strip()   if len(parts) > 3 else "—"
        parsed.append({"description": desc, "qty": qty, "unit_price": unit, "amount": amt})
    return parsed


def build_dataframe(invoices: list) -> pd.DataFrame:
    """
    Build a DataFrame from invoice entries, expanding Items into 4 columns.
    Multi-item invoices become multiple rows (one per item).
    """
    rows = []
    for inv in invoices:
        m     = inv["meta"]
        items = _parse_items(m.get("Items", "—"))
        for item in items:
            rows.append({
                "File":             m.get("File", ""),
                "Page":             m.get("Page", ""),
                "Invoice No":       m.get("Invoice No", "—"),
                "Date":             m.get("Date", "—"),
                "Vendor":           m.get("Vendor", "—"),
                "Tax ID":           m.get("Tax ID", "—"),
                "Customer":         m.get("Customer", "—"),
                "Item Description": item["description"],
                "Quantity":         item["qty"],
                "Unit Price":       item["unit_price"],
                "Amount":           item["amount"],
                "Subtotal":         m.get("Subtotal", "—"),
                "VAT":              m.get("VAT", "—"),
                "Total":            m.get("Total", "—"),
                "Currency":         m.get("Currency", "THB"),
                "Raw Preview":      m.get("Raw Preview", ""),
            })

    df = pd.DataFrame(rows)
    ordered = [c for c in COLUMN_ORDER if c in df.columns]
    return df[ordered]


def build_excel(df: pd.DataFrame) -> bytes:
    """
    Serialize a DataFrame to an Excel (.xlsx) file with auto-sized columns.

    Returns
    -------
    bytes  Ready-to-download Excel file content.
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Invoices")
        _auto_size_columns(writer.sheets["Invoices"])
    output.seek(0)
    return output.read()


def _auto_size_columns(worksheet) -> None:
    """Set each column width to fit its longest value (max 50 chars)."""
    for col in worksheet.columns:
        max_len = max(
            (len(str(cell.value)) for cell in col if cell.value),
            default=10,
        )
        worksheet.column_dimensions[col[0].column_letter].width = min(max_len + 4, 50)