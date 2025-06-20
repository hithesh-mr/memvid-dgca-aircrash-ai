import os
import re
import shutil
import tempfile
import pytesseract
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union
import pdf2image
import pdfplumber
from PIL import Image, ImageFile
from tqdm import tqdm
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed, ProcessPoolExecutor
import gc

# Configure PIL to be less strict about image file sizes
ImageFile.LOAD_TRUNCATED_IMAGES = True

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Check if Tesseract is installed
TESSERACT_INSTALLED = bool(shutil.which('tesseract') or shutil.which('tesseract.exe'))
if not TESSERACT_INSTALLED:
    logger.warning(
        "Tesseract OCR is not installed or not in PATH. "
        "Scanned PDFs will not be processed. "
        "Please install Tesseract from https://github.com/UB-Mannheim/tesseract/wiki"
    )

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFExtractor:
    """
    A class to handle extraction of text from both searchable and scanned PDFs.
    """
    
    def __init__(self, tesseract_cmd: str = None):
        """
        Initialize the PDF extractor.
        
        Args:
            tesseract_cmd: Path to Tesseract executable if not in PATH
        """
        self.tess_params = {}
        self.tesseract_available = TESSERACT_INSTALLED
        
        if tesseract_cmd:
            try:
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
                # Test if Tesseract is working
                pytesseract.get_tesseract_version()
                self.tesseract_available = True
            except Exception as e:
                logger.warning(f"Failed to initialize Tesseract with provided path: {e}")
                self.tesseract_available = False
        
        if self.tesseract_available:
            # Configure Tesseract parameters for better OCR
            self.tess_params = {
                'config': '--psm 6',  # Assume a single uniform block of text
                'lang': 'eng',        # English language
                'timeout': 60         # Timeout in seconds
            }
    
    def is_searchable_pdf(self, pdf_path: str) -> bool:
        """Check if a PDF contains searchable text."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Check first few pages for text
                for i, page in enumerate(pdf.pages):
                    if i >= 3:  # Check up to 3 pages
                        break
                    if page.extract_text(strip=True):
                        return True
            return False
        except Exception as e:
            logger.warning(f"Error checking if PDF is searchable: {e}")
            return False
    
    def extract_text_from_searchable_pdf(self, pdf_path: str) -> str:
        """Extract text from searchable PDFs."""
        text = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text.append(page_text.strip())
            return '\n\n'.join(text)
        except Exception as e:
            logger.error(f"Error extracting text from searchable PDF: {e}")
            return ""
    
    def process_image_page(self, image: Image.Image, page_num: int) -> str:
        """Process a single image page with OCR."""
        try:
            # Convert to grayscale for better OCR
            image = image.convert('L')
            
            # Apply basic image processing
            # image = image.point(lambda x: 0 if x < 140 else 255)  # Simple thresholding
            
            # Perform OCR
            return pytesseract.image_to_string(image, **self.tess_params).strip()
        except Exception as e:
            logger.error(f"Error processing page {page_num} with OCR: {e}")
            return ""
    
    def extract_text_from_scanned_pdf(self, pdf_path: str, dpi: int = 200) -> str:
        """Extract text from scanned PDFs using OCR with memory efficiency."""
        if not self.tesseract_available:
            logger.error("Tesseract OCR is not available. Cannot process scanned PDF.")
            return ""
            
        temp_dir = tempfile.mkdtemp()
        try:
            # Process PDF in chunks to save memory
            text_pages = []
            
            # First, get total page count without loading all pages
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
            
            # Process pages in chunks
            chunk_size = 5  # Process 5 pages at a time
            for chunk_start in range(0, total_pages, chunk_size):
                chunk_end = min(chunk_start + chunk_size, total_pages)
                
                # Convert only the current chunk of pages to images
                images = pdf2image.convert_from_path(
                    pdf_path,
                    dpi=dpi,
                    first_page=chunk_start + 1,  # 1-based index
                    last_page=chunk_end,
                    thread_count=1,  # Reduce memory usage
                    output_folder=temp_dir,
                    fmt='png',
                    use_pdftocairo=True
                )
                
                # Process each page in the chunk
                for i, image in enumerate(images):
                    page_num = chunk_start + i + 1
                    try:
                        text = self.process_image_page(image, page_num)
                        if text.strip():
                            text_pages.append(text)
                        # Explicitly close and clean up the image
                        image.close()
                        del image
                    except Exception as e:
                        logger.error(f"Error processing page {page_num}: {e}")
                
                # Force garbage collection
                del images
                gc.collect()
            
            return '\n\n'.join(text_pages)
            
        except Exception as e:
            logger.error(f"Error processing scanned PDF with OCR: {e}")
            return ""
        finally:
            # Clean up temporary files
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                logger.warning(f"Error cleaning up temporary files: {e}")
    
    def is_already_processed(self, pdf_path: Path, output_dir: Path) -> bool:
        """Check if a PDF has already been processed by looking for its markdown file."""
        output_path = output_dir / f"{pdf_path.stem}.md"
        return output_path.exists()
        
    def process_pdf(self, pdf_path: str, output_dir: str = None, force: bool = False) -> Tuple[bool, str]:
        """
        Process a single PDF file and save extracted text to a markdown file.
        
        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save the extracted text (default: same as PDF)
            force: If True, reprocess even if output already exists
            
        Returns:
            Tuple of (success, output_path, status) where status is 'skipped', 'processed', or 'failed'
        """
        try:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                logger.error(f"PDF file not found: {pdf_path}")
                return False, ""
            
            # Determine output path
            if output_dir is None:
                output_dir = pdf_path.parent
            else:
                output_dir = Path(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
            
            output_path = output_dir / f"{pdf_path.stem}.md"
            
            # Check if already processed and not forcing
            if not force and self.is_already_processed(pdf_path, output_dir):
                logger.info(f"Skipping already processed: {pdf_path.name}")
                return True, str(output_path), 'skipped' 
                
            # Ensure output directory exists
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Determine if PDF is searchable or scanned
            is_searchable = self.is_searchable_pdf(str(pdf_path))
            
            # Extract text based on PDF type
            if is_searchable:
                logger.info(f"Processing searchable PDF: {pdf_path.name}")
                text = self.extract_text_from_searchable_pdf(str(pdf_path))
            else:
                logger.info(f"Processing scanned PDF with OCR: {pdf_path.name}")
                text = self.extract_text_from_scanned_pdf(str(pdf_path))
            
            # Clean and save the extracted text
            if text.strip():
                # Add metadata
                metadata = f"""---
