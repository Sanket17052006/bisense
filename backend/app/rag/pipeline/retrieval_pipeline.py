from app.rag.database.index_manager import get_hybrid_search
def retrieve(query,top_k=6,doc_type=None):
 s=get_hybrid_search()
 if not s:return []
 out=[]
 for x in s.search(query,top_k):
  d=dict(x['metadata']);
  if doc_type and d.get('doc_type')!=doc_type: continue
  d['score']=x.get('rerank_score',x.get('score',0)); out.append(d)
 return out[:top_k]
