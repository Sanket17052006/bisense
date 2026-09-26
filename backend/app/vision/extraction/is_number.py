import re
def extract_is_numbers(text): return sorted(set(re.findall(r'\b(?:BIS\s+)?IS\s*[:#-]?\s*(\d{3,6}(?:[-/]\d+)?)\b',text,re.I)))
