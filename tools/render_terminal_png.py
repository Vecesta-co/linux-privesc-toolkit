#!/usr/bin/env python3
"""Render a real text transcript into a simple terminal-style PNG."""

from __future__ import annotations

import argparse
from pathlib import Path
import textwrap

from PIL import Image, ImageDraw, ImageFont


def render(source: Path, output: Path, title: str = "Recorded terminal output", keyword: str | None = None, context: int = 1, max_lines: int = 44) -> Path:
    raw = source.read_text(encoding="utf-8", errors="replace").splitlines()
    if keyword:
        selected = set()
        for index, line in enumerate(raw):
            if keyword.casefold() in line.casefold():
                selected.update(range(max(0, index-context), min(len(raw), index+context+1)))
        lines = [raw[i] for i in sorted(selected)]
    else:
        lines = raw
    lines = lines[:max_lines]
    font_path = Path("C:/Windows/Fonts/consola.ttf")
    if not font_path.exists(): font_path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf")
    font = ImageFont.truetype(str(font_path), 19) if font_path.exists() else ImageFont.load_default()
    wrapped = []
    for line in lines:
        wrapped.extend(textwrap.wrap(line, width=96, replace_whitespace=False, drop_whitespace=False) or [""])
    wrapped = wrapped[:max_lines]
    width = 1320; line_height = 29; top = 76; bottom = 30
    height = max(190, top + len(wrapped)*line_height + bottom)
    image = Image.new("RGB", (width, height), "#0E1116"); draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((12, 12, width-12, height-12), radius=16, fill="#161B22", outline="#30363D", width=2)
    draw.rounded_rectangle((12,12,width-12,58),radius=16,fill="#20262E")
    draw.rectangle((12,42,width-12,58),fill="#20262E")
    for i,color in enumerate(("#F85149","#D29922","#3FB950")):
        x=34+i*28; draw.ellipse((x,28,x+13,41),fill=color)
    draw.text((145,24),title,font=ImageFont.truetype(str(font_path),15) if font_path.exists() else font,fill="#8B949E")
    y=76
    for line in wrapped:
        color="#3FB950" if line.startswith("Command:") else "#E6EDF3"
        draw.text((34,y),line,font=font,fill=color); y+=line_height
    output.parent.mkdir(parents=True,exist_ok=True); image.save(output)
    return output


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input",type=Path); parser.add_argument("output",type=Path)
    parser.add_argument("--title",default="Recorded terminal output")
    parser.add_argument("--keyword"); parser.add_argument("--context",type=int,default=1)
    parser.add_argument("--max-lines",type=int,default=44)
    args=parser.parse_args()
    print(render(args.input,args.output,args.title,args.keyword,args.context,args.max_lines))


if __name__=="__main__": main()
