import re
def extract_mrp(text):
 m=re.search(r'\bMRP\s*[:#-]?\s*(?:₹|RS\.?|INR)?\s*([0-9]+(?:\.[0-9]+)?)',text,re.I); return m.group(1) if m else None
