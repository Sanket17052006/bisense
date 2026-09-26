from app.rag.pipeline.retrieval_pipeline import retrieve
def retrieve_requirements(info):
 qs=[f"{x} BIS requirements" for x in info.get('is_numbers',[])]; qs += [f"{info['product_type']} BIS requirements"] if info.get('product_type')!='unknown' else []
 out=[]; seen=set()
 for q in qs:
  for x in retrieve(q,4):
   k=x.get('chunk_id',x.get('id'));
   if k not in seen: seen.add(k); out.append(x)
 return out
