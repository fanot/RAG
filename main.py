import io
import os
import logging
import telebot
from utils import get_pdf_text, decode_text
from gpt import GPT
from storage import VectorStorage
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize the bot and other components
BOT_API_KEY = os.getenv('BOT_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

bot = telebot.TeleBot(BOT_API_KEY)
chat = GPT(OPENAI_API_KEY)
storage = VectorStorage(OPENAI_API_KEY)

# Ensure that the keys are not None
if BOT_API_KEY is None or OPENAI_API_KEY is None:
    logging.error("API keys are not set. Please check your environment variables.")
    exit(1)  # Exit the script if the keys are not set

# Load "Master and Margarita" as the base document for all users
@retry(wait=wait_exponential(multiplier=1, max=60), stop=stop_after_attempt(5))
def initialize_storage_with_book():
    try:
        with open("book.pdf", "rb") as file:
            raw_text = get_pdf_text(file)
        storage.new_storage("book", raw_text)
    except Exception as e:
        logging.error(f"Error initializing book storage: {e}")

initialize_storage_with_book()

# Welcome message for /start command
@bot.message_handler(commands=['start'])
def send_welcome_message(message):
    bot.reply_to(message, "Привет! Я Раг. Для получения дополнительной информации введите /help. Вы можете начать с вопросов о 'Мастере и Маргарите'.")

# Help message content and handler
help_message = """
Вот что вы можете делать:
- Задать вопрос по книге "Мастер и маргарита".
- Отправьте мне PDF или TXT файл. Я обработаю его и сохраню для ваших личных запросов.
- Задавайте вопросы по отправленным документам.
- Используйте /select, чтобы выбрать один из ваших загруженных документов для запросов.
- Используйте /reset, чтобы удалить все ваши документы и сбросить наш разговор.
"""

@bot.message_handler(commands=['help'])
def send_help_message(message):
    bot.reply_to(message, help_message)

# Handle document uploads and initialize user storage
# Dictionary to track each user's documents
user_documents = {}


# Function to display available documents
def list_documents(user_id):
    docs = user_documents.get(user_id, {})
    return '\n'.join([f"{idx}: {doc}" for idx, doc in enumerate(docs.keys(), start=1)])


# Handle document uploads and store document metadata
@bot.message_handler(content_types=['document'])
def handle_document(message):
    user_id = str(message.from_user.id)
    file_info = bot.get_file(message.document.file_id)
    file_extension = file_info.file_path.split('.')[-1].lower()

    try:
        file_data = bot.download_file(file_info.file_path)
        filename = message.document.file_name
        raw_text = get_pdf_text(io.BytesIO(file_data)) if file_extension == 'pdf' else decode_text(file_data)
        doc_id = len(user_documents.get(user_id, {}))
        if user_id not in user_documents:
            user_documents[user_id] = {}
        user_documents[user_id][doc_id] = {'name': filename, 'text': raw_text}
        storage.new_storage(f"{user_id}_{doc_id}", raw_text)
        bot.reply_to(message,
                     f"Документ '{filename}' обработан! Используйте /select, чтобы выбрать документ для запросов.")
    except Exception as e:
        logging.error(f"Error processing document: {e}")
        bot.reply_to(message, "Не удалось обработать документ. Пожалуйста, убедитесь, что это действительный файл.")


# Command to list and select documents
@bot.message_handler(commands=['select'])
def select_document(message):
    user_id = str(message.from_user.id)
    if user_id not in user_documents or not user_documents[user_id]:
        bot.reply_to(message, "Нет загруженных документов. Пожалуйста, сначала загрузите документ.")
        return
    doc_list = list_documents(user_id)
    msg = f"Пожалуйста, выберите документ по номеру:\n{doc_list}"
    bot.reply_to(message, msg, parse_mode='Markdown')


# Handler to process document selection
@bot.message_handler(func=lambda message: message.text.isdigit())
def process_selection(message):
    user_id = str(message.from_user.id)
    doc_index = int(message.text) - 1
    if user_id in user_documents and doc_index in user_documents[user_id]:
        active_doc = user_documents[user_id][doc_index]
        bot.reply_to(message,
                     f"Вы выбрали '{active_doc['name']}'. Теперь вы можете задавать вопросы об этом документе.")
    else:
        bot.reply_to(message, "Неверный выбор. Используйте /select, чтобы посмотреть доступные документы.")


# Reset user data and storage
@bot.message_handler(commands=['reset'])
def reset_user_data(message):
    user_id = str(message.from_user.id)
    chat.reset(user_id)
    storage.reset(user_id)
    user_documents.pop(user_id, None)
    bot.reply_to(message, "Ваши данные были сброшены. Начните снова, загрузив новый документ.")


# Start the bot's polling
if __name__ == '__main__':
    bot.polling(non_stop=True)