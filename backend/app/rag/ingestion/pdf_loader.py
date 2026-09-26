from pathlib import Path
def load_pdf_directory(directory):
 import fitz
 docs=[]
 for p in Path(directory).rglob('*.pdf'):
  try:
   pdf=fitz.open(p)
   for n,page in enumerate(pdf,1):
    text=page.get_text('text').strip()
    if text: docs.append({'id':f'{p.stem}-{n}','source':p.name,'doc_type':p.parent.name,'page':n,'text':text})
   pdf.close()
  except Exception as e: print('[PDF]',p,e)
 return docs
