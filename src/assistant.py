import threading
import time
from datetime import datetime
from queue import Queue
from typing import Optional
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.voice import voice
    from src.ai_engine import ai_engine
    from src.calendar_integration import calendar
    from src.commands import CommandHandler
    from src.config import ASSISTANT_NAME
except ImportError:
    try:
        from voice import voice
        from ai_engine import ai_engine
        from calendar_integration import calendar
        from commands import CommandHandler
        from config import ASSISTANT_NAME
    except ImportError:
        ASSISTANT_NAME = 'Алиса'
        from voice import voice
        from ai_engine import ai_engine
        from calendar_integration import calendar
        from commands import CommandHandler


class AIAssistant:
    """Главный класс AI-ассистента"""

    def __init__(self):
        self.name = ASSISTANT_NAME
        self.is_running = False
        self.listen_mode = 'once'

        self.voice = voice
        self.ai = ai_engine
        self.calendar = calendar

        self.command_handler = CommandHandler(self.ai, self.calendar, self.voice)

        self.command_queue = Queue()

        print(f"\n{'=' * 50}")
        print(f"🤖 {self.name} AI-ассистент запущен!")
        print(f"{'=' * 50}\n")

    def start(self):
        """Запуск ассистента"""
        self.is_running = True

        self.greet()

        while self.is_running:
            try:
                if self.listen_mode == 'once':
                    self._listen_once_mode()
                else:
                    self._listen_continuous_mode()

            except KeyboardInterrupt:
                self.stop()
                break
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                time.sleep(1)

    def _listen_once_mode(self):
        """Режим однократного прослушивания"""
        command = self.voice.listen_once(timeout=5)

        if command:
            result = self.command_handler.process_command(command)
            if result.get('speak', True):
                self.voice.speak(result['response'])
            else:
                print(f"\n🤖 {self.name}: {result['response']}\n")

            if result.get('action') == 'exit':
                self.stop()
        else:
            time.sleep(1)

    def _listen_continuous_mode(self):
        """Режим непрерывного прослушивания"""

        def on_command(text):
            result = self.command_handler.process_command(text)

            if result.get('speak', True):
                self.voice.speak(result['response'])
            else:
                print(f"\n🤖 {self.name}: {result['response']}\n")

            if result.get('action') == 'exit':
                self.stop()

        self.voice.start_listening(on_command)

        while self.is_running and self.listen_mode == 'continuous':
            time.sleep(0.1)

    def greet(self):
        """Приветствие"""
        hour = datetime.now().hour

        if hour < 6:
            greeting = "Доброй ночи"
        elif hour < 12:
            greeting = "Доброе утро"
        elif hour < 18:
            greeting = "Добрый день"
        else:
            greeting = "Добрый вечер"

        welcome = f"{greeting}! Я {self.name}, ваш голосовой ассистент. Чем могу помочь?"

        self.voice.speak(welcome)

        # Показываем подсказку
        print(f"\n💡 Скажите 'помощь' чтобы узнать мои возможности")
        print(f"   Скажите 'пока' для выхода\n")

    def stop(self):
        """Остановка ассистента"""
        self.is_running = False
        self.voice.stop_listening()
        print("\n👋 Ассистент остановлен")

    def set_listen_mode(self, mode: str):
        """Установка режима прослушивания"""
        if mode in ['once', 'continuous']:
            self.listen_mode = mode
            print(f"🎤 Режим прослушивания: {'однократный' if mode == 'once' else 'непрерывный'}")


def main():
    """Главная функция запуска"""
    assistant = AIAssistant()

    try:
        assistant.start()
    except KeyboardInterrupt:
        assistant.stop()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        assistant.stop()


if __name__ == "__main__":
    main()