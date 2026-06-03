#!/usr/bin/env python3
"""
OCR PDF — Make scanned PDFs searchable with Ctrl+F
===================================================

Converts a scanned (image-based) PDF into a searchable PDF by adding
an invisible text layer using Tesseract OCR. The output PDF looks
identical to the original but supports text search, selection, and copy.

Optimized for bilingual Hindi+English dictionary scans.

Usage:
    python ocr_pdf.py "input.pdf"
    python ocr_pdf.py "input.pdf" -o "output.pdf"
    python ocr_pdf.py "input.pdf" -l eng
"""

import argparse
import os
import shutil
import sys
import time

# Force UTF-8 output on Windows to avoid cp1252 encoding errors
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


# ── ANSI color helpers (works in Windows 10+ terminal) ──────────────────────

def _supports_color():
    """Check if the terminal supports ANSI colors."""
    if os.name == "nt":
        # Windows 10+ supports ANSI via virtual terminal processing
        os.system("")  # enables ANSI escape codes on Windows
        return True
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


_COLOR = _supports_color()


def _c(code, text):
    return f"\033[{code}m{text}\033[0m" if _COLOR else text


def green(t):  return _c("32", t)
def red(t):    return _c("31", t)
def yellow(t): return _c("33", t)
def cyan(t):   return _c("36", t)
def bold(t):   return _c("1", t)
def dim(t):    return _c("2", t)


# ── Pre-flight checks ──────────────────────────────────────────────────────

# Common Tesseract install locations on Windows
_TESSERACT_PATHS = [
    r"C:\Program Files\Tesseract-OCR",
    r"C:\Program Files (x86)\Tesseract-OCR",
]


def _add_tesseract_to_path():
    """Auto-detect Tesseract on Windows if it's not already in PATH."""
    if shutil.which("tesseract") is not None:
        return  # Already in PATH

    for path in _TESSERACT_PATHS:
        exe = os.path.join(path, "tesseract.exe")
        if os.path.isfile(exe):
            os.environ["PATH"] = path + os.pathsep + os.environ.get("PATH", "")
            print(dim(f"  Auto-detected Tesseract at: {path}"))
            return

    return  # Not found — check_tesseract() will handle the error


def check_tesseract():
    """Verify Tesseract OCR is installed and accessible."""
    _add_tesseract_to_path()

    if shutil.which("tesseract") is None:
        print(red("✗ Tesseract OCR is not installed or not in PATH.\n"))
        print("  Install it from:")
        print(cyan("  https://github.com/UB-Mannheim/tesseract/wiki\n"))
        print("  During installation:")
        print("  • Check 'Additional language data' → select Hindi (hin)")
        print("  • Make sure 'Add to PATH' is selected")
        sys.exit(1)


def check_language_packs(lang):
    """Verify required Tesseract language packs are installed."""
    import subprocess

    try:
        result = subprocess.run(
            ["tesseract", "--list-langs"],
            capture_output=True, text=True, timeout=10
        )
        installed = result.stdout.strip().splitlines()
        # First line is usually a header like "List of available languages..."
        installed = [l.strip() for l in installed[1:] if l.strip()]
    except Exception:
        # If we can't check, let ocrmypdf handle the error later
        return

    requested = [l.strip() for l in lang.split("+")]
    missing = [l for l in requested if l not in installed]

    if missing:
        print(red(f"✗ Missing Tesseract language pack(s): {', '.join(missing)}\n"))
        print("  To install missing language packs:")
        print("  • Re-run the Tesseract installer")
        print("  • Check 'Additional language data'")
        for m in missing:
            print(f"    → Select: {bold(m)}")
        print()
        print(dim("  Installed languages: " + ", ".join(installed)))
        sys.exit(1)


def check_ocrmypdf():
    """Verify ocrmypdf is installed."""
    try:
        import ocrmypdf  # noqa: F401
    except ImportError:
        print(red("✗ ocrmypdf is not installed.\n"))
        print("  Install it with:")
        print(cyan("  pip install ocrmypdf"))
        sys.exit(1)


def validate_input(path):
    """Validate the input PDF file."""
    if not os.path.exists(path):
        print(red(f"✗ File not found: {path}"))
        sys.exit(1)

    if not path.lower().endswith(".pdf"):
        print(red(f"✗ Not a PDF file: {path}"))
        sys.exit(1)

    size_mb = os.path.getsize(path) / (1024 * 1024)
    return size_mb


# ── Progress tracking ──────────────────────────────────────────────────────

