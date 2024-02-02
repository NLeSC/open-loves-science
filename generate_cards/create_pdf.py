from PyPDF2 import PdfWriter, PdfReader, PdfMerger, Transformation
import io
import csv
from reportlab.pdfgen import canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph
import segno
import os


def add_qr(url, page):
    # create a qr code and write to tmp file
    qrcode = segno.make_qr(url)
    imgPath = "tmp-qr.png"
    qrcode.save(imgPath, scale=5)
    # Using ReportLab to insert image into PDF
    imgTemp = io.BytesIO()
    imgDoc = canvas.Canvas(imgTemp)
    # Draw image on Canvas and save PDF in buffer
    imgDoc.drawImage(imgPath, 5, 5, 50, 50)  ## at (5,5) with size 50x50
    imgDoc.save()
    # overlay qr code on page
    imgTemp.seek(0)
    overlay = PdfReader(imgTemp).pages[0]
    op = Transformation().rotate(0).translate(tx=40, ty=45)
    overlay.add_transformation(op)
    page.merge_page(overlay)
    # remove temp file
    os.remove(imgPath)
    return page


def add_text_to_pdf(existing_pdf_path, cardcontent, output):
    # read your existing PDF
    existing_pdf = PdfReader(open(existing_pdf_path[0], "rb"))
    existing_pdf_back = PdfReader(open(existing_pdf_path[1], "rb"))

    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(200, 250))

    # make and draw a paragraph with the text

    # hacky way of determining text color
    if 'White' in existing_pdf_path[0]:
        textcolor = 'black'
        h_pos = 60
    else:
        textcolor = 'white'
        h_pos = 20

    my_Style = ParagraphStyle('My Para style',
                              fontName='Helvetica-Bold',
                              fontSize=12,
                              borderWidth=40,
                              borderPadding=40,
                              leading=20,
                              alignment=0,
                              textColor=textcolor
                              )
    p1 = Paragraph(cardcontent[0], my_Style)
    w, h = p1.wrap(180, round(250))
    p1.wrapOn(can, w - 50, h - 10)

    p1.drawOn(can, 200 - w + 40, 250 - h - h_pos)

    if len(cardcontent) == 3:
        # Add the quote
        my_Style = ParagraphStyle('My Para style',
                                  fontName='Helvetica-Bold',
                                  fontSize=8,
                                  borderWidth=10,
                                  borderPadding=10,
                                  leading=10,
                                  alignment=0,
                                  textColor=textcolor
                                  )
        p1 = Paragraph(cardcontent[2], my_Style)
        w, h = p1.wrap(180, round(250))
        p1.wrapOn(can, w - 50, h - 10)

        p1.drawOn(can, 200 - w + 40, 250 - h - 70)


    can.save()

    # move to the beginning of the StringIO buffer
    packet.seek(0)

    # create a new PDF with Reportlab
    new_pdf = PdfReader(packet)
    # add the text (which is the new pdf) on the existing page
    page = existing_pdf.pages[0]
    page.merge_page(new_pdf.pages[0])
    # if available, add QR code
    if len(cardcontent) > 1 and cardcontent[1] != '':
        page = add_qr(cardcontent[1], page)
    # add front and back of card
    output.add_page(existing_pdf_back.pages[0])
    output.add_page(page)
    return output


existing_pdf_paths = ["Red back Final.pdf",
                      "Red front Final.pdf"]
output_stream = open("OpenTOScience_Red.pdf", "wb")
combined_pages = PdfWriter()
with open('CardContentRed.csv', newline='') as csvfile:
    cardreader = csv.reader(csvfile, delimiter=';')
    # This skips the first row of the CSV file.
    next(cardreader)
    for row in cardreader:
        combined_pages = add_text_to_pdf(existing_pdf_paths, row, combined_pages)
    combined_pages.write(output_stream)
    output_stream.close()

existing_pdf_paths = ["White back Final.pdf",
                      "White front Final.pdf"]
output_stream = open("OpenTOScience_White.pdf", "wb")
combined_pages = PdfWriter()
with open('CardContentWhite.csv', newline='') as csvfile:
    cardreader = csv.reader(csvfile, delimiter=';')
    # This skips the first row of the CSV file.
    next(cardreader)
    for row in cardreader:
        combined_pages = add_text_to_pdf(existing_pdf_paths, row, combined_pages)
    combined_pages.write(output_stream)
    output_stream.close()

merger = PdfMerger()
pdfs = ["OpenTOScience_Red.pdf","OpenTOScience_White.pdf"]
for pdf in pdfs:
    merger.append(pdf)

merger.write("OpenTOScience.pdf")
merger.close()