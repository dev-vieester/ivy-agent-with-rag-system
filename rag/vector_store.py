import os
import chromadb
import uuid
from typing import List, Any
import numpy as np

class VectorStore:
    """Manages document embeddings in a ChromaDB vector store"""
    def __init__(self, collection_name : str, persist_directory : str ):
        """
                Initialize the vector store
                Args:
                    collection_name: Name of the ChromaDB collection
                    persist_directory: Directory to persist the vector store
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None

    def _initialize_store(self):
        """Initialize ChromaDB client and collection"""
        try:
            os.makedirs(self.persist_directory, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={
                    "description": "File document embeddings for RAG",
                    "hnsw:space": "cosine"
                }
            )
            print(f"Vector store initialized. Collection: {self.collection_name}")
            print(f"Existing documents in collection: {self.collection.count()}")
        except Exception as e:
            print(f"Error initializing vector store: {e}")
            raise

    def reset_collection(self):
        """Delete and recreate the collection (useful when changing distance metric)"""
        self.client.delete_collection(self.collection_name)
        self._initialize_store()
        print(f"Collection '{self.collection_name}' has been reset")

    def add_documents(self, documents: List[Any], embeddings: np.ndarray):
        if len(documents) != len(embeddings):
            raise ValueError("Number of documents must match number of embeddings")

        print(f"Adding {len(documents)} documents to vector store...")

        ids = []
        metadatas = []
        documents_text = []
        embeddings_list = []

        for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
            doc_id = f"doc_{uuid.uuid4().hex[:8]}_{i}"
            ids.append(doc_id)

            metadata = dict(doc.metadata)
            metadata['doc_index'] = i
            metadata['content_length'] = len(doc.page_content)
            metadatas.append(metadata)

            documents_text.append(doc.page_content)
            emb = embedding.tolist() if hasattr(embedding, 'tolist') else embedding
            embeddings_list.append(emb)

        BATCH_SIZE = 5000
        total = len(ids)

        try:
            for start in range(0, total, BATCH_SIZE):
                end = min(start + BATCH_SIZE, total)
                self.collection.add(
                    ids=ids[start:end],
                    embeddings=embeddings_list[start:end],
                    metadatas=metadatas[start:end],
                    documents=documents_text[start:end],
                )
                print(f"  Inserted batch {start}–{end} ({end - start} docs)")

            print(f"Successfully added {total} documents to vector store")
            print(f"Total documents in collection: {self.collection.count()}")
        except Exception as e:
            print(f"Error adding documents to vector store: {e}")
            raise