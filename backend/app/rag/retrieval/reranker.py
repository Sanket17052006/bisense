from functools import lru_cache
from app.core.config import get_settings
@lru_cache
def model():
 if not get_settings().enable_reranker:return None
 try:
  from sentence_transformers import CrossEncoder
  return CrossEncoder(get_settings().reranker_model)
 except Exception as e: print('[reranker]',e); return None
def rerank(query,items,k):
 m=model()
 if not m:return items[:k]
 scores=m.predict([(query,x['metadata'].get('text','')) for x in items])
 for x,s in zip(items,scores): x['rerank_score']=float(s)
 return sorted(items,key=lambda x:x.get('rerank_score',0),reverse=True)[:k]
