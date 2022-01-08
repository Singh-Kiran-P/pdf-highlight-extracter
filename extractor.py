import textwrap
from fpdf import FPDF
from typing import List, Tuple
import re

import fitz
from pyparsing import unicode


def _parse_highlight(annot: fitz.Annot, wordlist: List[Tuple[float, float, float, float, str, int, int, int]]) -> str:
    points = annot.vertices
    quad_count = int(len(points) / 4)
    sentences = []
    for i in range(quad_count):
        # where the highlighted part is
        r = fitz.Quad(points[i * 4: i * 4 + 4]).rect

        words = [w for w in wordlist if fitz.Rect(w[:4]).intersects(r)]
        sentences.append(" ".join(w[4] for w in words))
    sentence = " ".join(sentences)
    return sentence


def handle_page(page):
    wordlist = page.getText(
        'words', flags=fitz.TEXT_PRESERVE_LIGATURES | fitz.TEXT_INHIBIT_SPACES)

    wordlist.sort(key=lambda w: (w[3], w[0]))  # ascending y, then x

    highlights = []
    annot = page.firstAnnot
    while annot:
        if annot.type[0] == 8:
            highlights.append(_parse_highlight(annot, wordlist))
        annot = annot.next
    return highlights


def main(filepath: str) -> List:
    doc = fitz.open(filepath)

    highlights = []
    for page in doc:
        highlights += handle_page(page)

    return highlights


def text_to_pdf(filename, data):
    a4_width_mm = 210
    pt_to_mm = 0.35
    fontsize_pt = 13
    fontsize_mm = fontsize_pt * pt_to_mm
    margin_bottom_mm = 10
    character_width_mm = 7 * pt_to_mm
    width_text = a4_width_mm / character_width_mm

    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.set_auto_page_break(True, margin=margin_bottom_mm)
    pdf.add_page()
    pdf.set_font(family='Arial', size=fontsize_pt)

    for i in range(len(data)):
        result = data[i]
        result.replace("\xa0", "")
        result = re.sub(r'[^\x00-\x7f]', r'', data[i])
        lines = textwrap.wrap(result, width_text)

        if len(lines) == 0:
            pdf.ln()

        for wrap in lines:
            pdf.cell(0, fontsize_mm, wrap, ln=1)
        pdf.ln()
        pdf.ln()


    pdf.output(filename, 'F')

if __name__ == "__main__":

    text_to_pdf("export.pdf",main("example.pdf"))
