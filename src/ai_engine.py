import openai
import requests
import json
from typing import List, Dict, Optional
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.config import (
        OPENAI_API_KEY, OPENAI_MODEL,
        YANDEX_API_KEY, YANDEX_FOLDER_ID, YANDEX_MODEL,
        AI_PROVIDER, SYSTEM_PROMPT
    )
except ImportError:
    try:
        from config import (
            OPENAI_API_KEY, OPENAI_MODEL,
            YANDEX_API_KEY, YANDEX_FOLDER_ID, YANDEX_MODEL,
            AI_PROVIDER, SYSTEM_PROMPT
        )
    except ImportError:
        OPENAI_API_KEY = None
        OPENAI_MODEL = "gpt-3.5-turbo"
        YANDEX_API_KEY = None
        YANDEX_FOLDER_ID = None
        YANDEX_MODEL = "general"
        AI_PROVIDER = "openai"
        SYSTEM_PROMPT = "Ты - дружелюбный AI-ассистент. Отвечай кратко и по делу."


class AIEngine:
    """Класс для работы с AI API"""

    def __init__(self):
        self.provider = AI_PROVIDER
        self.conversation_history = []
        self.max_history = 10

        if self.provider == 'openai' and OPENAI_API_KEY:
            self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
        else:
            self.client = None

    def add_to_history(self, role: str, content: str):
        """Добавление сообщения в историю"""
        self.conversation_history.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })

        if len(self.conversation_history) > self.max_history * 2:
            self.conversation_history = self.conversation_history[-self.max_history * 2:]

    def clear_history(self):
        """Очистка истории"""
        self.conversation_history = []

    def get_response(self, user_input: str, context: Optional[Dict] = None) -> str:
        """Получение ответа от AI"""

        self.add_to_history('user', user_input)

        if self.provider == 'openai' and OPENAI_API_KEY and self.client:
            return self._get_openai_response(user_input, context)
        elif self.provider == 'yandex' and YANDEX_API_KEY and YANDEX_FOLDER_ID:
            return self._get_yandex_response(user_input, context)
        else:
            return self._get_fallback_response(user_input)

    def _get_openai_response(self, user_input: str, context: Optional[Dict] = None) -> str:
        """Получение ответа от OpenAI GPT"""
        try:
            messages = [{'role': 'system', 'content': SYSTEM_PROMPT}]

            for msg in self.conversation_history[-6:]:
                messages.append({
                    'role': msg['role'],
                    'content': msg['content']
                })

            if context:
                context_text = f"\nТекущее время: {context.get('current_time', 'неизвестно')}"
                if context.get('upcoming_events'):
                    context_text += "\nПредстоящие события:\n"
                    for event in context['upcoming_events'][:3]:
                        context_text += f"- {event}\n"
                messages.append({'role': 'system', 'content': context_text})

            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=500
            )

            ai_response = response.choices[0].message.content

            self.add_to_history('assistant', ai_response)

            return ai_response

        except Exception as e:
            print(f"❌ OpenAI API error: {e}")
            return self._get_fallback_response(user_input)

    def _get_yandex_response(self, user_input: str, context: Optional[Dict] = None) -> str:
        """Получение ответа от YandexGPT"""
        try:
            prompt = f"{SYSTEM_PROMPT}\n\n"

            if context:
                prompt += f"Контекст: {json.dumps(context, ensure_ascii=False)}\n\n"

            for msg in self.conversation_history[-6:]:
                prompt += f"{msg['role']}: {msg['content']}\n"

            prompt += f"user: {user_input}\n"
            prompt += "assistant: "

            response = requests.post(
                "https://llm.api.cloud.yandex.net/llm/v1/completion",
                headers={
                    "Authorization": f"Api-Key {YANDEX_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": YANDEX_MODEL,
                    "instruction_text": prompt,
                    "max_tokens": 500,
                    "temperature": 0.7
                }
            )

            if response.status_code == 200:
                ai_response = response.json()['result']['alternatives'][0]['text']
                self.add_to_history('assistant', ai_response)
                return ai_response
            else:
                print(f"❌ YandexGPT API error: {response.status_code}")
                return self._get_fallback_response(user_input)

        except Exception as e:
            print(f"❌ YandexGPT API error: {e}")
            return self._get_fallback_response(user_input)

    def _get_fallback_response(self, user_input: str) -> str:
        """Запасной вариант ответа без API"""
        user_input_lower = user_input.lower()

        # Простые ответы на частые вопросы
        if 'привет' in user_input_lower:
            return 'Здравствуйте! Чем могу помочь?'
        elif 'как дела' in user_input_lower:
            return 'У меня всё отлично, спасибо!'
        elif 'спасибо' in user_input_lower:
            return 'Пожалуйста! Рад помочь.'
        elif 'пока' in user_input_lower:
            return 'До свидания!'
        elif 'как тебя зовут' in user_input_lower:
            return 'Меня зовут Алиса, я ваш голосовой ассистент.'
        elif 'что ты умеешь' in user_input_lower:
            return 'Я умею показывать события календаря, сообщать время и дату, открывать сайты и отвечать на вопросы.'
        else:
            return "Извините, я сейчас работаю в автономном режиме. Пожалуйста, настройте API ключи для полного функционала."


ai_engine = AIEngine()