#!/usr/bin/env python3
"""Render every page of a PDF to PNG for visual document QA."""

from __future__ import annotations

import argparse
from pathlib import Path
import pymupdf


def render(pdf_path: Path, output_dir: Path, dpi: int = 180) -> int:
    document = pymupdf.open(pdf_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    for index, page in enumerate(document, start=1):
        page.get_pixmap(dpi=dpi).save(output_dir / f"page-{index:02d}.png")
    return len(document)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--dpi", type=int, default=180)
    args = parser.parse_args()
    print(f"Rendered {render(args.pdf, args.output_dir, args.dpi)} pages")


if __name__ == "__main__":
    main()
