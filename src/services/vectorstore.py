"""
Vector store service for AstraDB.
Handles embedding, storage, and retrieval of documents.
"""

import logging
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_astradb import AstraDBVectorStore
from langchain_core.documents import Document
from src.config import settings

logger = logging.getLogger(__name__)


def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    return GoogleGenerativeAIEmbeddings(model=settings.EMBEDDING_MODEL)


def connect() -> AstraDBVectorStore:
    """Create a fresh connection to AstraDB."""
    return AstraDBVectorStore(
        embedding=get_embeddings(),
        collection_name=settings.ASTRA_COLLECTION_NAME,
        api_endpoint=settings.ASTRA_DB_API_ENDPOINT,
        token=settings.ASTRA_DB_APPLICATION_TOKEN,
        namespace=settings.astra_namespace,
    )


def load_documents(docs: list[Document]) -> AstraDBVectorStore:
    """
    Clear existing data and load new documents into the vector store.
    Returns a fresh vstore connection after loading.
    """
    vstore = connect()

    try:
        vstore.delete_collection()
        logger.info("Cleared existing collection")
    except Exception as e:
        logger.debug(f"Collection clear (normal on first run): {e}")

    vstore = connect()
    vstore.add_documents(docs)
    logger.info(f"Loaded {len(docs)} documents into vector store")

    return vstore


def get_retriever(vstore: AstraDBVectorStore, k: int = 5):
    """Create a retriever from the vector store."""
    return vstore.as_retriever(search_kwargs={"k": k})
