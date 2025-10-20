import fitz

doc = fitz.open('data/raw/fintbx.pdf')
print(f"Total pages: {len(doc)}")

total_imgs = 0
for i in range(min(100, len(doc))):
    imgs = doc[i].get_images(full=True)
    total_imgs += len(imgs)
    if i < 10:
        print(f"Page {i+1}: {len(imgs)} images")

print(f"\nTotal images in first 100 pages: {total_imgs}")

# Check if images exist in the parsed folder
import os
from pathlib import Path

figures_dir = Path("data/parsed/figures/images")
formulas_dir = Path("data/parsed/formulas/images")
tables_dir = Path("data/parsed/tables/images")

print(f"\nFigures folder exists: {figures_dir.exists()}")
print(f"Formulas folder exists: {formulas_dir.exists()}")
print(f"Tables folder exists: {tables_dir.exists()}")

if figures_dir.exists():
    figure_files = list(figures_dir.glob("*.png"))
    print(f"Figure images saved: {len(figure_files)}")

if formulas_dir.exists():
    formula_files = list(formulas_dir.glob("*.png"))
    print(f"Formula images saved: {len(formula_files)}")

if tables_dir.exists():
    table_files = list(tables_dir.glob("*.png"))
    print(f"Table images saved: {len(table_files)}")

