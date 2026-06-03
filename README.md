# PDF Search — Make Scanned PDFs Searchable

Convert scanned PDFs into searchable PDFs so **Ctrl+F works**. Built for Hindi+English dictionaries.

---

## Architecture

```mermaid
flowchart LR
    A["📄 Scanned PDF"] --> B["🔍 ocrmypdf"]
    B --> C["⚙️ Tesseract OCR"]
    C --> D["📝 Text Extraction"]
    D --> E["📄 Searchable PDF"]

    style A fill:#1e293b,stroke:#475569,color:#f8fafc
    style B fill:#7c3aed,stroke:#6d28d9,color:#f8fafc
    style C fill:#2563eb,stroke:#1d4ed8,color:#f8fafc
    style D fill:#0891b2,stroke:#0e7490,color:#f8fafc
    style E fill:#059669,stroke:#047857,color:#f8fafc
```

## How It Works

1. **Extract** — Each page of the scanned PDF is extracted as an image
2. **OCR** — Tesseract reads Hindi + English text from each page image
3. **Embed** — An invisible text layer is placed exactly over the words
4. **Output** — A new PDF is created: same visuals + searchable text

The output PDF looks identical to the original. The text layer is invisible — it's only there so Ctrl+F, text selection, and copy-paste work.

## Tech Stack

| Tool | Role |
|------|------|
| **Python 3** | Script runtime |
| **ocrmypdf** | Orchestrates the entire OCR pipeline |
| **Tesseract OCR** | Engine that reads text from images |
| **Leptonica** | Image preprocessing (deskew, noise removal) |

---

## Setup

### 1. Install Tesseract OCR

Download the installer → https://github.com/UB-Mannheim/tesseract/wiki

During installation:
- ✅ Expand **"Additional language data"** → check **Hindi**
- ✅ Keep the default install path: `C:\Program Files\Tesseract-OCR`

**Restart your terminal after installation.**

### 2. Clone and Install

**a.** Clone the repository:
```bash
git clone https://github.com/VishnuKant0925/PDF-Search.git
```

**b.** Go into the project folder:
```bash
cd PDF-Search
```

**c.** Create a virtual environment:
```bash
python -m venv .venv
```

**d.** Activate the virtual environment:
```bash
.\.venv\Scripts\Activate.ps1
```
> Using CMD instead of PowerShell? Run this instead: `.\.venv\Scripts\activate.bat`

**e.** Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Run

**a.** Place your scanned PDF in the project folder, then run:
```bash
python ocr_pdf.py "your_file.pdf"
```

**b.** Open the output `your_file_searchable.pdf` and press **Ctrl+F** to search!

---

## Options

```bash
python ocr_pdf.py "input.pdf"                    # Hindi + English (default)
python ocr_pdf.py "input.pdf" -l eng              # English only
python ocr_pdf.py "input.pdf" -o "output.pdf"     # Custom output path
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `tesseract is not recognized` | The script auto-detects it. If installed elsewhere, add the install path to your system PATH. |
| `[WinError 2]` warning | Harmless — Ghostscript not installed. Your PDF is still searchable. |
| PowerShell script error | Run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` |
