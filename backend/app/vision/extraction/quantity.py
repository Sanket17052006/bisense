import re
def extract_quantity(text): return [f'{v} {u}' for v,u in re.findall(r'\b(\d+(?:\.\d+)?)\s*(kg|g|mg|l|ml|pcs?|pieces?)\b',text,re.I)]
