from pathlib import Path
import pandas as pd
def read_csv_robust(path):
 for enc in ['utf-8','utf-8-sig','cp1252','latin1']:
  try:return pd.read_csv(path,encoding=enc,on_bad_lines='skip')
  except Exception:pass
 raise ValueError(f'Cannot read {path}')
def load_csv_directory(directory):
 docs=[]
 for p in sorted(Path(directory).glob('*.csv')):
  try:
   df=read_csv_robust(p).fillna('')
   for i,row in df.iterrows():
    text='\n'.join(f'{c}: {v}' for c,v in row.items() if str(v).strip())
    if text: docs.append({'id':f'{p.stem}-{i}','source':p.name,'doc_type':p.stem.lower(),'row':int(i),'text':text})
  except Exception as e: print('[CSV]',p,e)
 return docs
