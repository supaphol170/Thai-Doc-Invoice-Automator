"""
app.py
──────
Entry point. Orchestrates the Streamlit app using modular components.

Run with:
    streamlit run app.py

Module layout:
    app.py        ← this file  (orchestration only)
    extractor.py  ← field parsing logic (regex + table extraction)
    loader.py     ← PDF / image reading → structured page entries
    exporter.py   ← DataFrame + Excel generation
    ui.py         ← all Streamlit rendering functions
"""

import streamlit as st

from ui import (
    setup_page,
    render_hero,
    render_upload_zone,
    render_process_button,
    make_progress_bar,
    update_progress,
    render_results,
    render_export_panel,
)
from loader import process_uploaded_file


# ── Page config & styles ──────────────────────────────────────────────────────
setup_page()

# ── Session state ─────────────────────────────────────────────────────────────
if "invoices" not in st.session_state:
    st.session_state.invoices = []

# ── Hero ──────────────────────────────────────────────────────────────────────
render_hero()

# ── Upload zone ───────────────────────────────────────────────────────────────
uploaded_files = render_upload_zone()

# ── Process ───────────────────────────────────────────────────────────────────
if uploaded_files:
    if render_process_button(len(uploaded_files)):
        st.session_state.invoices = []
        bar = make_progress_bar()

        all_entries = []
        for f in uploaded_files:
            try:
                entries = process_uploaded_file(f)
                all_entries.extend(entries)
            except Exception as e:
                st.error(f"❌ Error processing {f.name}: {e}")

        for idx, entry in enumerate(all_entries):
            m = entry["meta"]
            update_progress(bar, (idx + 1) / len(all_entries), f"Saving {m['File']} pg.{m['Page']}...")
            st.session_state.invoices.append(entry)

        bar.empty()
        st.success(f"✅ Processed {len(all_entries)} page(s) from {len(uploaded_files)} file(s)")

# ── Results + Export ──────────────────────────────────────────────────────────
if st.session_state.invoices:
    render_results(st.session_state.invoices)
    render_export_panel(st.session_state.invoices)
