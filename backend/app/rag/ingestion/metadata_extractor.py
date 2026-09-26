import re
def extract_metadata(doc): return {'source':doc.get('source',''),'doc_type':doc.get('doc_type',''),'page':doc.get('page'),'is_numbers':sorted(set(re.findall(r'\bIS\s*[:#-]?\s*(\d{3,6}(?:[-/]\d+)?)\b',doc.get('text',''),re.I)))}
