from pathlib import Path
import faiss,pickle,numpy as np
def build_faiss_index(docs,embeddings,out):
 Path(out).mkdir(parents=True,exist_ok=True); a=np.asarray(embeddings,dtype='float32'); idx=faiss.IndexFlatIP(a.shape[1]); idx.add(a); faiss.write_index(idx,str(Path(out)/'index.faiss')); pickle.dump(docs,open(Path(out)/'index_metadata.pkl','wb'))
