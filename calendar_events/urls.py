"""calendar_events URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from gcevent.views import *

urlpatterns = [
    path('', index, name='index'),
    path('get-token', getAuthToken, name='get.auth.token'),
    path('oauth2callback', oauthCallback, name='oauth.callback'),
    path('oauth-response/<str:msg>', oauthResponse, name='oauth.response'),
    path('user-list', userList, name='user.list'),
    path('celery-log', celeryLog, name='celery.log'),
    path('user-list/fetch-events/<str:uid>', fetchEvents, name='user.fetch.events'),
    path('user-list/fetch-contacts/<str:uid>', fetchContacts, name='user.fetch.contacts'),
    path('user-list/view-events/<str:uid>', viewEvents, name='user.view.events'),
    path('user-list/delete/<str:uid>', deleteUser, name='user.delete'),
    path('accounts/', admin.site.urls),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