def format_time(seconds):
    """Format seconds into a human-readable string."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes}m {secs}s"


def format_size(bytes_val):
    """Format bytes into a human-readable string."""
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f} KB"
    else:
        return f"{bytes_val / (1024 * 1024):.1f} MB"


# ── Main OCR logic ─────────────────────────────────────────────────────────

def run_ocr(input_path, output_path, language):
    """Run OCR on the input PDF and produce a searchable output PDF."""
    import ocrmypdf

    print()
    print(bold("=" * 50))
    print(bold("   OCR PDF -- Make Your PDF Searchable"))
    print(bold("=" * 50))
    print()
    print(f"  Input:    {cyan(input_path)}")
    print(f"  Output:   {cyan(output_path)}")
    print(f"  Language: {cyan(language)}")
    print()

    input_size = os.path.getsize(input_path)
    print(f"  Input size: {format_size(input_size)}")
    print()
    print(dim("  Processing... this may take a while for large PDFs."))
    print(dim("  (Tesseract OCR reads every page image and extracts text)"))
    print()

    start_time = time.time()

    try:
        # Split language string like "hin+eng" into list ["hin", "eng"]
        langs = [l.strip() for l in language.split("+")]

        exit_code = ocrmypdf.ocr(
            input_path,
            output_path,
            language=langs,
            deskew=True,           # Straighten rotated scans
            optimize=0,            # Lossless optimization
            skip_text=True,        # Skip pages already containing text
            progress_bar=True,     # Show built-in progress bar
        )
    except ocrmypdf.exceptions.PriorOcrFoundError:
        print()
        print(yellow("⚠ This PDF already has a text layer (already searchable)."))
        print(yellow("  Using --skip-text to preserve existing text and OCR remaining pages."))
        print()
        # This shouldn't happen because we set skip_text=True, but just in case
        exit_code = ocrmypdf.ExitCode.ok
    except ocrmypdf.exceptions.EncryptedPdfError:
        print()
        print(red("✗ This PDF is password-protected / encrypted."))
        print("  Please remove the password first, then try again.")
        sys.exit(1)
    except ocrmypdf.exceptions.InputFileError as e:
        print()
        print(red(f"✗ Problem with input PDF: {e}"))
        sys.exit(1)
    except ocrmypdf.exceptions.MissingDependencyError as e:
        print()
        print(red(f"✗ Missing dependency: {e}"))
        print("  Make sure Tesseract OCR and Ghostscript are installed.")
        sys.exit(1)
    except KeyboardInterrupt:
        print()
        print(yellow("\n⚠ Cancelled by user. Cleaning up..."))
        # Remove partial output if it exists
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except OSError:
                pass
        sys.exit(130)

    elapsed = time.time() - start_time

    if exit_code == ocrmypdf.ExitCode.ok:
        output_size = os.path.getsize(output_path)
        print()
        print(green("=" * 50))
        print(green(bold("  [OK] Success! Your PDF is now searchable.")))
        print(green("=" * 50))
        print()
        print(f"  Output file: {cyan(output_path)}")
        print(f"  Output size: {format_size(output_size)}")
        print(f"  Time taken:  {format_time(elapsed)}")
        print()
        print(dim("  Open the output PDF in any viewer and press Ctrl+F to search!"))
        print()
    elif exit_code == ocrmypdf.ExitCode.pdfa_conversion_failed:
        # OCR succeeded but PDF/A conversion failed — still usable
        print()
        print(yellow("⚠ OCR completed but PDF/A conversion had warnings."))
        print(green("  The output PDF is still searchable — Ctrl+F will work!"))
        print()
    else:
        print()
        print(red(f"✗ OCR failed with exit code: {exit_code}"))
        print("  Check the errors above for details.")
        sys.exit(1)


# ── CLI argument parsing ───────────────────────────────────────────────────

def build_parser():
    parser = argparse.ArgumentParser(
        description="Make scanned PDFs searchable with Ctrl+F using OCR.",
        epilog="Example: python ocr_pdf.py dictionary.pdf -o searchable.pdf",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "input",
        help="Path to the scanned PDF file",
    )
    parser.add_argument(
        "-o", "--output",
        help="Output path for the searchable PDF (default: <input>_searchable.pdf)",
        default=None,
    )
    parser.add_argument(
        "-l", "--language",
        help="OCR language(s), e.g. 'eng', 'hin', 'hin+eng' (default: hin+eng)",
        default="hin+eng",
    )
    return parser


def default_output_path(input_path):
    """Generate default output filename: input_searchable.pdf"""
    base, ext = os.path.splitext(input_path)
    return f"{base}_searchable{ext}"


# ── Entry point ────────────────────────────────────────────────────────────

def main():
    parser = build_parser()
    args = parser.parse_args()

    input_path = os.path.abspath(args.input)
    output_path = os.path.abspath(args.output) if args.output else default_output_path(input_path)
    language = args.language

    # Pre-flight checks
    check_ocrmypdf()
    check_tesseract()
    check_language_packs(language)
    size_mb = validate_input(input_path)

    # Warn for large files
    if size_mb > 100:
        print(yellow(f"⚠ Large file detected ({size_mb:.0f} MB). This may take a long time."))
        print(dim("  Consider running overnight for very large dictionaries."))
        print()

    # Prevent overwriting the input
    if os.path.abspath(input_path) == os.path.abspath(output_path):
        print(red("✗ Output path is the same as input. Use -o to specify a different output."))
        sys.exit(1)

    # Run OCR
    run_ocr(input_path, output_path, language)


if __name__ == "__main__":
    main()
