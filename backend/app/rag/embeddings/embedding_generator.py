from app.rag.embeddings.embedding_model import get_embedding_model
def encode_texts(texts): return get_embedding_model().encode(texts,normalize_embeddings=True,show_progress_bar=False)
def encode_query(q): return encode_texts([q])[0]
