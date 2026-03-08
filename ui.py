"""
ui.py
─────
All Streamlit rendering functions — hero, upload zone, results, export panel.
Keeps app.py clean by moving every st.* call here.
"""

import streamlit as st
from PIL import Image

from exporter import build_dataframe, build_excel


# ── CSS ───────────────────────────────────────────────────────────────────────

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Syne:wght@400;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Syne', sans-serif; }

.stApp { background-color: #0d0d0d; color: #f0ede6; }

h1, h2, h3 { font-family: 'Syne', sans-serif; font-weight: 800; letter-spacing: -0.5px; }

.hero-title  { font-size: 3rem; font-weight: 800; color: #f0ede6; line-height: 1.1; }
.hero-accent { color: #c8f050; }

.mono  { font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem; color: #888; }
.card  { background: #1a1a1a; border: 1px solid #2a2a2a; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; }
.tag   { display: inline-block; background: #c8f050; color: #0d0d0d; font-family: 'IBM Plex Mono', monospace;
         font-size: 0.7rem; font-weight: 600; padding: 2px 8px; border-radius: 4px; margin-right: 4px; }

.field-label { font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; color: #c8f050;
               text-transform: uppercase; letter-spacing: 1px; margin-bottom: 2px; }
.field-value { font-size: 1rem; color: #f0ede6; font-weight: 600; }

.divider { border: none; border-top: 1px solid #2a2a2a; margin: 1.5rem 0; }

.stButton > button {
    background-color: #c8f050 !important; color: #0d0d0d !important;
    font-family: 'IBM Plex Mono', monospace !important; font-weight: 600 !important;
    border: none !important; border-radius: 8px !important;
    padding: 0.6rem 1.5rem !important; font-size: 0.85rem !important;
    letter-spacing: 0.5px !important; transition: all 0.2s ease !important;
}
.stButton > button:hover { background-color: #d4f56a !important; transform: translateY(-1px) !important; }

.stDownloadButton > button {
    background-color: #1a1a1a !important; color: #c8f050 !important;
    border: 1px solid #c8f050 !important; font-family: 'IBM Plex Mono', monospace !important;
    font-weight: 600 !important; border-radius: 8px !important;
}
.stDataFrame { font-family: 'IBM Plex Mono', monospace !important; font-size: 0.8rem !important; }
[data-testid="stFileUploader"] { background: #1a1a1a !important; border: 1.5px dashed #3a3a3a !important; border-radius: 12px !important; }
.stTextInput > div > input { background: #1a1a1a !important; color: #f0ede6 !important;
    border: 1px solid #2a2a2a !important; border-radius: 8px !important;
    font-family: 'IBM Plex Mono', monospace !important; }
.stExpander { background: #1a1a1a !important; border: 1px solid #2a2a2a !important; border-radius: 12px !important; }
</style>
"""


# ── Page setup ────────────────────────────────────────────────────────────────

def setup_page() -> None:
    st.set_page_config(page_title="Invoice OCR → Excel", page_icon="🧾", layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)


# ── Hero section ──────────────────────────────────────────────────────────────

def render_hero() -> None:
    st.markdown("""
    <div style="padding: 2rem 0 1rem 0;">
        <div class="hero-title">Invoice OCR<br><span class="hero-accent">→ Excel</span></div>
        <p class="mono" style="margin-top:0.5rem;">[ PDF & IMAGE · THAI + ENGLISH · STRUCTURED EXTRACTION ]</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<hr class="divider">', unsafe_allow_html=True)


# ── Upload zone ───────────────────────────────────────────────────────────────

def render_upload_zone():
    """Render file uploader + info card. Returns uploaded files list."""
    col_upload, col_info = st.columns([2, 1])

    with col_upload:
        uploaded_files = st.file_uploader(
            "Drop invoices here",
            type=['pdf', 'png', 'jpg', 'jpeg'],
            accept_multiple_files=True,
            help="รองรับ PDF, PNG, JPG — หลายไฟล์พร้อมกัน",
        )

    with col_info:
        st.markdown("""
        <div class="card">
            <p class="mono">WHAT GETS EXTRACTED</p>
            <div style="margin-top: 0.8rem; line-height: 2.2;">
                <span class="tag">Invoice No</span><br>
                <span class="tag">Date</span><br>
                <span class="tag">Vendor</span>
                <span class="tag">Tax ID</span><br>
                <span class="tag">Customer</span><br>
                <span class="tag">Items</span><br>
                <span class="tag">Subtotal</span>
                <span class="tag">VAT</span>
                <span class="tag">Total</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    return uploaded_files


# ── Process button ────────────────────────────────────────────────────────────

def render_process_button(n_files: int) -> bool:
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    return st.button(f"⚡ Process {n_files} file(s)", use_container_width=False)


# ── Progress helpers ──────────────────────────────────────────────────────────

def make_progress_bar():
    return st.progress(0, text="Starting...")


def update_progress(bar, value: float, text: str) -> None:
    bar.progress(value, text=text)


# ── Single invoice card ───────────────────────────────────────────────────────

def render_invoice_card(inv: dict) -> None:
    """Render one expander card: image preview + fields + manual edit + raw text."""
    m = inv["meta"]
    label = f"🧾  {m['File']}  —  pg.{m['Page']}  |  Invoice: {m['Invoice No']}  |  Total: {m['Total']} {m['Currency']}"

    with st.expander(label, expanded=True):
        col_img, col_fields = st.columns([1, 1])

        with col_img:
            _render_image_preview(inv["image"])

        with col_fields:
            _render_field_grid(m)

        _render_manual_correction(inv)
        _render_raw_lines(inv["lines"])


def _render_image_preview(img) -> None:
    if img is not None:
        st.image(img, use_column_width=True)
    else:
        st.info("No image preview")


def _render_field_grid(m: dict) -> None:
    fields = [
        ("Invoice No", m["Invoice No"]),
        ("Date",       m["Date"]),
        ("Vendor",     m["Vendor"]),
        ("Tax ID",     m["Tax ID"]),
        ("Customer",   m["Customer"]),
        ("Subtotal",   m["Subtotal"]),
        ("VAT",        m["VAT"]),
        ("Total",      m["Total"]),
        ("Currency",   m["Currency"]),
    ]
    for label, value in fields:
        st.markdown(
            f'<p class="field-label">{label}</p><p class="field-value">{value}</p>',
            unsafe_allow_html=True,
        )


def _render_manual_correction(inv: dict) -> None:
    m = inv["meta"]
    with st.expander("✏️ Manual correction"):
        cols = st.columns(2)
        editable = ["Invoice No", "Date", "Vendor", "Tax ID", "Customer", "Items", "Subtotal", "VAT", "Total"]
        for i, key in enumerate(editable):
            new_val = cols[i % 2].text_input(key, value=m[key], key=f"{m['File']}_{m['Page']}_{key}")
            inv["meta"][key] = new_val


def _render_raw_lines(lines: list) -> None:
    with st.expander("🔍 Raw OCR / PDF text"):
        for line in lines:
            st.markdown(f'<span class="mono">{line}</span>', unsafe_allow_html=True)


# ── Results section ───────────────────────────────────────────────────────────

def render_results(invoices: list) -> None:
    """Render all invoice cards."""
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<p class="mono">EXTRACTED RESULTS</p>', unsafe_allow_html=True)
    for inv in invoices:
        render_invoice_card(inv)


# ── Export panel ──────────────────────────────────────────────────────────────

def render_export_panel(invoices: list) -> None:
    """Render DataFrame preview + Download Excel + Clear all buttons."""
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<p class="mono">EXPORT</p>', unsafe_allow_html=True)

    df = build_dataframe(invoices)
    display_cols = [c for c in df.columns if c != "Raw Preview"]
    st.dataframe(df[display_cols], use_container_width=True)

    excel_bytes = build_excel(df)

    col_dl, col_clear = st.columns([2, 1])
    with col_dl:
        st.download_button(
            label="⬇️ Download Excel",
            data=excel_bytes,
            file_name="invoices_extracted.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with col_clear:
        if st.button("🗑️ Clear all", use_container_width=True):
            st.session_state.invoices = []
            st.rerun()