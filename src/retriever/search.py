from src.utils.qdrant_utils import search
from src.embedder.embed_clips import embed_query
from src.config import QDRANT_COLLECTION_NAME

def fetch_relevant_documents(query: str, num_result: int = 5):
  query_vector = embed_query(query)
  rel_docs = search(QDRANT_COLLECTION_NAME, query_vector, num_result)
  return rel_docs

