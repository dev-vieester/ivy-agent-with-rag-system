from typing import List
import numpy as np
import os

SUPPORTED_PROVIDERS = ("gemini", "sentence_transformer")

class EmbeddingManager:
    """Handles document embedding generation — supports Gemini and SentenceTransformer"""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        provider: str = "sentence_transformer",  # "gemini" or "sentence_transformer"
    ):
        if provider not in SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported provider '{provider}'. Choose from: {SUPPORTED_PROVIDERS}")

        self.model_name = model_name
        self.provider = provider
        self.model = None
        self._load_model()

    def _load_model(self):
        """Load the appropriate embedding model based on provider"""
        try:
            print(f"Loading [{self.provider}] embedding model: {self.model_name}")

            if self.provider == "sentence_transformer":
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(self.model_name)
                dim = self.model.get_sentence_embedding_dimension()
                print(f"Model loaded successfully. Embedding dimension: {dim}")

            elif self.provider == "gemini":
                from langchain_google_genai import GoogleGenerativeAIEmbeddings
                api_key = os.getenv("GOOGLE_API_KEY")
                if not api_key:
                    raise ValueError("GOOGLE_API_KEY not found. Check your .env file.")
                self.model = GoogleGenerativeAIEmbeddings(
                    model=self.model_name,
                    google_api_key=api_key,
                )
                print("Gemini embedding model loaded successfully.")

        except Exception as e:
            print(f"Error loading model '{self.model_name}': {e}")
            raise

    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for a list of texts.
        Always returns a numpy array regardless of provider.
        """
        if self.model is None:
            raise ValueError("Model not loaded.")

        print(f"Generating embeddings for {len(texts)} texts...")

        if self.provider == "sentence_transformer":
            embeddings = self.model.encode(texts, show_progress_bar=True)
            # already numpy array

        elif self.provider == "gemini":
            raw = self.model.embed_documents(texts)
            embeddings = np.array(raw, dtype=np.float32)

        print(f"Generated embeddings with shape: {embeddings.shape}")
        return embeddings