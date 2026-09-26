def generate_citations(results): return [{'source':r.get('source'),'page':r.get('page'),'chunk_id':r.get('chunk_id'),'score':r.get('score')} for r in results]
