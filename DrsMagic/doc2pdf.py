import glob
import os
import win32com.client

def doc_to_pdf(doc_path, pdf_path):
    word = win32com.client.Dispatch("Word.Application")
    word.Visible = False
    doc = word.Documents.Open(os.path.abspath(doc_path))
    doc.SaveAs(os.path.abspath(pdf_path), FileFormat=17)  # 17 = wdFormatPDF
    doc.Close()
    word.Quit()

input_folder = r'Attachments'
doc_files = glob.glob(os.path.join(input_folder, '*.doc'))
for doc_file in doc_files:
    pdf_file = os.path.splitext(doc_file)[0] + '.pdf'
    doc_to_pdf(doc_file, pdf_file)
