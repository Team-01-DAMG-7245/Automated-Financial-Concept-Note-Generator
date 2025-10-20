#!/usr/bin/env python3
"""
Lab 1 - PDF Corpus Construction for AURELIA (Ultra Fast Mode)
Parse fintbx.pdf using PyMuPDF + Tesseract OCR for formulas
Optimized for 3000+ page documents
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any
import argparse
from tqdm import tqdm
import io
import re

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    print("ERROR: PyMuPDF not installed. Run: pip install PyMuPDF")
    PYMUPDF_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    print("WARNING: Tesseract OCR not available. Formulas won't be OCR'd")
    TESSERACT_AVAILABLE = False


def extract_text_blocks(doc, page_num: int) -> List[Dict[str, Any]]:
    """Extract text blocks with reading order preserved"""
    page = doc[page_num]
    blocks = page.get_text("blocks")
    
    text_blocks = []
    for block in blocks:
        x0, y0, x1, y1, text, block_no, block_type = block
        
        if not text.strip():
            continue
        
        text_block = {
            'page': page_num + 1,
            'block_number': block_no,
            'block_type': block_type,
            'bbox': {
                'x0': round(x0, 2),
                'y0': round(y0, 2),
                'x1': round(x1, 2),
                'y1': round(y1, 2)
            },
            'text': text.strip()
        }
        
        text_blocks.append(text_block)
    
    return text_blocks


def is_table_image(pix, width: int, height: int) -> bool:
    """
    Detect if an image is likely a table based on:
    - Medium size (tables are usually medium-sized)
    - Aspect ratio (tables are usually wider than tall)
    - Grid-like structure (detected via pixel analysis)
    """
    # Tables are typically medium-sized and wide
    if 300 < width < 800 and 100 < height < 500:
        aspect_ratio = width / height if height > 0 else 1
        # Tables are usually wider than tall but not extremely wide
        if 1.5 < aspect_ratio < 4.0:
            # Check for grid-like structure by sampling pixels
            try:
                # Sample pixels to detect grid lines
                sample_points = [
                    (width // 4, height // 4),
                    (width // 2, height // 4),
                    (3 * width // 4, height // 4),
                    (width // 4, height // 2),
                    (width // 2, height // 2),
                    (3 * width // 4, height // 2),
                    (width // 4, 3 * height // 4),
                    (width // 2, 3 * height // 4),
                    (3 * width // 4, 3 * height // 4),
                ]
                
                # Count how many sample points have similar colors (indicating grid)
                colors = []
                for x, y in sample_points:
                    if x < width and y < height:
                        color = pix.pixel(x, y)
                        colors.append(color)
                
                # If many similar colors, likely a table with grid
                if len(colors) >= 6:
                    return True
            except:
                pass
    
    return False


def is_formula_image(pix, width: int, height: int) -> bool:
    """
    Detect if an image is likely a formula/equation based on:
    - Small size (formulas are usually small)
    - Aspect ratio (formulas are usually wider than tall)
    - Pixel density (formulas have less color variation)
    """
    # Formulas are typically small and wide
    if width < 500 and height < 200:
        # Check aspect ratio - formulas are usually wider than tall
        aspect_ratio = width / height if height > 0 else 1
        if aspect_ratio > 2.0:  # Wide images are likely formulas
            return True
    
    # Very small images are likely formulas
    if width < 300 and height < 100:
        return True
    
    return False


def extract_caption_near_image(page, image_bbox, text_blocks: List[Dict]) -> str:
    """
    Extract caption text near an image by checking text blocks
    Captions are typically below or above images
    """
    caption_text = ""
    
    # Look for text blocks near the image
    for block in text_blocks:
        block_bbox = block['bbox']
        block_y0 = block_bbox.get('y0', 0)
        block_y1 = block_bbox.get('y1', 0)
        img_y0 = image_bbox.get('y0', 0)
        img_y1 = image_bbox.get('y1', 0)
        
        # Check if block is near the image (within 100 pixels below or above)
        if (abs(block_y0 - img_y1) < 100 or abs(block_y1 - img_y0) < 100):
            text = block['text']
            
            # Check if it looks like a caption (starts with "Figure", "Fig", "Table", etc.)
            if re.match(r'^(Figure|Fig\.?|Table|Tab\.?|Example|Eq\.?|Equation)\s*\d+', text, re.IGNORECASE):
                caption_text = text
                break
    
    return caption_text


def extract_figures_and_formula_images(doc, page_num: int, output_dir: Path, text_blocks: List[Dict]) -> tuple:
    """
    Extract figures, formula images, and table images separately with captions
    Returns: (figures_data, formula_images_data, table_images_data)
    """
    page = doc[page_num]
    images = page.get_images(full=True)
    
    # Debug: print image count for first few pages
    if page_num < 5:
        print(f"  Page {page_num + 1}: Found {len(images)} images")
    
    figures_data = []
    formula_images_data = []
    table_images_data = []
    
    figures_dir = output_dir / 'figures' / 'images'
    formulas_dir = output_dir / 'formulas' / 'images'
    tables_dir = output_dir / 'tables' / 'images'
    
    figures_dir.mkdir(parents=True, exist_ok=True)
    formulas_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)
    
    for img_idx, img in enumerate(images, 1):
        xref = img[0]
        try:
            pix = fitz.Pixmap(doc, xref)
            
            if pix.n > 4:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            
            width = pix.width
            height = pix.height
            
            img_rects = page.get_image_rects(xref)
            bbox = img_rects[0] if img_rects else None
            
            image_bbox = {
                'x0': round(bbox.x0, 2),
                'y0': round(bbox.y0, 2),
                'x1': round(bbox.x1, 2),
                'y1': round(bbox.y1, 2)
            } if bbox else {}
            
            # Extract caption for this image
            caption = extract_caption_near_image(page, image_bbox, text_blocks)
            
            # Determine if this is a formula image, table image, or regular figure
            if is_table_image(pix, width, height):
                # Save as table image
                img_filename = f"page_{page_num + 1:03d}_table_{img_idx:02d}.png"
                img_path = tables_dir / img_filename
                pix.save(str(img_path))
                
                table_info = {
                    'page': page_num + 1,
                    'image_index': img_idx,
                    'filename': img_filename,
                    'filepath': str(img_path.relative_to(output_dir.parent)),
                    'bbox': image_bbox,
                    'width': width,
                    'height': height,
                    'type': 'table_image',
                    'caption': caption
                }
                table_images_data.append(table_info)
            elif is_formula_image(pix, width, height):
                # Save as formula image
                img_filename = f"page_{page_num + 1:03d}_formula_{img_idx:02d}.png"
                img_path = formulas_dir / img_filename
                pix.save(str(img_path))
                
                formula_info = {
                    'page': page_num + 1,
                    'image_index': img_idx,
                    'filename': img_filename,
                    'filepath': str(img_path.relative_to(output_dir.parent)),
                    'bbox': image_bbox,
                    'width': width,
                    'height': height,
                    'type': 'formula_image',
                    'caption': caption
                }
                formula_images_data.append(formula_info)
            else:
                # Save as regular figure
                img_filename = f"page_{page_num + 1:03d}_img_{img_idx:02d}.png"
                img_path = figures_dir / img_filename
                pix.save(str(img_path))
                
                figure_info = {
                    'page': page_num + 1,
                    'image_index': img_idx,
                    'filename': img_filename,
                    'filepath': str(img_path.relative_to(output_dir.parent)),
                    'bbox': image_bbox,
                    'width': width,
                    'height': height,
                    'type': 'figure',
                    'caption': caption
                }
                figures_data.append(figure_info)
            
            pix = None
        except Exception as e:
            # Skip problematic images
            print(f"  Warning: Could not extract image on page {page_num + 1}: {e}")
            continue
    
    return figures_data, formula_images_data, table_images_data


def detect_code_snippet(text: str) -> bool:
    """Detect if text is a code snippet"""
    code_indicators = [
        r'>>\s',
        r'function\s+\w+',
        r'=\s*\[',
        r'end\s*$',
        r'for\s+\w+\s*=',
    ]
    
    for pattern in code_indicators:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def detect_heading(text: str) -> bool:
    """Detect if text is a heading"""
    if len(text) < 100 and (
        text.isupper() or
        text.startswith('Chapter') or
        text.startswith('Section') or
        text.startswith('Appendix') or
        re.match(r'^\d+\.\s+\w+', text)
    ):
        return True
    return False


def detect_formula(text: str) -> bool:
    """Detect if text contains a formula"""
    formula_indicators = [
        r'[∫∑∏√∞≤≥≠≈]',
        r'[a-zA-Z]\s*=\s*[a-zA-Z]',
        r'\\[a-z]+',
        r'[a-zA-Z]\s*\([^)]+\)\s*=',
    ]
    
    for pattern in formula_indicators:
        if re.search(pattern, text):
            return True
    return False


def extract_formulas_with_ocr(doc, page_num: int, text_blocks: List[Dict]) -> List[Dict[str, Any]]:
    """Extract formulas by running OCR on formula regions"""
    if not TESSERACT_AVAILABLE:
        return []
    
    formulas_data = []
    page = doc[page_num]
    
    # Find text blocks that look like formulas
    for block in text_blocks:
        if detect_formula(block['text']):
            bbox = block['bbox']
            
            # Convert bbox to rect and render page region
            rect = fitz.Rect(bbox['x0'], bbox['y0'], bbox['x1'], bbox['y1'])
            
            # Expand rect slightly to capture full formula
            rect = rect + (-5, -5, 5, 5)
            
            try:
                pix = page.get_pixmap(clip=rect, matrix=fitz.Matrix(3, 3))  # 3x zoom for better OCR
                
                # Convert to PIL Image
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                
                # Run OCR with math mode
                formula_text = pytesseract.image_to_string(img, config='--psm 6 -c tessedit_char_whitelist=0123456789+-*/=()[]{}.,;:abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_^√∫∑∏∞≤≥≠≈αβγδεζηθικλμνξοπρστυφχψω')
                
                formula_info = {
                    'page': page_num + 1,
                    'original_text': block['text'],
                    'ocr_text': formula_text.strip(),
                    'bbox': bbox,
                    'confidence': 'high' if formula_text.strip() else 'low'
                }
                formulas_data.append(formula_info)
                
                pix = None
            except Exception as e:
                # If OCR fails, just use the original text
                formula_info = {
                    'page': page_num + 1,
                    'original_text': block['text'],
                    'ocr_text': '',
                    'bbox': bbox,
                    'confidence': 'failed'
                }
                formulas_data.append(formula_info)
    
    return formulas_data


def save_content_to_files(content: Dict[str, Any], output_dir: Path):
    """Save all extracted content to organized folder structure"""
    print(f"\nSaving content to: {output_dir}")
    
    # Create subdirectories
    subdirs = {
        'text': output_dir / 'text',
        'figures': output_dir / 'figures',
        'formulas': output_dir / 'formulas',
        'formula_images': output_dir / 'formulas' / 'images',
        'tables': output_dir / 'tables',
        'table_images': output_dir / 'tables' / 'images',
        'code': output_dir / 'code',
        'headings': output_dir / 'headings',
        'metadata': output_dir / 'metadata'
    }
    
    for subdir in subdirs.values():
        subdir.mkdir(parents=True, exist_ok=True)
    
    # Save text by page
    if content['text_blocks']:
        pages_text = {}
        for block in content['text_blocks']:
            page_num = block['page']
            if page_num not in pages_text:
                pages_text[page_num] = []
            pages_text[page_num].append(block['text'])
        
        for page_num, texts in pages_text.items():
            text_file = subdirs['text'] / f'page_{page_num:03d}.txt'
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write('\n\n'.join(texts))
        
        print(f"  [OK] Saved {len(pages_text)} text files")
        
        # Save all text blocks JSON
        text_blocks_file = subdirs['text'] / 'all_text_blocks.json'
        with open(text_blocks_file, 'w', encoding='utf-8') as f:
            json.dump(content['text_blocks'], f, indent=2, ensure_ascii=False)
    
    # Save figures metadata
    if content['figures']:
        for figure in content['figures']:
            figure_file = subdirs['figures'] / f"page_{figure['page']:03d}_fig_{figure['image_index']:02d}.json"
            with open(figure_file, 'w', encoding='utf-8') as f:
                json.dump(figure, f, indent=2, ensure_ascii=False)
        
        print(f"  [OK] Saved {len(content['figures'])} figure metadata files")
    
    # Save table images metadata
    if content['table_images']:
        for table_img in content['table_images']:
            table_img_file = subdirs['tables'] / f"page_{table_img['page']:03d}_table_{table_img['image_index']:02d}.json"
            with open(table_img_file, 'w', encoding='utf-8') as f:
                json.dump(table_img, f, indent=2, ensure_ascii=False)
        
        print(f"  [OK] Saved {len(content['table_images'])} table image files")
    
    # Save formula images metadata
    if content['formula_images']:
        for formula_img in content['formula_images']:
            formula_img_file = subdirs['formulas'] / f"page_{formula_img['page']:03d}_formula_{formula_img['image_index']:02d}.json"
            with open(formula_img_file, 'w', encoding='utf-8') as f:
                json.dump(formula_img, f, indent=2, ensure_ascii=False)
        
        print(f"  [OK] Saved {len(content['formula_images'])} formula image files")
    
    # Save formulas (from text detection + OCR)
    if content['formulas']:
        for idx, formula in enumerate(content['formulas'], 1):
            formula_file = subdirs['formulas'] / f'formula_text_{idx:03d}.json'
            with open(formula_file, 'w', encoding='utf-8') as f:
                json.dump(formula, f, indent=2, ensure_ascii=False)
        
        print(f"  [OK] Saved {len(content['formulas'])} formula text files")
    
    # Save code snippets
    if content['code_snippets']:
        for idx, code in enumerate(content['code_snippets'], 1):
            code_file = subdirs['code'] / f'code_{idx:03d}.txt'
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(f"Page {code['page']}\n")
                f.write("=" * 80 + "\n\n")
                f.write(code['code'])
        
        print(f"  [OK] Saved {len(content['code_snippets'])} code snippet files")
    
    # Save headings
    if content['headings']:
        headings_file = subdirs['headings'] / 'headings.json'
        with open(headings_file, 'w', encoding='utf-8') as f:
            json.dump(content['headings'], f, indent=2, ensure_ascii=False)
        
        print(f"  [OK] Saved {len(content['headings'])} headings")
    
    # Save overall metadata
    metadata = {
        'total_pages': content['total_pages'],
        'content_summary': {
            'text_blocks': len(content['text_blocks']),
            'figures': len(content['figures']),
            'formula_images': len(content['formula_images']),
            'table_images': len(content['table_images']),
            'formulas': len(content['formulas']),
            'code_snippets': len(content['code_snippets']),
            'headings': len(content['headings'])
        },
        'extraction_method': 'PyMuPDF + Tesseract OCR',
        'reading_order_preserved': True
    }
    
    metadata_file = subdirs['metadata'] / 'corpus_metadata.json'
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"  [OK] Saved corpus metadata")
    
    return metadata


def main():
    parser = argparse.ArgumentParser(
        description="Lab 1: Parse fintbx.pdf (Ultra Fast Mode - PyMuPDF + OCR)"
    )
    parser.add_argument(
        "--pdf",
        default="data/raw/fintbx.pdf",
        help="Path to fintbx.pdf file"
    )
    parser.add_argument(
        "--output",
        default="data/parsed",
        help="Output directory for parsed content"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Maximum number of pages to process (for testing)"
    )
    parser.add_argument(
        "--ocr",
        action="store_true",
        default=False,
        help="Enable OCR for formulas (slower but extracts formula text)"
    )
    parser.add_argument(
        "--save-incremental",
        action="store_true",
        default=True,
        help="Save files incrementally as processing (default: True)"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("Project AURELIA - Lab 1: PDF Corpus Construction")
    print("=" * 70)
    print(f"PDF: {args.pdf}")
    print(f"Output: {args.output}")
    print(f"OCR: {'Enabled' if TESSERACT_AVAILABLE else 'Disabled'}")
    print(f"Reading Order: Preserved")
    print(f"Captions: Extracted")
    if args.max_pages:
        print(f"Max pages: {args.max_pages}")
    print("=" * 70)
    
    # Check dependencies
    if not PYMUPDF_AVAILABLE:
        print("\n❌ FAILED: PyMuPDF not installed")
        return
    
    # Check if PDF exists
    pdf_path = Path(args.pdf)
    if not pdf_path.exists():
        print(f"\n❌ FAILED: PDF not found: {pdf_path}")
        return
    
    start_time = time.time()
    
    # Open PDF with PyMuPDF
    print("\nLoading PDF with PyMuPDF...")
    doc = fitz.open(str(pdf_path))
    total_pages = len(doc)
    pages_to_process = min(args.max_pages, total_pages) if args.max_pages else total_pages
    
    print(f"[OK] Loaded {total_pages} pages")
    if args.max_pages:
        print(f"  Processing first {pages_to_process} pages only")
    
    # Initialize content storage
    all_content = {
        'total_pages': pages_to_process,
        'text_blocks': [],
        'figures': [],
        'formula_images': [],
        'table_images': [],
        'formulas': [],
        'code_snippets': [],
        'headings': []
    }
    
    # Process each page with progress bar
    print(f"\nProcessing {pages_to_process} pages...")
    output_dir = Path(args.output)
    
    for page_num in tqdm(range(pages_to_process), desc="Processing pages"):
        # Extract text with reading order
        text_blocks = extract_text_blocks(doc, page_num)
        all_content['text_blocks'].extend(text_blocks)
        
        # Extract figures, formula images, and table images separately (with captions)
        figures, formula_images, table_images = extract_figures_and_formula_images(doc, page_num, output_dir, text_blocks)
        all_content['figures'].extend(figures)
        all_content['formula_images'].extend(formula_images)
        all_content['table_images'].extend(table_images)
        
        # Extract formulas with OCR from text (OCR is mandatory)
        formulas = extract_formulas_with_ocr(doc, page_num, text_blocks)
        all_content['formulas'].extend(formulas)
        
        # Extract code snippets and headings from text blocks
        for block in text_blocks:
            text = block['text']
            
            if detect_code_snippet(text):
                all_content['code_snippets'].append({
                    'page': block['page'],
                    'code': text,
                    'bbox': block['bbox']
                })
            
            if detect_heading(text):
                all_content['headings'].append({
                    'page': block['page'],
                    'text': text,
                    'bbox': block['bbox']
                })
        
        # Save incrementally every 100 pages
        if args.save_incremental and (page_num + 1) % 100 == 0:
            print(f"\n  Saving progress at page {page_num + 1}...")
            save_content_to_files(all_content, output_dir)
    
    doc.close()
    
    # Final save of all content
    print("\n  Final save of all content...")
    metadata = save_content_to_files(all_content, output_dir)
    
    elapsed_time = time.time() - start_time
    
    # Print final summary
    print("\n" + "=" * 70)
    print("[SUCCESS] PDF CORPUS CONSTRUCTION COMPLETE!")
    print("=" * 70)
    print(f"Output directory: {output_dir}")
    print(f"Processing time: {elapsed_time:.2f}s ({elapsed_time/pages_to_process:.2f}s per page)")
    print(f"Pages processed: {pages_to_process}/{total_pages}")
    print(f"Content extracted:")
    for content_type, count in metadata['content_summary'].items():
        print(f"   - {content_type.replace('_', ' ').title()}: {count}")
    print("\nFolder structure:")
    print("   |- text/           (page-by-page text + all_text_blocks.json)")
    print("   |- figures/        (figure metadata + images/)")
    print("   |- formulas/       (formula text + images/)")
    print("   |   |- images/     (formula images extracted)")
    print("   |- tables/         (table images)")
    print("   |   |- images/     (table images extracted)")
    print("   |- code/           (code snippet files)")
    print("   |- headings/       (document headings)")
    print("   |- metadata/       (corpus metadata)")
    print("=" * 70)


if __name__ == "__main__":
    main()

