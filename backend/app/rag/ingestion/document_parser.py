from app.rag.ingestion.csv_loader import load_csv_directory
from app.rag.ingestion.pdf_loader import load_pdf_directory
def load_all_documents(raw_dir,documents_dir): return load_csv_directory(raw_dir)+load_pdf_directory(documents_dir)
