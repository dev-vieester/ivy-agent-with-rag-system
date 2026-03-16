from dotenv import load_dotenv
load_dotenv()

from rag.rag_retriever import RagRetriever
from rag.embedding_manager import EmbeddingManager
from rag.vector_store import VectorStore
from rag.retrieve_document import process_documents
from rag.split_documents import split_documents
from typing import List, Dict, Any


class RetrievalAgent:
    """Agent that handles document ingestion and retrieval via RAG"""

    def __init__(
        self,
        collection_name: str = "file_documents",
        persist_directory: str = "data/vector_store",
        embedding_model: str = "all-MiniLM-L6-v2",
        embedding_provider: str = "sentence_transformer",  # or "gemini"
    ):
        self.embedding_manager = EmbeddingManager(
            model_name=embedding_model,
            provider=embedding_provider,
        )

        self.vector_store = VectorStore(
            collection_name=collection_name,
            persist_directory=persist_directory,
        )
        self.vector_store._initialize_store()

        self.retriever = RagRetriever(
            vector_store=self.vector_store,
            embedding_manager=self.embedding_manager,
        )

    def ingest(
        self,
        pdf_directory: str = "data/pdf_files",
        doc_directory: str = "data/doc_files",
        csv_directory: str = "data/csv_files",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ):
        raw_docs = process_documents(pdf_directory, doc_directory, csv_directory)
        if not raw_docs:
            print("No documents found to ingest.")
            return

        chunks = split_documents(raw_docs, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        texts = [chunk.page_content for chunk in chunks]
        embeddings = self.embedding_manager.generate_embeddings(texts)
        self.vector_store.add_documents(chunks, embeddings)
        print(f"Ingestion complete. {len(chunks)} chunks stored.")

    def retrieve(self, query: str, top_k: int = 5, score_threshold: float = 0.7) -> List[Dict[str, Any]]:
        return self.retriever.retrieve(query, top_k=top_k, score_threshold=score_threshold)