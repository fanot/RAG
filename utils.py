from PyPDF2 import PdfReader


def get_pdf_text(pdf):
    text = ""
    pdf_reader = PdfReader(pdf)
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def decode_text(file_data):
    encodings = ['utf-8', 'windows-1251', 'iso-8859-5', 'latin-1', 'utf-16']
    for encoding in encodings:
        try:
            return file_data.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("Could not decode the file with any of the standard encodings.")
