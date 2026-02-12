import speech_recognition as sr
import pyttsx3
import threading
import queue
import time
from typing import Optional, Callable
import pygame
from gtts import gTTS
import io
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.config import VOICE_RATE, VOICE_VOLUME, VOICE_GENDER, RECOGNITION_LANGUAGE, ASSISTANT_NAME
except ImportError:
    try:
        from config import VOICE_RATE, VOICE_VOLUME, VOICE_GENDER, RECOGNITION_LANGUAGE, ASSISTANT_NAME
    except ImportError:
        VOICE_RATE = 150
        VOICE_VOLUME = 1.0
        VOICE_GENDER = 'male'
        RECOGNITION_LANGUAGE = 'ru-RU'
        ASSISTANT_NAME = 'Алиса'


class VoiceEngine:
    """Класс для работы с голосовым вводом/выводом"""

    def __init__(self):
        self.recognizer = sr.Recognizer()

        try:
            self.microphone = sr.Microphone()
        except Exception as e:
            print(f"❌ Ошибка инициализации микрофона: {e}")
            self.microphone = None

        try:
            self.tts_engine = pyttsx3.init()
            self._configure_voice()
        except Exception as e:
            print(f"❌ Ошибка инициализации TTS: {e}")
            self.tts_engine = None

        self.listen_queue = queue.Queue()
        self.is_listening = False
        self.listen_thread = None
        self.listen_callback = None

        self.use_gtts = False
        try:
            pygame.mixer.init()
        except:
            pass

        print("🎤 Voice engine initialized")

    def _configure_voice(self):
        """Настройка голоса pyttsx3"""
        if not self.tts_engine:
            return

        try:
            voices = self.tts_engine.getProperty('voices')

            if VOICE_GENDER == 'female' and len(voices) > 1:
                self.tts_engine.setProperty('voice', voices[1].id)
            else:
                self.tts_engine.setProperty('voice', voices[0].id)

            self.tts_engine.setProperty('rate', VOICE_RATE)
            self.tts_engine.setProperty('volume', VOICE_VOLUME)
        except:
            pass

    def speak(self, text: str):
        """Озвучивание текста"""
        print(f"🤖 {ASSISTANT_NAME}: {text}")

        if self.use_gtts:
            self._speak_gtts(text)
        else:
            self._speak_pyttsx3(text)

    def _speak_pyttsx3(self, text: str):
        """Озвучивание через pyttsx3"""
        if not self.tts_engine:
            print("⚠️ TTS engine не инициализирован")
            self._speak_gtts(text)
            return

        try:
            self.tts_engine.say(text)
            self.tts_engine.runAndWait()
        except Exception as e:
            print(f"❌ Ошибка озвучивания: {e}")
            self._speak_gtts(text)

    def _speak_gtts(self, text: str):
        """Озвучивание через Google TTS"""
        try:
            tts = gTTS(text=text, lang=RECOGNITION_LANGUAGE[:2])
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            fp.seek(0)
            pygame.mixer.music.load(fp)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
        except Exception as e:
            print(f"❌ gTTS error: {e}")

    def listen_once(self, timeout: int = 5, phrase_time_limit: int = 5) -> Optional[str]:
        """Однократное прослушивание"""
        if not self.microphone:
            print("❌ Микрофон не доступен")
            return None

        try:
            with self.microphone as source:
                print("🎧 Слушаю...")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

            print("🔄 Распознаю...")
            text = self.recognizer.recognize_google(audio, language=RECOGNITION_LANGUAGE)
            print(f"📝 Распознано: {text}")
            return text

        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except sr.RequestError as e:
            print(f"❌ Ошибка сервиса распознавания: {e}")
            return None
        except Exception as e:
            print(f"❌ Ошибка: {e}")
            return None

    def start_listening(self, callback: Callable[[str], None]):
        """Запуск непрерывного прослушивания в фоне"""
        if not self.microphone:
            print("❌ Микрофон не доступен")
            return

        self.is_listening = True
        self.listen_callback = callback

        def listen_loop():
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source)

                while self.is_listening:
                    try:
                        audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=5)
                        text = self.recognizer.recognize_google(audio, language=RECOGNITION_LANGUAGE)
                        if text and self.listen_callback:
                            self.listen_callback(text)
                    except sr.WaitTimeoutError:
                        continue
                    except sr.UnknownValueError:
                        continue
                    except Exception as e:
                        print(f"❌ Ошибка в цикле прослушивания: {e}")
                        time.sleep(0.5)

        self.listen_thread = threading.Thread(target=listen_loop, daemon=True)
        self.listen_thread.start()
        print("🎧 Непрерывное прослушивание запущено")

    def stop_listening(self):
        """Остановка непрерывного прослушивания"""
        self.is_listening = False
        if self.listen_thread:
            self.listen_thread.join(timeout=2)
        print("🎧 Прослушивание остановлено")

    def toggle_gtts(self, enabled: bool):
        """Переключение между pyttsx3 и gTTS"""
        self.use_gtts = enabled
        print(f"🔊 gTTS {'включен' if enabled else 'выключен'}")


voice = VoiceEngine()