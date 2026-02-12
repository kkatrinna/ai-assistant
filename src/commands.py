import datetime
import webbrowser
import sys
import os
from typing import Dict, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.config import ASSISTANT_NAME
except ImportError:
    try:
        from config import ASSISTANT_NAME
    except ImportError:
        ASSISTANT_NAME = 'Алиса'


class CommandHandler:
    """Обработчик команд"""

    def __init__(self, ai_engine, calendar, voice):
        self.ai = ai_engine
        self.calendar = calendar
        self.voice = voice
        self.assistant_name = ASSISTANT_NAME

    def process_command(self, text: str) -> Dict[str, Any]:
        """Обработка команды"""
        text = text.lower()

        if any(word in text for word in ['события', 'календарь', 'план', 'расписание']):
            return self._handle_calendar_command(text)

        elif 'время' in text or 'часов' in text or 'который час' in text:
            return self._handle_time_command()

        elif 'дата' in text or 'число' in text or 'какой день' in text or 'сегодня' in text:
            return self._handle_date_command()

        elif 'открой' in text:
            return self._handle_browser_command(text)

        elif any(word in text for word in ['помощь', 'help', 'что ты умеешь', 'команды']):
            return self._handle_help_command()

        elif any(word in text for word in ['пока', 'до свидания', 'выход', 'стоп']):
            return {
                'action': 'exit',
                'response': 'До свидания! Буду ждать ваших указаний.',
                'speak': True
            }

        else:
            return self._handle_ai_command(text)

    def _handle_calendar_command(self, text: str) -> Dict[str, Any]:
        """Обработка команд календаря"""
        events = []

        if 'сегодня' in text:
            events = self.calendar.get_today_events()
            if events:
                events_text = self.calendar.format_events_text(events)
                return {
                    'action': 'calendar',
                    'response': f"Вот ваши события на сегодня:\n{events_text}",
                    'speak': True,
                    'data': events
                }
            else:
                return {
                    'action': 'calendar',
                    'response': "На сегодня у вас нет запланированных событий.",
                    'speak': True
                }
        else:
            events = self.calendar.get_upcoming_events(5)
            if events:
                events_text = self.calendar.format_events_text(events)
                return {
                    'action': 'calendar',
                    'response': f"Ближайшие события:\n{events_text}",
                    'speak': True,
                    'data': events
                }
            else:
                return {
                    'action': 'calendar',
                    'response': "У вас нет предстоящих событий.",
                    'speak': True
                }

    def _handle_time_command(self) -> Dict[str, Any]:
        """Обработка команды времени"""
        now = datetime.datetime.now()
        time_str = now.strftime("%H:%M")
        return {
            'action': 'time',
            'response': f"Сейчас {time_str}",
            'speak': True
        }

    def _handle_date_command(self) -> Dict[str, Any]:
        """Обработка команды даты"""
        now = datetime.datetime.now()
        date_str = now.strftime("%d.%m.%Y")
        weekday = self._get_weekday(now.weekday())
        return {
            'action': 'date',
            'response': f"Сегодня {weekday}, {date_str}",
            'speak': True
        }

    def _handle_browser_command(self, text: str) -> Dict[str, Any]:
        """Обработка команды открытия браузера"""
        sites = {
            'youtube': 'https://youtube.com',
            'ютуб': 'https://youtube.com',
            'google': 'https://google.com',
            'github': 'https://github.com',
            'гитхаб': 'https://github.com',
            'gmail': 'https://mail.google.com',
            'почта': 'https://mail.google.com',
            'яндекс': 'https://yandex.ru',
            'yandex': 'https://yandex.ru',
        }

        for key, url in sites.items():
            if key in text:
                try:
                    webbrowser.open(url)
                    return {
                        'action': 'browser',
                        'response': f"Открываю {key}",
                        'speak': True
                    }
                except:
                    return {
                        'action': 'error',
                        'response': f"Не удалось открыть {key}",
                        'speak': True
                    }

        return {
            'action': 'unknown',
            'response': "Я не знаю такой сайт",
            'speak': True
        }

    def _handle_ai_command(self, text: str) -> Dict[str, Any]:
        """Обработка команды через AI"""
        context = {
            'current_time': datetime.datetime.now().strftime("%H:%M"),
            'upcoming_events': []
        }

        try:
            events = self.calendar.get_upcoming_events(3)
            context['upcoming_events'] = [
                f"{e['summary']} в {e['start']}"
                for e in events
            ]
        except:
            pass

        response = self.ai.get_response(text, context)

        return {
            'action': 'ai_response',
            'response': response,
            'speak': True
        }

    def _handle_help_command(self) -> Dict[str, Any]:
        """Обработка команды помощи"""
        help_text = f"""
Я {self.assistant_name}, ваш AI-ассистент. Я умею:

📅 **Календарь:**
• "Покажи события" - ближайшие события
• "Что сегодня?" - события на сегодня

⏰ **Время и дата:**
• "Который час?" - текущее время
• "Какая дата?" - сегодняшняя дата

🌐 **Браузер:**
• "Открой YouTube" - открыть сайт
• "Открой Google" - открыть поисковик

💬 **Общение:**
• Просто задавайте вопросы - я отвечу через AI
• "Пока" - завершить работу

🎤 **Голос:**
• Говорите четко в микрофон
• Я понимаю русский язык
        """
        return {
            'action': 'help',
            'response': help_text,
            'speak': False
        }

    def _get_weekday(self, weekday_num: int) -> str:
        """Получение названия дня недели"""
        weekdays = [
            'понедельник', 'вторник', 'среда',
            'четверг', 'пятница', 'суббота', 'воскресенье'
        ]
        return weekdays[weekday_num]