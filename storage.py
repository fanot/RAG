from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter


class VectorStorage:
    """
    A class that represents a vector storage for chatbot data.
    
    Attributes:
        embeddings (OpenAIEmbeddings): An instance of OpenAIEmbeddings for generating embeddings.
        splitter (RecursiveCharacterTextSplitter): An instance of RecursiveCharacterTextSplitter for splitting text into chunks.
        vectors (dict): A dictionary to store the vectors for each user.

    Methods:
        new_storage(username: str, text: str) -> None:
            Creates a new vector storage for the given username and text.

        retrieve(username: str, query: str, top_k: int):
            Retrieves the most similar documents to the given query for the specified username.

        reset(username: str) -> None:
            Resets the vector storage for the specified username.
    """

    def __init__(self, api_key: str) -> None:
        """
        The constructor for VectorStorage class.

        Args:
            api_key (str): The API key for OpenAI API.

        """
        self.embeddings = OpenAIEmbeddings(api_key=api_key)
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        self.vectors = {}

    def new_storage(self, username: str, text: str) -> None:
        """
        Creates a new vector storage for the given username and text.

        Args:
            username (str): The username of the user.
            text (str): The text to be stored.

        Returns:
            None
        """
        texts = self.splitter.split_text(text)
        self.vectors[username] = FAISS.from_texts(texts, self.embeddings)

    def retrieve(self, username: str, query: str, top_k: int):
        """
        Retrieves the most similar documents to the given query for the specified username.

        Args:
            username (str): The username of the user.
            query (str): The query to search for.
            top_k (int): The number of top documents to retrieve.

        Returns:
            str: The concatenated page content of the retrieved documents.
        """
        if username not in self.vectors:
            return None
        docs = self.vectors[username].similarity_search(query, top_k=top_k)
        return " ".join([d.page_content for d in docs])

    def reset(self, username: str) -> None:
        """
        Resets the vector storage for the specified username.

        Args:
            username (str): The username of the user.

        Returns:
            None
        """
        if username in self.vectors:
            del self.vectors[username]