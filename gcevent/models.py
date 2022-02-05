from django.db import models


# Create your models here.
class UserCredentials(models.Model):
    uid = models.CharField(max_length=200, unique=True)
    state = models.TextField()
    code = models.TextField()
    scope = models.TextField()
    credentials = models.JSONField()
    profile = models.JSONField()
    celery_run = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.profile['name']


class Events(models.Model):
    user = models.ManyToManyField(UserCredentials)
    ev_id = models.CharField(max_length=200, unique=True)
    summary = models.TextField(null=True)
    status = models.CharField(max_length=200)
    link = models.URLField()
    event_json = models.JSONField()
    created_at = models.DateTimeField()

    def __str__(self):
        return self.summary


class CeleryLog(models.Model):
    event_fetched = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
