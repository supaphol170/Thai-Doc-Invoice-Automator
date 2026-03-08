"""
extractor.py
────────────
Parses raw text lines + pdfplumber tables into structured invoice fields.
Supports Thai tax invoices (ใบกำกับภาษี) and English invoices.
"""

import re


# ── Internal helper ──────────────────────────────────────────────────────────

def _find(patterns: list, text: str) -> str:
    """Return first regex match group(1) across all patterns, or empty string."""
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE | re.MULTILINE)
        if m:
            return m.group(1).strip()
    return ""


# ── Individual field extractors ───────────────────────────────────────────────

def extract_invoice_no(full_text: str) -> str:
    return _find([
        r'เลข(?:ที่)?ใบ(?:กํากับ|กำกับ|แจ้ง)[^\n]*?(\d{5,}[\/\-]\d{4,})',
        r'invoice\s*(?:no|number|#)[.:\s]+([A-Z0-9\-\/]{4,})',
        r'inv[.:\s#]+([A-Z0-9\-\/]{4,})',
    ], full_text)


def extract_date(full_text: str) -> str:
    return _find([
        r'วันที่\s*(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
        r'date[:\s]+(\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4})',
        r'(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{2,4})',
    ], full_text)


def extract_vendor(text_lines: list, full_text: str) -> str:
    """Company name is usually in the first 10 lines; skip digital-signature lines."""
    for line in text_lines[:10]:
        if re.search(r'digitally signed|digital sign|cn=|nc=', line, re.IGNORECASE):
            continue
        if re.search(r'บริษัท|ห้างหุ้นส่วน|ร้าน|co\.,?\s*ltd|company|corp', line, re.IGNORECASE):
            return line.strip()
    return _find([r'(?:from|vendor|seller|issued by|sold by)[:\s]+(.+)'], full_text)


def extract_customer(full_text: str) -> str:
    return _find([
        r'(?:bill\s*to|ship\s*to|sold\s*to)[:\s]+(.+)',
        r'(?:ลูกค้า|ผู้ซื้อ|บิลถึง)[:\s]+(.+)',
    ], full_text)


def extract_tax_id(full_text: str) -> str:
    return _find([
        r'เลขประจ[ํา]ตัวผู[\u0f70b\u0e49\uf70b]?เสียภาษ[ี]\S*\s*([\d]+)',
        r'เลขประจ\S*ตัวผ\S+เสียภาษ\S+\s*([\d]{10,})',
        r'tax\s*id[:\s]+([\d\-]+)',
    ], full_text)


def extract_items_from_tables(tables: list) -> list:
    """Pull line-item rows from pdfplumber tables."""
    items = []
    for table in tables:
        in_data = False
        for row in table:
            if not row:
                continue
            row_text = " ".join(str(c) for c in row if c)
            if re.search(r'DESCRIPTION|รายการสินค', row_text, re.IGNORECASE):
                in_data = True
                continue
            if in_data:
                if re.search(r'รวมเงิน|รวมเป|ยอด|หักส|ภาษี', row_text):
                    break
                cells = [str(c).strip() for c in row if c and str(c).strip() not in ('', 'None')]
                if len(cells) >= 3 and re.search(r'\d+\.\d{2}', row_text):
                    desc   = cells[1] if len(cells) > 1 else cells[0]
                    qty    = cells[2] if len(cells) > 2 else ""
                    uprice = cells[3] if len(cells) > 3 else ""
                    amt    = cells[-1]
                    items.append(f"{desc} | qty:{qty} | unit:{uprice} | amt:{amt}")
    return items


def extract_items_from_text(text_lines: list) -> list:
    """Fallback: pull item lines from raw text when table extraction yields nothing."""
    items = []
    in_items = False
    for line in text_lines:
        if re.search(r'DESCRIPTION|รายการสินค', line, re.IGNORECASE):
            in_items = True
            continue
        if in_items:
            if re.search(r'รวมเงิน|subtotal|รวมเป|ยอดเงิน|ภาษี', line, re.IGNORECASE):
                break
            if re.match(r'.+\s+[\d,]+\.\d{2}', line.strip()):
                items.append(line.strip())
    return items


