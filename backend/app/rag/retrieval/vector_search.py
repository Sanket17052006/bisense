import faiss,numpy as np,pickle
class VectorSearch:
 def __init__(self,index,meta): self.index=index; self.meta=meta
 @classmethod
 def load(cls,ip,mp): return cls(faiss.read_index(ip),pickle.load(open(mp,'rb')))
 def search(self,q,k=20):
  if not self.index.ntotal:return []
  s,i=self.index.search(np.asarray([q],dtype='float32'),min(k,self.index.ntotal)); return [{'metadata':self.meta[j],'score':float(sc)} for sc,j in zip(s[0],i[0]) if j>=0]
