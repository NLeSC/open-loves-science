from pypdf import PdfWriter, PdfReader
import io
import csv
from reportlab.pdfgen import canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from PIL import Image, ImageDraw
import segno                                            # for qr codes
import os


DESIGN_W = 200.0
DESIGN_H = 250.0
V_MARGIN_TOP = 50
V_MARGIN_BOT = 40


def _page_size(reader, page_index):
    mb = reader.pages[page_index].mediabox
    page_w = float(mb.right) - float(mb.left)
    page_h = float(mb.top) - float(mb.bottom)
    return page_w, page_h


def _draw_card_content(can, page_w, page_h, text, textcolor, h_pos, sx, sy):
    box_w = 110 * sx
    box_h = page_h

    style = ParagraphStyle(
        'Card',
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=14,
        alignment=TA_CENTER,
        textColor=textcolor,
        spaceBefore=0,
        spaceAfter=0,
    )

    p = Paragraph(text, style)

    # Wrap using a scaled box width
    w, h = p.wrap(box_w, box_h)

    # Horizontal positioning: centered on actual page width
    x = (page_w - box_w) / 2.0

    # Top-align: keep top edge fixed (scaled from design units)
    top_y = page_h - ((h_pos + V_MARGIN_TOP) * sy)
    y = top_y - h

    p.drawOn(can, x, y)

    return h


def _draw_card_quote(can, page_w, page_h, quote, textcolor, h_pos, box_h_main_text, sx, sy):
    box_w = 110 * sx
    box_h = page_h

    style = ParagraphStyle(
        'Quote',
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        alignment=TA_CENTER,
        textColor=textcolor,
        spaceBefore=0,
        spaceAfter=0,
    )

    p = Paragraph(quote, style)

    # Wrap using a scaled box width
    w, h = p.wrap(box_w, box_h)

    # Horizontal positioning: centered on actual page width
    x = (page_w - box_w) / 2.0

    # Top-align: quote starts below main text (gap scaled from design units)
    top_y = page_h - ((h_pos + V_MARGIN_TOP) * sy) - box_h_main_text - (8 * sy)
    y = top_y - h

    p.drawOn(can, x, y)


def _round_corners_png(in_path, out_path, radius):
    img = Image.open(in_path).convert("RGBA")
    w, h = img.size

    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0, w, h), radius=radius, fill=255)

    img.putalpha(mask)
    img.save(out_path)


def add_overlay(template_pdf_paths, cardcontent, output):
    # Read your existing PDFs (back + front)
    with open(template_pdf_paths[0], "rb") as fback:
        back_bytes = io.BytesIO(fback.read())
    with open(template_pdf_paths[1], "rb") as ffront:
        front_bytes = io.BytesIO(ffront.read())

    template_pdf_back = PdfReader(back_bytes)
    template_pdf_front = PdfReader(front_bytes)

    # Actual page size + scaling factors relative to the old design space (200x250)
    page_w, page_h = _page_size(template_pdf_back, 0)
    sx = page_w / DESIGN_W
    sy = page_h / DESIGN_H
    s = min(sx, sy)  # square scaling for QR size/radius

    # Hacky way of determining text color / placement (h_pos is in DESIGN units)
    if 'White' in template_pdf_paths[0]:
        textcolor = 'black'
        h_pos = 60
    else:
        textcolor = 'white'
        h_pos = 10

    text = cardcontent[0]

    # Create a QR code if the URL column is not NA / empty
    qr_url = (cardcontent[1] or '').strip() if len(cardcontent) > 1 else ''

    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(page_w, page_h))

    # Main text
    box_h_main_text = _draw_card_content(can, page_w, page_h, text, textcolor, h_pos, sx, sy)

    # Quote
    if len(cardcontent) == 3:
        _draw_card_quote(can, page_w, page_h, cardcontent[2], textcolor, h_pos, box_h_main_text, sx, sy)

    # QR
    if qr_url:
        qrcode = segno.make_qr(qr_url)
        tmp_qr = "tmp-qr.png"
        tmp_qr_rounded = "tmp-qr-rounded.png"
        qrcode.save(tmp_qr, scale=5)

        _round_corners_png(tmp_qr, tmp_qr_rounded, radius=int(20 * s))

        qr_size = 50 * s
        qr_x = (page_w - qr_size) / 2.0
        qr_y = V_MARGIN_BOT * sy

        can.drawImage(
            tmp_qr_rounded,
            qr_x, qr_y,
            qr_size, qr_size,
            preserveAspectRatio=True, mask='auto'
        )

        os.remove(tmp_qr)
        os.remove(tmp_qr_rounded)
        
    can.save()
    packet.seek(0)

    overlay_pdf = PdfReader(packet)

    # Merge overlay onto the BACK page
    back_page = template_pdf_back.pages[0]
    back_page.merge_page(overlay_pdf.pages[0])

    # Add front and back of card
    output.add_page(template_pdf_front.pages[0])
    output.add_page(back_page)

    return output


def create_cards(template_pdf_paths, card_contents, out_pdf_path):
    output_stream = open(out_pdf_path, "wb")
    combined_pages = PdfWriter()

    with open(card_contents, newline='', encoding='utf-8-sig') as csvfile:
        cardreader = csv.reader(csvfile, delimiter=';')

        # Replaces "NA" with None
        cardreader = (
            [None if cell == "NA" else cell for cell in row]
            for row in cardreader
        )

        # This skips the first row of the CSV file.
        next(cardreader)

        for row in cardreader:
            combined_pages = add_overlay(template_pdf_paths, row, combined_pages)

        combined_pages.write(output_stream)
        output_stream.close()


# Red deck
create_cards(
    template_pdf_paths=["Red back Final.pdf", "Red front Final.pdf"],
    card_contents="CardContentRed.csv",
    out_pdf_path="OpenLovesScience_Red.pdf"
)

# White deck
create_cards(
    template_pdf_paths=["White back Final.pdf", "White front Final.pdf"],
    card_contents="CardContentWhite.csv",
    out_pdf_path="OpenLovesScience_White.pdf"
)

# Combine Red + White into one PDF (same effect as PdfMerger append order)
red = PdfReader("OpenLovesScience_Red.pdf")
white = PdfReader("OpenLovesScience_White.pdf")

writer = PdfWriter()
for page in red.pages:
    writer.add_page(page)
for page in white.pages:
    writer.add_page(page)

with open("OpenLovesScience_Cards.pdf", "wb") as f:
    writer.write(f)