def extract_amounts_from_tables(tables: list) -> tuple:
    """Return (subtotal, vat, total) from summary rows in pdfplumber tables."""
    subtotal = vat = total = ""
    for table in tables:
        for row in table:
            if not row:
                continue
            cells = [str(c).strip() for c in row if c and str(c).strip() not in ('', 'None')]
            row_text = " ".join(cells)
            nums = re.findall(r'[\d,]+\.?\d*', row_text)
            if not nums:
                continue
            if re.search(r'รวมเป[\uf712]?นเงิน|subtotal', row_text, re.IGNORECASE) and not subtotal:
                subtotal = nums[-1]
            if re.search(r'ภาษีมูลค[\uf70a]?[\u0e48\u0e49\u0e4a\u0e4b]?าเพิ่ม|vat', row_text, re.IGNORECASE) and not vat:
                vat = nums[-1]
            if re.search(r'ยอดเงินสุทธิ|grand total|net amount|amount due', row_text, re.IGNORECASE) and not total:
                total = nums[-1]
    return subtotal, vat, total


def extract_amounts_from_text(full_text: str) -> tuple:
    """Regex fallback for subtotal/vat/total when tables don't have them."""
    subtotal = _find([
        r'รวมเป[\uf712]?นเงิน\s*([\d,]+\.?\d*)',
        r'(?:subtotal|sub-total)[:\s]+([\d,]+\.?\d*)',
    ], full_text)
    vat = _find([
        r'ภาษีมูลค[\uf70a]?[\u0e48\u0e49]?าเพิ่ม\s*([\d,]+\.?\d*)',
        r'(?:vat|tax)[:\s]+([\d,]+\.?\d*)',
    ], full_text)
    total = _find([
        r'ยอดเงินสุทธิ\s*([\d,]+\.?\d*)',
        r'(?:grand\s*total|net\s*amount)[:\s]+([\d,]+\.?\d*)',
    ], full_text)
    return subtotal, vat, total


def detect_currency(full_text: str) -> str:
    if re.search(r'\$|usd', full_text, re.IGNORECASE):
        return "USD"
    return "THB"


# ── Main entry point ─────────────────────────────────────────────────────────

def extract_invoice_fields(text_lines: list, tables: list = None) -> dict:
    """
    Combine all extractors into a single structured dict.

    Parameters
    ----------
    text_lines : list of str   Raw text lines from the page.
    tables     : list          pdfplumber tables (optional).

    Returns
    -------
    dict with keys: Invoice No, Date, Vendor, Tax ID, Customer,
                    Items, Subtotal, VAT, Total, Currency, Raw Preview
    """
    tables    = tables or []
    full_text = "\n".join(text_lines)

    # Field extraction
    invoice_no = extract_invoice_no(full_text)
    date       = extract_date(full_text)
    vendor     = extract_vendor(text_lines, full_text)
    customer   = extract_customer(full_text)
    tax_id     = extract_tax_id(full_text)
    currency   = detect_currency(full_text)

    # Items
    items = extract_items_from_tables(tables)
    if not items:
        items = extract_items_from_text(text_lines)

    # Amounts — prefer table, fall back to text regex
    subtotal, vat, total = extract_amounts_from_tables(tables)
    sub_fb, vat_fb, tot_fb = extract_amounts_from_text(full_text)
    subtotal = subtotal or sub_fb
    vat      = vat      or vat_fb
    total    = total    or tot_fb

    return {
        "Invoice No":  invoice_no or "—",
        "Date":        date       or "—",
        "Vendor":      vendor[:60] if vendor else "—",
        "Tax ID":      tax_id     or "—",
        "Customer":    customer[:60] if customer else "—",
        "Items":       " / ".join(items) if items else "—",
        "Subtotal":    subtotal   or "—",
        "VAT":         vat        or "—",
        "Total":       total      or "—",
        "Currency":    currency,
        "Raw Preview": full_text[:600].replace("\n", " | "),
    }
