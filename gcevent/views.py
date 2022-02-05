from __future__ import print_function

import json

from django.shortcuts import render, HttpResponseRedirect, reverse, HttpResponse
from django.conf import settings
import datetime
import requests
import os.path
from django.contrib.auth.models import User
from .models import *
from google.auth.transport.requests import Request as RequestG
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from google.oauth2 import id_token
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google.oauth2.credentials

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly', 'https://www.googleapis.com/auth/userinfo.email',
          'https://www.googleapis.com/auth/userinfo.profile', 'openid']

cred_path = os.path.join(settings.BASE_DIR, 'gcevent/client_secret.json')


def seed():
    if not User.objects.filter(username='gcevent').exists():
        instance = User.objects.create(
            first_name='GC',
            last_name='Event',
            email='gcevent@gcevent.com',
            username='gcevent',
            is_superuser=True,
            is_staff=True
        )
        instance.set_password('gcevent')
        instance.save()


def index(request):
    seed()
    if settings.DEBUG:
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    return render(request, 'gcevent/index.html')


def getAuthToken(request):
    # Use the client_secret.json file to identify the application requesting
    # authorization. The client ID (from that file) and access scopes are required.
    flow = Flow.from_client_secrets_file(cred_path, SCOPES)

    # Indicate where the API server will redirect the user after the user completes
    # the authorization flow. The redirect URI is required. The value must exactly
    # match one of the authorized redirect URIs for the OAuth 2.0 client, which you
    # configured in the API Console. If this value doesn't match an authorized URI,
    # you will get a 'redirect_uri_mismatch' error.
    redirect_uri = request.build_absolute_uri(reverse('oauth.callback'))
    if "http:" in redirect_uri:
        redirect_uri = "https:" + redirect_uri[5:]
    flow.redirect_uri = redirect_uri

    # Generate URL for request to Google's OAuth 2.0 server.
    # Use kwargs to set optional request parameters.
    authorization_url, state = flow.authorization_url(
        # Enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true')
    return HttpResponseRedirect(authorization_url)


def oauthCallback(request):
    authorization_response = request.build_absolute_uri()
    if "http:" in authorization_response:
        authorization_response = "https:" + authorization_response[5:]
    # Use the client_secret.json file to identify the application requesting
    # authorization. The client ID (from that file) and access scopes are required.
    flow = Flow.from_client_secrets_file(cred_path, SCOPES, state=request.GET['state'])
    redirect_uri = request.build_absolute_uri(reverse('oauth.callback'))
    if "http:" in redirect_uri:
        redirect_uri = "https:" + redirect_uri[5:]
    flow.redirect_uri = redirect_uri

    flow.fetch_token(authorization_response=authorization_response)

    # Credential object
    credentials = flow.credentials

    user_profile = getUserProfileInfo(credentials.token)
    credentials = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }

    if not UserCredentials.objects.filter(uid=user_profile['id']).exists():
        UserCredentials.objects.create(
            uid=user_profile['id'],
            state=request.GET['state'],
            code=request.GET['code'],
            scope=request.GET['scope'],
            credentials=credentials,
            profile=user_profile
        )
        response = {
            'msg': 'You have successfully granted access to view your calendar events.'
        }
    else:
        response = {
            'msg': 'You have already granted access to view your calendar events.'
        }

    return HttpResponseRedirect(reverse('oauth.response', kwargs={'msg': response.get('msg')}))


def getUserProfileInfo(token):
    url = f"https://www.googleapis.com/oauth2/v1/userinfo?alt=json&access_token={token}"

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)

    return json.loads(response.text)


def oauthResponse(request, msg):
    context = {
        'msg': msg
    }
    return render(request, 'gcevent/success.html', context)


@login_required
def celeryLog(request):
    celery_log = CeleryLog.objects.all().order_by('-created_at')
    context = {
        'celery_log': celery_log
    }
    return render(request, 'gcevent/celery-log.html', context)


@login_required
def userList(request):
    user_list = UserCredentials.objects.all().order_by('created_at')
    context = {
        'user_list': user_list
    }
    return render(request, 'gcevent/user-list.html', context)


@login_required
def fetchEvents(request, uid):
    user = UserCredentials.objects.get(uid=uid)
    credentials = user.credentials
    # import six
    # print(six.iterkeys(credentials))

    # token_file = os.path.join(settings.BASE_DIR, f'gcevent/tokens/{uid}.json')
    # token = open(token_file, "w")
    # token.write("Woops! I have deleted the content!")
    # token.close()

    # creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    creds = Credentials.from_authorized_user_info(credentials, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(RequestG())
        else:
            messages.error(request, 'Invalid/Expired credentials! Please authorize again.')
            return HttpResponseRedirect(reverse('user.list'))

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
            except Exception:
                pass
        messages.success(request, 'Events fetched successfully!')
    except HttpError as error:
        messages.error(request, 'An error occurred: %s' % error)

    return HttpResponseRedirect(reverse('user.list'))


@login_required
def deleteUser(request, uid):
    UserCredentials.objects.get(uid=uid).delete()
    messages.success(request, 'User deleted successfully!')
    return HttpResponseRedirect(reverse('user.list'))


@login_required
def viewEvents(request, uid):
    user_info = UserCredentials.objects.get(uid=uid)
    event_list = Events.objects.filter(user__uid=uid)
    context = {
        'event_list': event_list,
        'user_info': user_info
    }
    return render(request, 'gcevent/event-list.html', context)
