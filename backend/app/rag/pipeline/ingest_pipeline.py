from pathlib import Path
import pickle
from rank_bm25 import BM25Okapi
from app.core.config import get_settings
from app.rag.ingestion.document_parser import load_all_documents
from app.rag.processing.document_normalizer import normalize_documents
from app.rag.processing.chunker import chunk_documents
from app.rag.embeddings.embedding_generator import encode_texts
from app.rag.database.vector_store import build_faiss_index
from app.rag.database.metadata_store import save_metadata
def ingest():
 s=get_settings(); docs=normalize_documents(load_all_documents(s.raw_data_dir,s.documents_dir)); chunks=chunk_documents(docs,s.chunk_size,s.chunk_overlap)
 if not chunks:return {'documents':0,'chunks':0}
 build_faiss_index(chunks,encode_texts([x['text'] for x in chunks]),str(Path(s.vector_db_dir)/'faiss'))
 bm=BM25Okapi([x['text'].lower().split() for x in chunks]); bd=Path(s.vector_db_dir)/'bm25'; bd.mkdir(parents=True,exist_ok=True); pickle.dump({'index':bm,'documents':chunks},open(bd/'bm25_index.pkl','wb'))
 Path(s.processed_data_dir,'metadata').mkdir(parents=True,exist_ok=True); save_metadata(chunks,str(Path(s.processed_data_dir)/'metadata/chunks.json'))
 return {'documents':len(docs),'chunks':len(chunks)}
