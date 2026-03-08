📑 Thai-Doc-Invoice-Automator
Thai-Doc-Invoice-Automator is a Python-powered automation tool designed to extract structured data from invoices and receipts in both Thai and English. It seamlessly transforms PDF files and images into ready-to-use Excel spreadsheets.

✨ Key Features
🔍 Multi-format Support: Seamlessly handles both images (JPG, PNG) and PDF files.
🇹🇭 Thai Language Precision: * Images: Leverages EasyOCR (Thai + English) to process complex scans and photos.
Digital PDFs: Uses pdfplumber for direct text-layer extraction, ensuring 100% accuracy for digital documents.
🤖 Automated Structuring: Intelligent data parsing using Regex + Table Extraction logic.
🎨 User-Friendly UI: Modern and intuitive web interface built with Streamlit.
📊 Export Ready: Instant download of results in Excel (.xlsx) format with auto-adjusted column widths.
🚫 No Poppler Required: Easy installation—uses pdfplumber instead of pdf2image, removing complex external dependencies.

📦 Extracted Fields
Invoice No: Tax Invoice / Receipt Number
Date: Document issue date
Vendor/Customer: Company names and billing addresses
Tax ID: Thai Tax Identification Numbers
Items Table: "Product descriptions, Quantity, Unit Price, and Line Amounts"
Totals: "Subtotal, VAT (7%), and Grand Total"
Currency: Automatic detection (THB / USD)

🛠 Tech Stack
Extraction:"pdfplumber, EasyOCR"
Processing: "Python, Pandas, Numpy, Regex"
Interface: Streamlit
Export: openpyxl

📁 Project Structure
invoice_ocr/
├── app.py          # Main Entry point (Orchestration)
├── extractor.py    # Field parsing logic (Regex & Table logic)
├── loader.py       # File handling (PDF/Image reading)
├── exporter.py     # DataFrame to Excel transformation
└── ui.py           # Streamlit rendering components

🚀 Quick Start
1. Clone the repository ```git clone https://github.com/supaphol170/Thai-Doc-Invoice-Automator.git & cd Thai-Doc-Invoice-Automator```
2. Install Dependencies ```pip install -r requirements.txt```
3. Run Application ```streamlit run app.py```
   
🤝 Contribution
Contributions are welcome! If you find a bug or have a feature request, please open an Issue or submit a Pull Request.

Developed with ❤️ for High-Efficiency Data Automation.
