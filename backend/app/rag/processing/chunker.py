def chunk_text(text,size=800,overlap=120):
 text=text.strip(); out=[]; start=0
 while start<len(text):
  end=min(len(text),start+size); out.append(text[start:end])
  if end==len(text): break
  start=end-overlap
 return out
def chunk_documents(docs,size=800,overlap=120):
 out=[]
 for d in docs:
  for i,t in enumerate(chunk_text(d['text'],size,overlap)):
   x=dict(d); x['text']=t; x['chunk_id']=f"{d['id']}-chunk-{i}"; out.append(x)
 return out
