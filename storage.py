import logging
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct


class VectorStorage:
    """
    A class that represents a vector storage for chatbot data using Qdrant.

    Attributes:
        embeddings (OpenAIEmbeddings): An instance of OpenAIEmbeddings for generating embeddings.
        splitter (RecursiveCharacterTextSplitter): An instance of RecursiveCharacterTextSplitter for splitting text into chunks.
        qdrant_client (QdrantClient): A client for interacting with the Qdrant service.
        collection_name (str): Name of the collection in Qdrant where vectors are stored.

    Methods:
        new_storage(username: str, text: str) -> None:
            Creates a new vector storage for the given username and text.

        retrieve(username: str, query: str, top_k: int):
            Retrieves the most similar documents to the given query for the specified username.

        reset(username: str) -> None:
            Resets the vector storage for the specified username.
    """

    def __init__(self, api_key: str, qdrant_host: str = 'localhost', qdrant_port: int = 6333) -> None:
        self.embeddings = OpenAIEmbeddings(api_key=api_key)
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        self.qdrant_client = QdrantClient(host=qdrant_host, port=qdrant_port)
        self.collection_name = 'chatbot_vectors'

    def new_storage(self, username: str, text: str) -> None:
        texts = self.splitter.split_text(text)
        embeddings = self.embeddings.embed_documents(texts)
        points = [PointStruct(id=i, vector=embedding.tolist(), payload={"text": text}) for i, (embedding, text) in
                  enumerate(zip(embeddings, texts))]
        self.qdrant_client.upsert(collection_name=self.collection_name, points=points)

    def retrieve(self, username: str, query: str, top_k: int):
        query_embedding = self.embeddings.embed_query(query)
        search_result = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding.tolist(),
            limit=top_k
        )
        if not search_result:
            return None
        documents = [doc.payload['text'] for doc in search_result]
        logging.info(f"Retrieved {len(documents)} documents for user {username} using query '{query}'")
        return " ".join(documents)

    def reset(self, username: str) -> None:
        # Ищем все точки для данного пользователя
        filter_params = {
            "must": [
                {"key": "username", "match": {"value": username}}
            ]
        }
        # Удаление точек, соответствующих фильтру
        self.qdrant_client.delete_points(collection_name=self.collection_name, filter=filter_params)

