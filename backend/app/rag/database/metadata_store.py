import json
def save_metadata(docs,path): json.dump(docs,open(path,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
def load_metadata(path): return json.load(open(path,encoding='utf-8'))
