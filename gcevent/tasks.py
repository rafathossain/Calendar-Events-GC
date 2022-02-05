import json
import os.path
from datetime import datetime

from celery import Celery
from django.conf import settings
from google.auth.transport.requests import Request as RequestG
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from .models import *
from .models import UserCredentials

app = Celery()


@app.task
def fetchEvents():
    # If modifying these scopes, delete the file token.json.
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly', 'https://www.googleapis.com/auth/userinfo.email',
              'https://www.googleapis.com/auth/userinfo.profile', 'openid']

    user_list = UserCredentials.objects.all()
    event_count = 0
    for user in user_list:
        uid = user.uid
        user = UserCredentials.objects.get(uid=uid)
        credentials = user.credentials

        # token_file = os.path.join(settings.BASE_DIR, f'gcevent/tokens/{uid}.json')
        # token = open(token_file, "w")
        # token.write("Woops! I have deleted the content!")
        # token.close()

        # creds = Credentials.from_authorized_user_file(token_file, SCOPES)
        creds = Credentials.from_authorized_user_info(credentials, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(RequestG())

        try:
            service = build('calendar', 'v3', credentials=creds)

            # Call the Calendar API
            events_result = service.events().list(calendarId='primary').execute()
            events = events_result.get('items', [])

            for event in events:
                try:
                    if Events.objects.filter(ev_id=event['id']).exists():
                        ev_instance = Events.objects.get(ev_id=event['id'])
                        ev_instance.summary = event['summary']
                        ev_instance.status = event['status']
                        ev_instance.link = event['htmlLink']
                        ev_instance.event_json = event
                        ev_instance.created_at = event['created']
                        ev_instance.save()
                    else:
                        ev_instance = Events.objects.create(
                            ev_id=event['id'],
                            summary=event['summary'],
                            status=event['status'],
                            link=event['htmlLink'],
                            event_json=event,
                            created_at=event['created']
                        )
                        ev_instance.user.add(user)
                        event_count += 1
                except Exception as e:
                    pass
        except Exception:
            pass

    CeleryLog.objects.create(
        event_fetched=event_count
    )
