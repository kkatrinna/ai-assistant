import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
YANDEX_API_KEY = os.getenv('YANDEX_API_KEY')
YANDEX_FOLDER_ID = os.getenv('YANDEX_FOLDER_ID')

AI_PROVIDER = os.getenv('AI_PROVIDER', 'openai')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
YANDEX_MODEL = os.getenv('YANDEX_MODEL', 'general')

VOICE_RATE = int(os.getenv('VOICE_RATE', 150))
VOICE_VOLUME = float(os.getenv('VOICE_VOLUME', 1.0))
VOICE_GENDER = os.getenv('VOICE_GENDER', 'male')
ASSISTANT_NAME = os.getenv('ASSISTANT_NAME', 'Алиса')

RECOGNITION_LANGUAGE = os.getenv('RECOGNITION_LANGUAGE', 'ru-RU')
TIMEZONE = os.getenv('TIMEZONE', 'Europe/Moscow')

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / 'data'
CREDENTIALS_DIR = DATA_DIR / 'credentials'
TOKEN_PATH = DATA_DIR / 'token.pickle'
GOOGLE_CREDENTIALS_FILE = CREDENTIALS_DIR / 'google_credentials.json'

DATA_DIR.mkdir(exist_ok=True)
CREDENTIALS_DIR.mkdir(exist_ok=True)

GOOGLE_CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar']
GOOGLE_CALENDAR_ID = 'primary'


SYSTEM_PROMPT = f"""Ты - {ASSISTANT_NAME}, дружелюбный AI-ассистент. 
Твои возможности:
- Отвечать на вопросы пользователя
- Помогать с задачами
- Управлять календарем (создавать события, проверять расписание)
- Напоминать о важных делах

Отвечай кратко, по делу, но дружелюбно.
Используй русский язык.
"""