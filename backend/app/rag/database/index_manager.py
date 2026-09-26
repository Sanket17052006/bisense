from pathlib import Path
from app.core.config import get_settings
from app.rag.retrieval.vector_search import VectorSearch
from app.rag.retrieval.bm25_search import BM25Search
from app.rag.retrieval.hybrid_search import HybridSearch
def get_hybrid_search():
 s=get_settings(); f=Path(s.vector_db_dir)/'faiss'; b=Path(s.vector_db_dir)/'bm25/bm25_index.pkl'
 if not (f/'index.faiss').exists() or not (f/'index_metadata.pkl').exists() or not b.exists(): return None
 return HybridSearch(VectorSearch.load(str(f/'index.faiss'),str(f/'index_metadata.pkl')),BM25Search.load(str(b)))
