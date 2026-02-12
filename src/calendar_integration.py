import datetime
import pickle
import os
from typing import List, Dict, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from config import GOOGLE_CALENDAR_SCOPES, GOOGLE_CALENDAR_ID, TOKEN_PATH, GOOGLE_CREDENTIALS_FILE


class GoogleCalendar:
    """Класс для работы с Google Calendar API"""

    def __init__(self):
        self.service = None
        self.authenticate()

    def authenticate(self):
        """Аутентификация в Google Calendar API"""
        creds = None

        if os.path.exists(TOKEN_PATH):
            try:
                with open(TOKEN_PATH, 'rb') as token:
                    creds = pickle.load(token)
            except:
                pass

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except:
                    creds = None

            if not creds:
                if not os.path.exists(GOOGLE_CREDENTIALS_FILE):
                    print("\n" + "=" * 60)
                    print("❌ Файл credentials не найден!")
                    print("=" * 60)
                    print("\nДля работы с Google Calendar необходимо:")
                    print("1. Перейти на https://console.cloud.google.com/")
                    print("2. Создать проект и включить Google Calendar API")
                    print("3. Создать credentials (OAuth 2.0 Client ID)")
                    print("4. Скачать JSON файл и сохранить как:")
                    print(f"   {GOOGLE_CREDENTIALS_FILE}\n")
                    return

                flow = InstalledAppFlow.from_client_secrets_file(
                    GOOGLE_CREDENTIALS_FILE, GOOGLE_CALENDAR_SCOPES
                )
                creds = flow.run_local_server(port=0)

            with open(TOKEN_PATH, 'wb') as token:
                pickle.dump(creds, token)

        try:
            self.service = build('calendar', 'v3', credentials=creds)
            print("✅ Google Calendar API connected")
        except Exception as e:
            print(f"❌ Google Calendar API error: {e}")

    def get_upcoming_events(self, max_results: int = 10) -> List[Dict]:
        """Получение предстоящих событий"""
        if not self.service:
            return []

        try:
            now = datetime.datetime.utcnow().isoformat() + 'Z'

            events_result = self.service.events().list(
                calendarId=GOOGLE_CALENDAR_ID,
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            events = events_result.get('items', [])

            formatted_events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                formatted_events.append({
                    'summary': event['summary'],
                    'start': start,
                    'id': event['id'],
                    'description': event.get('description', '')
                })

            return formatted_events

        except HttpError as error:
            print(f"❌ An error occurred: {error}")
            return []

    def create_event(self, summary: str, start_time: datetime.datetime,
                     end_time: datetime.datetime = None, description: str = "") -> Optional[Dict]:
        """Создание нового события"""
        if not self.service:
            return None

        try:
            if not end_time:
                end_time = start_time + datetime.timedelta(hours=1)

            event = {
                'summary': summary,
                'description': description,
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'Europe/Moscow',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'Europe/Moscow',
                },
            }

            event = self.service.events().insert(
                calendarId=GOOGLE_CALENDAR_ID,
                body=event
            ).execute()

            return {
                'id': event['id'],
                'summary': event['summary'],
                'link': event.get('htmlLink', '')
            }

        except HttpError as error:
            print(f"❌ An error occurred: {error}")
            return None

    def delete_event(self, event_id: str) -> bool:
        """Удаление события"""
        if not self.service:
            return False

        try:
            self.service.events().delete(
                calendarId=GOOGLE_CALENDAR_ID,
                eventId=event_id
            ).execute()
            return True
        except HttpError as error:
            print(f"❌ An error occurred: {error}")
            return False

    def get_today_events(self) -> List[Dict]:
        """Получение событий на сегодня"""
        if not self.service:
            return []

        try:
            now = datetime.datetime.utcnow()
            end_of_day = now.replace(hour=23, minute=59, second=59)

            events_result = self.service.events().list(
                calendarId=GOOGLE_CALENDAR_ID,
                timeMin=now.isoformat() + 'Z',
                timeMax=end_of_day.isoformat() + 'Z',
                singleEvents=True,
                orderBy='startTime'
            ).execute()

            return events_result.get('items', [])

        except HttpError as error:
            print(f"❌ An error occurred: {error}")
            return []

    def format_events_text(self, events: List[Dict]) -> str:
        """Форматирование событий в текст"""
        if not events:
            return "На сегодня событий нет."

        text = "📅 Ваши события:\n\n"
        for i, event in enumerate(events, 1):
            start = event['start'].get('dateTime', event['start'].get('date'))

            try:
                dt = datetime.datetime.fromisoformat(start.replace('Z', '+00:00'))
                time_str = dt.strftime('%H:%M')
            except:
                time_str = start

            text += f"{i}. {time_str} - {event['summary']}\n"

            if event.get('description'):
                text += f"   📝 {event['description'][:50]}\n"
            text += "\n"

        return text


calendar = GoogleCalendar()