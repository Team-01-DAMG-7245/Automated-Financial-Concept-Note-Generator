#!/usr/bin/env python3
"""
Markdown Generator for AURELIA
Converts parsed PDF data to clean, well-structured Markdown format
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any
import argparse


def load_parsed_data(parsed_dir: Path) -> Dict[str, Any]:
    """Load all parsed data from the parsed directory"""
    data = {
        'text_blocks': [],
        'figures': [],
        'formula_images': [],
        'table_images': [],
        'code_snippets': [],
        'headings': [],
        'metadata': {}
    }
    
    # Load text blocks
    text_blocks_file = parsed_dir / 'text' / 'all_text_blocks.json'
    if text_blocks_file.exists():
        with open(text_blocks_file, 'r', encoding='utf-8') as f:
            data['text_blocks'] = json.load(f)
    
    # Load headings
    headings_file = parsed_dir / 'headings' / 'headings.json'
    if headings_file.exists():
        with open(headings_file, 'r', encoding='utf-8') as f:
            data['headings'] = json.load(f)
    
    # Load code snippets
    code_dir = parsed_dir / 'code'
    if code_dir.exists():
        for code_file in sorted(code_dir.glob('code_*.txt')):
            with open(code_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Extract page number from content
                page_match = re.search(r'Page (\d+)', content)
                page_num = int(page_match.group(1)) if page_match else 0
                code = content.split('=' * 80)[-1].strip()
                data['code_snippets'].append({
                    'page': page_num,
                    'code': code
                })
    
    # Load figures
    figures_dir = parsed_dir / 'figures'
    if figures_dir.exists():
        for fig_file in sorted(figures_dir.glob('page_*_fig_*.json')):
            with open(fig_file, 'r', encoding='utf-8') as f:
                data['figures'].append(json.load(f))
    
    # Load formula images
    formulas_dir = parsed_dir / 'formulas'
    if formulas_dir.exists():
        for formula_file in sorted(formulas_dir.glob('page_*_formula_*.json')):
            with open(formula_file, 'r', encoding='utf-8') as f:
                data['formula_images'].append(json.load(f))
    
    # Load table images
    tables_dir = parsed_dir / 'tables'
    if tables_dir.exists():
        for table_file in sorted(tables_dir.glob('page_*_table_*.json')):
            with open(table_file, 'r', encoding='utf-8') as f:
                data['table_images'].append(json.load(f))
    
    # Load metadata
    metadata_file = parsed_dir / 'metadata' / 'corpus_metadata.json'
    if metadata_file.exists():
        with open(metadata_file, 'r', encoding='utf-8') as f:
            data['metadata'] = json.load(f)
    
    return data


def determine_heading_level(text: str) -> int:
    """Determine heading level based on text characteristics"""
    text_lower = text.lower()
    
    # Chapter headings
    if text.startswith('Chapter') or text.startswith('CHAPTER'):
        return 1
    
    # Section headings
    if text.startswith('Section') or text.startswith('SECTION'):
        return 2
    
    # Appendix
    if text.startswith('Appendix') or text.startswith('APPENDIX'):
        return 1
    
    # Numbered headings (1., 2., etc.)
    if re.match(r'^\d+\.\s+[A-Z]', text):
        return 2
    
    # Numbered subheadings (1.1, 1.2, etc.)
    if re.match(r'^\d+\.\d+\.?\s+[A-Z]', text):
        return 3
    
    # All caps (likely heading)
    if text.isupper() and len(text) < 100:
        return 2
    
    # Default
    return 2


def format_code_block(code: str, language: str = 'matlab') -> str:
    """Format code as markdown code block"""
    return f"```{language}\n{code}\n```"


def format_image_reference(image_data: Dict, image_type: str) -> str:
    """Format image reference in markdown"""
    page = image_data['page']
    caption = image_data.get('caption', '')
    filename = image_data['filename']
    
    if image_type == 'figure':
        path = f"figures/images/{filename}"
        alt_text = caption if caption else f"Figure from page {page}"
    elif image_type == 'formula':
        path = f"formulas/images/{filename}"
        alt_text = caption if caption else f"Formula from page {page}"
    elif image_type == 'table':
        path = f"tables/images/{filename}"
        alt_text = caption if caption else f"Table from page {page}"
    else:
        path = filename
        alt_text = f"Image from page {page}"
    
    return f"![{alt_text}]({path})"


def format_formula(formula_text: str) -> str:
    """Format formula in LaTeX notation"""
    # Basic LaTeX formatting
    formula_text = formula_text.strip()
    
    # If it already looks like LaTeX, use it as-is
    if '\\' in formula_text or '$' in formula_text:
        return f"$${formula_text}$$"
    
    # Otherwise, wrap in LaTeX delimiters
    return f"$${formula_text}$$"


def generate_markdown(parsed_data: Dict[str, Any], output_file: Path):
    """Generate comprehensive markdown from parsed data"""
    
    print(f"Generating markdown from parsed data...")
    
    # Group content by page
    pages_content = {}
    
    # Add text blocks
    for block in parsed_data['text_blocks']:
        page = block['page']
        if page not in pages_content:
            pages_content[page] = {
                'text': [],
                'code': [],
                'figures': [],
                'formulas': [],
                'tables': [],
                'headings': []
            }
        pages_content[page]['text'].append(block['text'])
    
    # Add headings
    for heading in parsed_data['headings']:
        page = heading['page']
        if page not in pages_content:
            pages_content[page] = {
                'text': [],
                'code': [],
                'figures': [],
                'formulas': [],
                'tables': [],
                'headings': []
            }
        pages_content[page]['headings'].append(heading)
    
    # Add code snippets
    for code in parsed_data['code_snippets']:
        page = code['page']
        if page not in pages_content:
            pages_content[page] = {
                'text': [],
                'code': [],
                'figures': [],
                'formulas': [],
                'tables': [],
                'headings': []
            }
        pages_content[page]['code'].append(code)
    
    # Add figures
    for figure in parsed_data['figures']:
        page = figure['page']
        if page not in pages_content:
            pages_content[page] = {
                'text': [],
                'code': [],
                'figures': [],
                'formulas': [],
                'tables': [],
                'headings': []
            }
        pages_content[page]['figures'].append(figure)
    
    # Add formula images
    for formula in parsed_data['formula_images']:
        page = formula['page']
        if page not in pages_content:
            pages_content[page] = {
                'text': [],
                'code': [],
                'figures': [],
                'formulas': [],
                'tables': [],
                'headings': []
            }
        pages_content[page]['formulas'].append(formula)
    
    # Add table images
    for table in parsed_data['table_images']:
        page = table['page']
        if page not in pages_content:
            pages_content[page] = {
                'text': [],
                'code': [],
                'figures': [],
                'formulas': [],
                'tables': [],
                'headings': []
            }
        pages_content[page]['tables'].append(table)
    
    # Generate markdown content
    markdown_lines = []
    markdown_lines.append("# Financial Toolbox User's Guide\n")
    markdown_lines.append(f"*Generated from fintbx.pdf ({parsed_data['metadata'].get('total_pages', 'unknown')} pages)*\n")
    markdown_lines.append("---\n")
    
    # Process each page
    for page_num in sorted(pages_content.keys()):
        content = pages_content[page_num]
        
        # Add page separator
        markdown_lines.append(f"\n<!-- Page: {page_num} -->\n")
        markdown_lines.append(f"## Page {page_num}\n")
        
        # Add headings first
        for heading in content['headings']:
            level = determine_heading_level(heading['text'])
            heading_md = '#' * level
            markdown_lines.append(f"{heading_md} {heading['text']}\n")
        
        # Add text content
        if content['text']:
            for text in content['text']:
                markdown_lines.append(f"{text}\n\n")
        
        # Add code snippets
        for code in content['code']:
            markdown_lines.append(f"\n**Code Snippet (Page {code['page']}):**\n")
            markdown_lines.append(format_code_block(code['code']))
            markdown_lines.append("\n")
        
        # Add figures
        for figure in content['figures']:
            markdown_lines.append(f"\n**Figure:**\n")
            markdown_lines.append(format_image_reference(figure, 'figure'))
            if figure.get('caption'):
                markdown_lines.append(f"\n*{figure['caption']}*\n")
            markdown_lines.append("\n")
        
        # Add formulas
        for formula in content['formulas']:
            markdown_lines.append(f"\n**Formula:**\n")
            markdown_lines.append(format_image_reference(formula, 'formula'))
            if formula.get('caption'):
                markdown_lines.append(f"\n*{formula['caption']}*\n")
            markdown_lines.append("\n")
        
        # Add tables
        for table in content['tables']:
            markdown_lines.append(f"\n**Table:**\n")
            markdown_lines.append(format_image_reference(table, 'table'))
            if table.get('caption'):
                markdown_lines.append(f"\n*{table['caption']}*\n")
            markdown_lines.append("\n")
        
        markdown_lines.append("---\n")
    
    # Write markdown file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(''.join(markdown_lines))
    
    print(f"[OK] Markdown generated: {output_file}")
    print(f"[OK] Total pages: {len(pages_content)}")
    print(f"[OK] Total size: {len(''.join(markdown_lines)):,} characters")


def generate_metadata_json(parsed_data: Dict[str, Any], output_file: Path):
    """Generate metadata JSON with document structure"""
    
    metadata = {
        'document_info': {
            'title': "Financial Toolbox User's Guide",
            'source': 'fintbx.pdf',
            'total_pages': parsed_data['metadata'].get('total_pages', 0),
            'extraction_method': parsed_data['metadata'].get('extraction_method', 'Unknown')
        },
        'content_summary': parsed_data['metadata'].get('content_summary', {}),
        'structure': {
            'headings': len(parsed_data['headings']),
            'code_snippets': len(parsed_data['code_snippets']),
            'figures': len(parsed_data['figures']),
            'formulas': len(parsed_data['formula_images']),
            'tables': len(parsed_data['table_images'])
        },
        'headings_by_level': {},
        'pages_with_content': {}
    }
    
    # Count headings by level
    for heading in parsed_data['headings']:
        level = determine_heading_level(heading['text'])
        if level not in metadata['headings_by_level']:
            metadata['headings_by_level'][level] = 0
        metadata['headings_by_level'][level] += 1
    
    # Write metadata JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"[OK] Metadata generated: {output_file}")


def validate_markdown(markdown_file: Path) -> bool:
    """Validate the generated markdown file"""
    
    print(f"\nValidating markdown file...")
    
    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for required elements
    checks = {
        'Has headings': '#' in content,
        'Has page markers': '<!-- Page:' in content,
        'Has code blocks': '```' in content,
        'Has images': '![' in content,
        'Has content': len(content) > 1000,
    }
    
    all_passed = all(checks.values())
    
    print("\nValidation Results:")
    for check, passed in checks.items():
        status = "[OK]" if passed else "[FAIL]"
        print(f"  {status} {check}")
    
    if all_passed:
        print("\n[SUCCESS] Markdown validation passed!")
    else:
        print("\n[WARNING] Some validation checks failed")
    
    return all_passed


def main():
    parser = argparse.ArgumentParser(
        description="Generate markdown from parsed PDF data"
    )
    parser.add_argument(
        "--parsed-dir",
        default="data/parsed",
        help="Directory containing parsed PDF data"
    )
    parser.add_argument(
        "--output",
        default="outputs/fintbx_complete.md",
        help="Output markdown file"
    )
    parser.add_argument(
        "--metadata",
        default="outputs/fintbx_metadata.json",
        help="Output metadata JSON file"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate the generated markdown"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("Project AURELIA - Markdown Generator")
    print("=" * 70)
    print(f"Parsed data: {args.parsed_dir}")
    print(f"Output markdown: {args.output}")
    print(f"Output metadata: {args.metadata}")
    print("=" * 70)
    
    # Check if parsed directory exists
    parsed_dir = Path(args.parsed_dir)
    if not parsed_dir.exists():
        print(f"\n[ERROR] Parsed directory not found: {parsed_dir}")
        return
    
    # Create output directory
    output_file = Path(args.output)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    metadata_file = Path(args.metadata)
    metadata_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Load parsed data
    print("\nLoading parsed data...")
    parsed_data = load_parsed_data(parsed_dir)
    
    print(f"[OK] Loaded:")
    print(f"  - Text blocks: {len(parsed_data['text_blocks'])}")
    print(f"  - Headings: {len(parsed_data['headings'])}")
    print(f"  - Code snippets: {len(parsed_data['code_snippets'])}")
    print(f"  - Figures: {len(parsed_data['figures'])}")
    print(f"  - Formulas: {len(parsed_data['formula_images'])}")
    print(f"  - Tables: {len(parsed_data['table_images'])}")
    
    # Generate markdown
    print("\nGenerating markdown...")
    generate_markdown(parsed_data, output_file)
    
    # Generate metadata
    print("\nGenerating metadata...")
    generate_metadata_json(parsed_data, metadata_file)
    
    # Validate if requested
    if args.validate:
        validate_markdown(output_file)
    
    print("\n" + "=" * 70)
    print("[SUCCESS] MARKDOWN GENERATION COMPLETE!")
    print("=" * 70)
    print(f"Output files:")
    print(f"  - Markdown: {output_file}")
    print(f"  - Metadata: {metadata_file}")
    print("=" * 70)


if __name__ == "__main__":
    main()

