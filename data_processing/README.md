# PDF Text Extraction Tool

This tool extracts text from both searchable and scanned PDFs, saving the output as markdown files with metadata.

## Features

- Automatically detects searchable vs. scanned PDFs
- Uses OCR (Tesseract) for scanned documents
- Preserves document structure and metadata
- Processes multiple PDFs in parallel
- Saves output in markdown format with source information

## Prerequisites

1. Python 3.7+
2. Tesseract OCR engine (for scanned PDFs)
   - Windows: Download from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
   - Ubuntu/Debian: `sudo apt install tesseract-ocr`
   - macOS: `brew install tesseract`

## Installation

1. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Process a single PDF:
```bash
python -m data_processing.pdf_extractor path/to/your/document.pdf -o output/directory
```

### Process all PDFs in a directory:
```bash
python -m data_processing.pdf_extractor path/to/pdfs -o output/directory
```

### Command Line Options:
```
positional arguments:
  input              Input PDF file or directory containing PDFs

optional arguments:
  -h, --help         show this help message and exit
  -o, --output       Output directory (default: input_dir/extracted_text)
  -w, --workers      Number of worker processes (default: 4)
  --tesseract        Path to Tesseract executable (if not in PATH)
```

### Example:
```bash
# Process all PDFs in the current directory using 8 workers
python -m data_processing.pdf_extractor . -o ./extracted_text -w 8
```

## Output Format

Each PDF is converted to a markdown file with the following structure:

```markdown
---
source: original_filename.pdf
type: searchable  # or 'scanned' for OCR'd documents
---

# Extracted Text

[The full text content of the PDF...]
```

## Notes

- For best OCR results, ensure scanned documents are high quality (300+ DPI)
- Processing time depends on document size and system resources
- Large PDFs may require more memory, especially for OCR processing

## Troubleshooting

If you encounter issues with Tesseract:
1. Verify Tesseract is installed and in your system PATH
2. Specify the full path to the Tesseract executable using `--tesseract`
3. Ensure you have the appropriate language data installed
