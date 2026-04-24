import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from src.core.config import settings
import asyncio

class VectorStore:
    def __init__(self):
        self.client = chromadb.HttpClient(
            host=settings.CHROMA_URL.split("://")[1].split(":")[0], 
            port=settings.CHROMA_URL.split(":")[2] if len(settings.CHROMA_URL.split(":")) > 2 else "8000"
        )
        # Using the requested model locally with huggingface
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
    def _get_collection_name(self, doc_id: str) -> str:
        return f"doc_{str(doc_id).replace('-', '_')}"

    async def create_collection(self, doc_id: str, custom_collection_id: str = None):
        loop = asyncio.get_event_loop()
        collection_name = custom_collection_id if custom_collection_id else self._get_collection_name(doc_id)
        
        def _create():
            return self.client.get_or_create_collection(
                name=collection_name, 
                embedding_function=self.embedding_fn
            )
            
        await loop.run_in_executor(None, _create)

    async def add_chunks(self, doc_id: str, chunks: list[str], metadatas: list[dict], custom_collection_id: str = None):
        loop = asyncio.get_event_loop()
        collection_name = custom_collection_id if custom_collection_id else self._get_collection_name(doc_id)
        
        def _add():
            collection = self.client.get_collection(
                name=collection_name, 
                embedding_function=self.embedding_fn
            )
            batch_size = 32
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i:i + batch_size]
                batch_metas = metadatas[i:i + batch_size]
                # To prevent chunk ID collision in session caches, include timestamp or uuid natively,
                # but for simplicity we rely on sequence.
                import uuid
                batch_ids = [f"chunk_{uuid.uuid4()}" for _ in range(len(batch_chunks))]
                
                collection.add(
                    documents=batch_chunks,
                    metadatas=batch_metas,
                    ids=batch_ids
                )
        await loop.run_in_executor(None, _add)

    async def similarity_search(self, doc_id: str, query: str, k: int = 5, custom_collection_id: str = None) -> list[dict]:
        loop = asyncio.get_event_loop()
        collection_name = custom_collection_id if custom_collection_id else self._get_collection_name(doc_id)
        
        def _search():
            try:
                collection = self.client.get_collection(
                    name=collection_name, 
                    embedding_function=self.embedding_fn
                )
                results = collection.query(
                    query_texts=[query],
                    n_results=k
                )
                
                docs = []
                if results['documents'] and results['documents'][0]:
                    for doc, meta, score in zip(results['documents'][0], results['metadatas'][0], results['distances'][0]):
                        docs.append({
                            "content": doc,
                            "metadata": meta,
                            "score": score
                        })
                return docs
            except Exception:
                return [] # Collection might not exist
            
        return await loop.run_in_executor(None, _search)

    async def delete_collection(self, doc_id: str):
        loop = asyncio.get_event_loop()
        collection_name = self._get_collection_name(doc_id)
        
        def _delete():
            try:
                self.client.delete_collection(name=collection_name)
            except Exception:
                pass # collection might not exist
                
        await loop.run_in_executor(None, _delete)

vector_store = VectorStore()
