# Replace old imports with new ones from langchain-community and langchain-openai
import time
from langchain_community.chat_models import ChatOpenAI
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage


class GPT:
    """
    Represents a chatbot that uses the OpenAI chat model GPT-4.

    Attributes:
        messages (dict): A dictionary to store the messages for each user.
        chat (ChatOpenAI): An instance of ChatOpenAI for generating responses.
        retry_delay (float): Initial delay in seconds for retrying after a rate limit error.

    Methods:
        new_rag(username: str, rag_content: str) -> None:
            Creates a new RAG (Retrieval-Augmented Generation) conversation.

        ask(username: str, query: str) -> str:
            Sends a query to the chat model and returns the response, handling retries on rate limit errors.

        reset(username: str) -> None:
            Resets the conversation for a given username.
    """

    def __init__(self, api_key: str, retry_delay: float = 1.0) -> None:
        """
        Initializes a ChatGPT 4 instance.

        Args:
            api_key (str): The API key for accessing the OpenAI chat model.
            retry_delay (float): Initial delay for retries after rate limiting, in seconds.
        """
        self.messages = {}
        self.chat = ChatOpenAI(openai_api_key=api_key, model='gpt-4o')
        self.retry_delay = retry_delay

    def new_rag(self, username: str, rag_content: str) -> None:
        self.messages[username] = [
            SystemMessage(content="You are a helpful assistant. Your name is Ragoût."),
            HumanMessage(content=make_rag(rag_content)),
            AIMessage(content="I understand. I will answer your questions based on this document.")
        ]

    def ask(self, username: str, query: str) -> str:
        if username not in self.messages:
            self.reset(username)
        self.messages[username].append(HumanMessage(content=query))
        try:
            res = self.chat(self.messages[username])
        except Exception as e:
            if "429" in str(e):
                time.sleep(self.retry_delay)  # Simple exponential backoff
                self.retry_delay *= 2
                return self.ask(username, query)
            raise e
        self.messages[username].append(res)
        return res.content

    def reset(self, username: str) -> None:
        self.messages[username] = [SystemMessage(content="You are a helpful assistant.")]
        self.retry_delay = 1.0  # Reset delay on a new conversation


def make_rag(rag_content: str) -> str:
    return f"""Следующий документ представляет собой документ, который я вам даю. Вам предстоит ответить на вопросы по этой документации. 

    Документ: {rag_content}

    На этом документ заканчивается. В следующих сообщениях я задам вам вопросы по этому документу. 
    Для ответа на вопрос используйте ТОЛЬКО фактическую информацию из стенограммы.
    Дайте цитату, где это написано.
    Если вы чувствуете, что у вас недостаточно информации для ответа на вопрос, скажите: «Я не знаю».
    Ваши ответы должны быть многословными и подробными. Вы понимаете?"""
