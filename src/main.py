
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import argparse
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from src.assistant import AIAssistant, main as assistant_main


def check_dependencies():
    """Проверка наличия зависимостей"""
    missing = []

    try:
        import speech_recognition
    except ImportError:
        missing.append("SpeechRecognition")

    try:
        import pyttsx3
    except ImportError:
        missing.append("pyttsx3")

    try:
        import pyaudio
    except ImportError:
        missing.append("pyaudio")

    try:
        import openai
    except ImportError:
        missing.append("openai")

    try:
        import googleapiclient
    except ImportError:
        missing.append("google-api-python-client")

    if missing:
        print("\n" + "=" * 60)
        print("❌ ОТСУТСТВУЮТ ЗАВИСИМОСТИ")
        print("=" * 60)
        print(f"\nНе найдены библиотеки: {', '.join(missing)}")
        print("\n💡 Установите их командой:")
        print(f"\n   pip install {' '.join(missing)}")
        print("\n   или")
        print(f"\n   pip install -r requirements.txt")
        print("\n" + "=" * 60)
        return False

    return True


class AssistantGUI:
    """Графический интерфейс для ассистента"""

    def __init__(self, root):
        self.root = root
        self.root.title("🤖 AI-ассистент")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)

        self.assistant = None
        self.assistant_thread = None

        self.setup_ui()
        self.check_config()

    def setup_ui(self):
        """Настройка интерфейса"""
        # Основной контейнер
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        title_label = ttk.Label(
            main_frame,
            text="🤖 Голосовой AI-ассистент",
            font=("Helvetica", 18, "bold")
        )
        title_label.pack(pady=(0, 20))

        self.status_var = tk.StringVar(value="🟡 Готов к запуску")
        status_label = ttk.Label(
            main_frame,
            textvariable=self.status_var,
            font=("Helvetica", 10)
        )
        status_label.pack(pady=(0, 20))

        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=20)

        self.start_btn = ttk.Button(
            button_frame,
            text="🚀 Запустить ассистента",
            command=self.start_assistant,
            width=25
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(
            button_frame,
            text="⏹ Остановить",
            command=self.stop_assistant,
            state=tk.DISABLED,
            width=20
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        settings_frame = ttk.LabelFrame(main_frame, text="⚙️ Настройки", padding="15")
        settings_frame.pack(fill=tk.X, pady=20)

        listen_frame = ttk.Frame(settings_frame)
        listen_frame.pack(fill=tk.X, pady=5)

        ttk.Label(listen_frame, text="Режим прослушивания:").pack(side=tk.LEFT)

        self.listen_mode = tk.StringVar(value="once")
        ttk.Radiobutton(
            listen_frame,
            text="Однократный",
            variable=self.listen_mode,
            value="once"
        ).pack(side=tk.LEFT, padx=(20, 10))

        ttk.Radiobutton(
            listen_frame,
            text="Непрерывный",
            variable=self.listen_mode,
            value="continuous"
        ).pack(side=tk.LEFT)

        # AI провайдер
        ai_frame = ttk.Frame(settings_frame)
        ai_frame.pack(fill=tk.X, pady=5)

        ttk.Label(ai_frame, text="AI провайдер:").pack(side=tk.LEFT)

        self.ai_provider = tk.StringVar(value="openai")
        ttk.Radiobutton(
            ai_frame,
            text="OpenAI GPT",
            variable=self.ai_provider,
            value="openai"
        ).pack(side=tk.LEFT, padx=(20, 10))

        ttk.Radiobutton(
            ai_frame,
            text="YandexGPT",
            variable=self.ai_provider,
            value="yandex"
        ).pack(side=tk.LEFT)

        tts_frame = ttk.Frame(settings_frame)
        tts_frame.pack(fill=tk.X, pady=5)

        ttk.Label(tts_frame, text="Озвучка:").pack(side=tk.LEFT)

        self.tts_engine = tk.StringVar(value="pyttsx3")
        ttk.Radiobutton(
            tts_frame,
            text="pyttsx3 (офлайн)",
            variable=self.tts_engine,
            value="pyttsx3"
        ).pack(side=tk.LEFT, padx=(20, 10))

        ttk.Radiobutton(
            tts_frame,
            text="gTTS (онлайн)",
            variable=self.tts_engine,
            value="gtts"
        ).pack(side=tk.LEFT)

        log_frame = ttk.LabelFrame(main_frame, text="📋 Лог", padding="15")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))

        self.log_text = tk.Text(
            log_frame,
            height=10,
            wrap=tk.WORD,
            font=("Consolas", 9)
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(self.log_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_text.yview)

    def check_config(self):
        """Проверка конфигурации"""
        from src.config import AI_PROVIDER

        if AI_PROVIDER == 'openai':
            self.log("✅ OpenAI API настроен")
        elif AI_PROVIDER == 'yandex':
            self.log("✅ YandexGPT API настроен")

        from src.config import GOOGLE_CREDENTIALS_FILE
        if GOOGLE_CREDENTIALS_FILE.exists():
            self.log("✅ Google Calendar credentials найдены")
        else:
            self.log("⚠️ Google Calendar credentials не найдены")
            self.log("   Календарь будет недоступен")

    def log(self, message: str):
        """Добавление сообщения в лог"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def start_assistant(self):
        """Запуск ассистента"""
        # Обновляем статус
        self.status_var.set("🟢 Ассистент запущен")
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

        self.log("🚀 Запуск AI-ассистента...")

        self.assistant_thread = threading.Thread(target=self._run_assistant, daemon=True)
        self.assistant_thread.start()

    def _run_assistant(self):
        """Запуск ассистента в потоке"""
        try:
            import sys
            from io import StringIO

            class LogRedirector:
                def __init__(self, log_func):
                    self.log_func = log_func
                    self.buffer = ""

                def write(self, text):
                    if text.strip():
                        self.log_func(text.strip())

                def flush(self):
                    pass

            original_stdout = sys.stdout
            sys.stdout = LogRedirector(self.log)

            self.assistant = AIAssistant()
            self.assistant.set_listen_mode(self.listen_mode.get())
            self.assistant.start()

            sys.stdout = original_stdout

        except Exception as e:
            self.log(f"❌ Ошибка: {e}")
            self.root.after(0, self.stop_assistant)

    def stop_assistant(self):
        """Остановка ассистента"""
        if self.assistant:
            self.assistant.stop()
            self.assistant = None

        self.status_var.set("🟡 Ассистент остановлен")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log("👋 Ассистент остановлен")

    def on_closing(self):
        """Обработчик закрытия окна"""
        self.stop_assistant()
        self.root.destroy()


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(
        description="🤖 AI-ассистент с голосовым управлением",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--cli',
        action='store_true',
        help='Запуск в режиме командной строки (без GUI)'
    )

    parser.add_argument(
        '--mode',
        choices=['once', 'continuous'],
        default='once',
        help='Режим прослушивания'
    )

    args = parser.parse_args()

    if not check_dependencies():
        sys.exit(1)

    if args.cli:
        print("🤖 Запуск в консольном режиме...")
        assistant = AIAssistant()
        assistant.set_listen_mode(args.mode)
        try:
            assistant.start()
        except KeyboardInterrupt:
            assistant.stop()
    else:
        root = tk.Tk()
        app = AssistantGUI(root)
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        root.mainloop()


if __name__ == "__main__":
    main()