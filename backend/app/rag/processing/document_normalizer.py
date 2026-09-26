from app.rag.processing.text_cleaner import clean_text
from app.rag.processing.clause_extractor import extract_clauses
def normalize_documents(docs):
 out=[]
 for d in docs:
  x=dict(d); x['text']=clean_text(x.get('text','')); x['clauses']=extract_clauses(x['text'])
  if x['text']: out.append(x)
 return out
