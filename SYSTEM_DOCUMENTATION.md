# PDF Search System Documentation

## Purpose

This project converts scanned, image-based PDF files into searchable PDFs. The final output keeps the original page appearance but adds an invisible text layer so Ctrl+F, text selection, and copy-paste work normally.

The codebase is intentionally small: the whole application lives in a single Python entrypoint, [ocr_pdf.py](ocr_pdf.py#L1), and the rest of the repository contains the package dependency list, project notes, and sample input/output PDFs.

## What The System Does

The system takes an input PDF, checks that the required OCR tools are available, validates the file, and then hands the document to `ocrmypdf`. `ocrmypdf` performs the heavy lifting by running OCR over each page image, embedding the recognized text invisibly into the PDF, and writing the searchable result to a new file.

The repository is tuned for Hindi and English dictionary scans, but the language can be changed from the command line.

## Repository Layout

The workspace currently contains these important files:

- [ocr_pdf.py](ocr_pdf.py) - main application logic and CLI entrypoint
- [requirements.txt](requirements.txt) - Python dependency list
- [README.md](README.md) - short project overview and quick start instructions
- `sample_dictionary.pdf` - example scanned source PDF
- `sample_dictionary_searchable.pdf` - example searchable output PDF

## Technology Stack

### Python 3

Python is the runtime for the whole tool. The script uses Python standard library modules for command-line parsing, filesystem checks, process handling, timing, and Windows console behavior.

Where it is used:

- `argparse` for CLI arguments in [ocr_pdf.py](ocr_pdf.py#L271)
- `os` for paths, file checks, environment updates, and file sizes in [ocr_pdf.py](ocr_pdf.py#L19), [ocr_pdf.py](ocr_pdf.py#L58), [ocr_pdf.py](ocr_pdf.py#L136)
- `shutil` for locating the `tesseract` executable in [ocr_pdf.py](ocr_pdf.py#L65)
- `sys` for Windows UTF-8 output and exit handling in [ocr_pdf.py](ocr_pdf.py#L25)
- `time` for runtime measurement in [ocr_pdf.py](ocr_pdf.py#L194)
- `subprocess` for language-pack discovery in [ocr_pdf.py](ocr_pdf.py#L94)

### ocrmypdf

`ocrmypdf` is the core processing library. The script imports it only when needed, verifies that it is installed, and then calls `ocrmypdf.ocr(...)` to perform the OCR pipeline.

What it does in this project:

- reads the input PDF
- sends page images through OCR
- writes a new searchable PDF
- handles page-level options like deskewing, skipping pages that already contain text, and progress display
- exposes structured exceptions that the script uses for user-friendly error handling

Where it is used:

- dependency check in [ocr_pdf.py](ocr_pdf.py#L125)
- main OCR call in [ocr_pdf.py](ocr_pdf.py#L200)
- result handling in [ocr_pdf.py](ocr_pdf.py#L243)

### Tesseract OCR

Tesseract is the actual OCR engine. It converts page images into text. In this project, the script checks that the executable exists, checks that required language packs are installed, and passes the selected language set to `ocrmypdf`.

Where it is used:

- executable discovery and PATH auto-fix in [ocr_pdf.py](ocr_pdf.py#L58)
- installation check in [ocr_pdf.py](ocr_pdf.py#L80)
- language-pack validation in [ocr_pdf.py](ocr_pdf.py#L94)
- language selection passed into OCR in [ocr_pdf.py](ocr_pdf.py#L200)

### Ghostscript

Ghostscript is not imported directly, but it is part of the OCR toolchain used by `ocrmypdf`. It helps with PDF processing and conversion steps. The script surfaces Ghostscript-related issues through `ocrmypdf.exceptions.MissingDependencyError`.

Where it is used:

- reported as a required external dependency in [ocr_pdf.py](ocr_pdf.py#L225)

### Leptonica

Leptonica is a low-level image-processing library used by the Tesseract stack. The script does not call it directly, but it is part of the OCR dependency chain that supports image handling and preprocessing.

In practical terms, Leptonica helps the OCR pipeline work on scanned pages by supporting the image operations that sit underneath OCR.

## End-To-End Flow

### 1. User runs the command

The entrypoint is the `main()` function in [ocr_pdf.py](ocr_pdf.py#L302). It is executed only when the script is launched directly from the command line.

Example:

```bash
python ocr_pdf.py "input.pdf"
```

### 2. CLI arguments are parsed

The parser is built in [ocr_pdf.py](ocr_pdf.py#L271). The script accepts:

- one required positional input PDF path
- an optional output path with `-o` or `--output`
- an optional OCR language string with `-l` or `--language`

Default language is `hin+eng`, which is the main reason this repository works well for bilingual dictionary scans.

### 3. Input and environment checks run

Before any OCR work starts, the script verifies that the environment is usable:

- `check_ocrmypdf()` ensures the Python package exists in [ocr_pdf.py](ocr_pdf.py#L125)
- `check_tesseract()` ensures the Tesseract executable is installed and reachable in [ocr_pdf.py](ocr_pdf.py#L80)
- `_add_tesseract_to_path()` tries common Windows installation paths if Tesseract is not already on PATH in [ocr_pdf.py](ocr_pdf.py#L65)
- `check_language_packs()` verifies the requested OCR languages are available in [ocr_pdf.py](ocr_pdf.py#L94)
- `validate_input()` confirms that the file exists, is a PDF, and returns its size in [ocr_pdf.py](ocr_pdf.py#L136)

This design keeps failures early and readable. The script exits before OCR starts if a required tool is missing.

### 4. Output path is resolved

If the user does not provide `-o`, the default name is generated by `default_output_path()` in [ocr_pdf.py](ocr_pdf.py#L294). It appends `_searchable` before the `.pdf` extension.

Examples:

- `dictionary.pdf` -> `dictionary_searchable.pdf`
- `scan.book.pdf` -> `scan.book_searchable.pdf`

The script also prevents accidental overwrite by refusing to write output to the same path as the input in [ocr_pdf.py](ocr_pdf.py#L322).

### 5. OCR is executed

The actual conversion happens in `run_ocr()` in [ocr_pdf.py](ocr_pdf.py#L173). This is the heart of the application.

The function:

- prints a banner and the selected input/output settings
- measures input file size and runtime
- splits the language string like `hin+eng` into a list
- calls `ocrmypdf.ocr(...)`
- handles OCR-related exceptions
- prints success, warning, or error messages at the end

Key OCR options used in the call:

- `deskew=True` to straighten rotated scans
- `optimize=0` to keep processing lossless and avoid aggressive optimization
- `skip_text=True` to avoid re-OCRing pages that already contain text
- `progress_bar=True` to show processing progress

### 6. Output is written and reported

If `ocrmypdf` reports success, the script prints the output file size and elapsed processing time, then tells the user to open the PDF and press Ctrl+F.

If OCR completed but PDF/A conversion had warnings, the output is still treated as usable and searchable.

## Code Map

This section connects the main functions to their responsibilities.

### Runtime and console setup

The top of [ocr_pdf.py](ocr_pdf.py#L18) sets up imports and Windows UTF-8 handling. That is important because scanned dictionary text often includes Hindi characters, and Windows terminals can otherwise fail on non-ASCII output.

The color helpers in [ocr_pdf.py](ocr_pdf.py#L32) make command-line output easier to read. They are purely presentation logic and do not affect OCR behavior.

### Dependency discovery and validation

- `_TESSERACT_PATHS` in [ocr_pdf.py](ocr_pdf.py#L58) stores common Windows install paths
- `_add_tesseract_to_path()` in [ocr_pdf.py](ocr_pdf.py#L65) mutates `PATH` only when necessary
- `check_tesseract()` in [ocr_pdf.py](ocr_pdf.py#L80) stops the app with a clear message if Tesseract is missing
- `check_language_packs()` in [ocr_pdf.py](ocr_pdf.py#L94) asks Tesseract which languages are installed and blocks missing languages before OCR starts
- `check_ocrmypdf()` in [ocr_pdf.py](ocr_pdf.py#L125) prevents a confusing runtime import failure later in the process
- `validate_input()` in [ocr_pdf.py](ocr_pdf.py#L136) prevents invalid file types and missing-file errors

### Progress Helpers

- `format_time()` in [ocr_pdf.py](ocr_pdf.py#L152) formats elapsed time as seconds or minutes + seconds
- `format_size()` in [ocr_pdf.py](ocr_pdf.py#L161) formats file sizes into B, KB, or MB

These helpers do not change OCR results; they only make the command-line output understandable.

### OCR Orchestration

- `run_ocr()` in [ocr_pdf.py](ocr_pdf.py#L173) orchestrates the full OCR job
- the `PriorOcrFoundError` branch in [ocr_pdf.py](ocr_pdf.py#L209) explains what happens when a PDF already has text
- the `EncryptedPdfError` branch in [ocr_pdf.py](ocr_pdf.py#L216) handles password-protected PDFs
- the `InputFileError` branch in [ocr_pdf.py](ocr_pdf.py#L221) catches malformed input files
- the `MissingDependencyError` branch in [ocr_pdf.py](ocr_pdf.py#L225) surfaces missing OCR toolchain pieces
- the `KeyboardInterrupt` branch in [ocr_pdf.py](ocr_pdf.py#L230) cleans up partial output if the user cancels

### CLI and Application Entry

- `build_parser()` in [ocr_pdf.py](ocr_pdf.py#L271) defines the CLI interface
- `default_output_path()` in [ocr_pdf.py](ocr_pdf.py#L294) generates the default output filename
- `main()` in [ocr_pdf.py](ocr_pdf.py#L302) wires everything together
- the `if __name__ == "__main__":` guard in [ocr_pdf.py](ocr_pdf.py#L331) makes the file executable as a script

## Why Each Library Exists

### argparse

Handles the command-line interface so users can pass the input file, output file, and language without editing code.

### os

Handles file paths, existence checks, environment variable changes, file size lookup, and safe path normalization.

### shutil

Used specifically to locate the `tesseract` executable with `shutil.which(...)`.

### sys

Used for platform detection, terminal output encoding on Windows, and terminating the process with the correct exit codes.

### time

Used only for timing the OCR job so the script can report how long the conversion took.

### subprocess

Used to run `tesseract --list-langs` and parse available language packs before OCR begins.

### ocrmypdf

This is the actual OCR pipeline controller. Without it, the script would have to implement PDF page extraction, OCR execution, text-layer embedding, and PDF rewriting manually.

## How The Logic Works In Practice

The logic is deliberately defensive:

1. Check that the required tools exist.
2. Check that the requested OCR languages are installed.
3. Check that the input file is real and is a PDF.
4. Refuse to overwrite the input file.
5. Run OCR with stable defaults tuned for scanned documents.
6. Report the result in a friendly way.

That means most failures are caught before the expensive OCR run starts.

## Important Behaviors

- The output PDF visually matches the source PDF, but contains an invisible text layer.
- Existing text is preserved because `skip_text=True` is used.
- The tool is optimized for Hindi + English, but other Tesseract languages can be selected with `-l`.
- Large files trigger a warning before processing begins.
- Canceling with Ctrl+C removes partial output if it was created.

## Relationship Between Source And Output Files

The repository includes both the input and output example PDFs so you can compare the behavior visually:

- `sample_dictionary.pdf` is the scanned source
- `sample_dictionary_searchable.pdf` is the OCR-processed output

This is the simplest way to verify that the output preserves layout while adding searchable text.

## Limitations And Dependencies

The script is a wrapper around external OCR tooling, so success depends on the environment:

- Tesseract must be installed
- the requested Tesseract language packs must be installed
- `ocrmypdf` must be installed in the Python environment
- Ghostscript must be available for the full PDF toolchain

If any of those are missing, the script exits early with an explicit message.

## How To Read The Code Base

If you want to understand the project quickly, read it in this order:

1. [ocr_pdf.py](ocr_pdf.py#L302) to see the top-level flow
2. [ocr_pdf.py](ocr_pdf.py#L173) to understand the OCR call
3. [ocr_pdf.py](ocr_pdf.py#L80) and [ocr_pdf.py](ocr_pdf.py#L94) to understand environment validation
4. [ocr_pdf.py](ocr_pdf.py#L271) to understand the CLI interface
5. [requirements.txt](requirements.txt) to see the single pinned Python dependency

That sequence shows the whole system from entrypoint to OCR engine.

## Short Summary

This project is a focused command-line OCR wrapper. Python provides the CLI and validation layer, `ocrmypdf` orchestrates the document conversion, Tesseract performs text recognition, and the script adds Windows-friendly setup, input checks, and user-facing status messages around that core pipeline.
