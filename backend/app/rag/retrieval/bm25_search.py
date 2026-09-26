import re,pickle
def tok(x): return re.findall(r'\w+',x.lower())
class BM25Search:
 def __init__(self,index,docs): self.index=index; self.docs=docs
 @classmethod
 def load(cls,path):
  x=pickle.load(open(path,'rb')); return cls(x['index'],x['documents'])
 def search(self,q,k=20):
  if not self.docs:return []
  scores=self.index.get_scores(tok(q)); ids=sorted(range(len(scores)),key=lambda i:scores[i],reverse=True)[:k]; return [{'metadata':self.docs[i],'score':float(scores[i])} for i in ids]
