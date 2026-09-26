import re
def extract_licence_numbers(text): return sorted(set(re.findall(r'\b(?:LICENCE|LICENSE|LIC|CML)\s*(?:NO|NUMBER)?\s*[:#-]?\s*([A-Z0-9./-]{4,})',text,re.I)))
