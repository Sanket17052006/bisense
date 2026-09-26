import re
def extract_manufacturer(text):
 m=re.search(r'(?:MANUFACTURED\s+BY|MANUFACTURER|MFG\.?\s+BY)\s*[:#-]?\s*(.+)',text,re.I); return m.group(1).split('\n')[0].strip() if m else None
