def extract_pdf_with_ocr(path):
 from vision.ocr.tesseract_ocr import ocr_image
 import fitz,tempfile,os
 out=[]; pdf=fitz.open(path)
 for n,page in enumerate(pdf,1):
  with tempfile.NamedTemporaryFile(suffix='.png',delete=False) as f: name=f.name
  page.get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False).save(name)
  try: out.append({'source':os.path.basename(path),'page':n,'text':ocr_image(name)})
  finally: os.unlink(name)
 pdf.close(); return out