source: {pdf_path.name}
type: {'searchable' if is_searchable else 'scanned'}
---

"""
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(metadata + text)
                
                logger.info(f"Successfully processed: {pdf_path.name}")
                return True, str(output_path), 'processed'
            else:
                logger.warning(f"No text extracted from: {pdf_path.name}")
                return False, "", 'failed'
                
        except Exception as e:
            logger.error(f"Error processing {pdf_path}: {e}")
            return False, "", 'failed'

def process_directory(input_dir: str, output_dir: str = None, max_workers: int = 2, 
                     force: bool = False) -> Dict[str, Dict[str, str]]:
    """
    Process all PDFs in a directory with memory-efficient handling.
    
    Args:
        input_dir: Directory containing PDFs
        output_dir: Directory to save extracted text (default: input_dir/extracted_text)
        max_workers: Number of worker processes (reduced to 2 by default for memory)
        force: If True, reprocess even if output exists
        
    Returns:
        Dictionary mapping input PDF paths to processing results
    """
    """
    Process all PDFs in a directory.
    
    Args:
        input_dir: Directory containing PDFs
        output_dir: Directory to save extracted text (default: input_dir/text)
        max_workers: Number of worker threads for parallel processing
        
    Returns:
        Dictionary mapping input PDF paths to output markdown paths
    """
    input_dir = Path(input_dir)
    if output_dir is None:
        output_dir = input_dir / "extracted_text"
    else:
        output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all PDF files
    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDF files found in {input_dir}")
        return {}
    
    extractor = PDFExtractor()
    results = {}
    
    # Process PDFs with limited concurrency to avoid memory issues
    # Use ProcessPoolExecutor to isolate memory usage between processes
    max_workers = min(max_workers, 2)  # Limit to 2 workers max for memory
    
    # Process one PDF at a time if Tesseract is being used
    if extractor.tesseract_available:
        max_workers = 1
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(extractor.process_pdf, str(pdf), str(output_dir), force): pdf
            for pdf in pdf_files
        }
        
        # Track progress with tqdm
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing PDFs"):
            pdf_path = futures[future]
            try:
                success, output_path, status = future.result()
                results[str(pdf_path)] = {
                    'status': status,
                    'output_path': output_path if success else None,
                    'success': success
                }
            except Exception as e:
                logger.error(f"Error processing {pdf_path}: {e}")
                results[str(pdf_path)] = {
                    'status': 'failed',
                    'output_path': None,
                    'success': False,
                    'error': str(e)
                }
    
    return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Extract text from PDFs (both searchable and scanned)")
    parser.add_argument("input", help="Input PDF file or directory")
    parser.add_argument("-o", "--output", help="Output directory (default: input_dir/extracted_text)")
    parser.add_argument("-w", "--workers", type=int, default=2, 
                        help="Number of worker processes (default: 2, reduced for memory)")
    parser.add_argument("--tesseract", help="Path to Tesseract executable")
    parser.add_argument("--force", action="store_true", 
                       help="Force reprocessing of all files, even if they exist")
    
    args = parser.parse_args()
    
    extractor = PDFExtractor(tesseract_cmd=args.tesseract)
    
    # Print processing summary
    def print_summary(results):
        if not results:
            print("No files were processed.")
            return
            
        total = len(results)
        processed = sum(1 for r in results.values() if r['status'] == 'processed')
        skipped = sum(1 for r in results.values() if r['status'] == 'skipped')
        failed = sum(1 for r in results.values() if r['status'] == 'failed')
        
        print("\n" + "="*50)
        print(f"{'Processing Summary':^50}")
        print("="*50)
        print(f"Total PDFs: {total}")
        print(f"Successfully processed: {processed}")
        print(f"Skipped (already processed): {skipped}")
        print(f"Failed: {failed}")
        print("="*50)
        
        if failed > 0:
            failed_files = [k for k, v in results.items() if v['status'] == 'failed']
            print("\nFailed files:")
            for f in failed_files:
                print(f"- {f}")
        
        output_path = next((r['output_path'] for r in results.values() if r['output_path']), None)
        if output_path:
            output_dir = Path(output_path).parent
            print(f"\nOutput directory: {output_dir.absolute()}")
    
    input_path = Path(args.input)
    if input_path.is_file():
        success, output_path, status = extractor.process_pdf(
            str(input_path), 
            args.output,
            args.force
        )
        print_summary({
            str(input_path): {
                'status': status,
                'output_path': output_path if success else None,
                'success': success
            }
        })
    else:
        results = process_directory(
            str(input_path),
            output_dir=args.output,
            max_workers=args.workers,
            force=args.force
        )
        print_summary(results)
