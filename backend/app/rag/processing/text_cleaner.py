import re
def clean_text(text): return re.sub(r'\n{3,}','\n\n',re.sub(r'[ \t]+',' ',str(text).replace('\x00',' '))).strip()
