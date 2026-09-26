from app.rag.embeddings.embedding_generator import encode_query
from app.rag.retrieval.reranker import rerank
class HybridSearch:
 def __init__(self,v,b): self.v=v; self.b=b
 def search(self,q,k=6):
  a=self.v.search(encode_query(q),20); b=self.b.search(q,20); m={}
  for x in a:m.setdefault(x['metadata'].get('chunk_id',x['metadata'].get('id')),dict(x['metadata']))['v']=x['score']
  mx=max([x['score'] for x in b] or [1])
  for x in b:m.setdefault(x['metadata'].get('chunk_id',x['metadata'].get('id')),dict(x['metadata']))['b']=x['score']/max(mx,1e-9)
  c=[]
  for x in m.values(): x['hybrid_score']=.65*x.get('v',0)+.35*x.get('b',0); c.append({'metadata':x,'score':x['hybrid_score']})
  return rerank(q,sorted(c,key=lambda x:x['score'],reverse=True)[:30],k)
