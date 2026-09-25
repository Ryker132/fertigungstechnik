"""Render every lecture slide to a JPEG. Idempotent: skips existing files."""
import pymupdf
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT.parent / "Data"
OUT = ROOT / "slides"

JOBS = [
    ("ft1", "FT-1_Urformen_2015-07-08.pdf"),
    ("ft2", "FT-2_Umformen_2015-07-08.pdf"),
    ("ft3", "FT-3_Trennen_2015-07-08.pdf"),
    ("ft5", "FT-5_Beschichten_2015-07-08.pdf"),
    ("ft6", "FT-6_Handhabung_von_Industrierobotern_2015-07-08.pdf"),
    ("ft7", "FT-7_Grundlagen_Fertigungsprozesse_2015-07-08.pdf"),
]

def main():
    made = 0
    skipped = 0
    for folder, pdf_name in JOBS:
        dest = OUT / folder
        dest.mkdir(parents=True, exist_ok=True)
        doc = pymupdf.open(DATA / pdf_name)
        mat = pymupdf.Matrix(1.9, 1.9)
        for i, page in enumerate(doc, start=1):
            target = dest / f"{i:03d}.jpg"
            if target.exists() and target.stat().st_size > 8000:
                skipped += 1
                continue
            pix = page.get_pixmap(matrix=mat, alpha=False)
            pix.save(str(target), jpg_quality=76)
            made += 1
        print(folder, "pages", doc.page_count, flush=True)
    print("rendered", made, "skipped", skipped, flush=True)

if __name__ == "__main__":
    main()
