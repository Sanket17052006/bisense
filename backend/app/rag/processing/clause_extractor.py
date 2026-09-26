import re
def extract_clauses(text): return [{'clause':m.group(1),'title':m.group(2)} for m in re.finditer(r'(?im)^\s*((?:\d+\.)+\d*)\s*[:.-]?\s*(.+)$',text)]
