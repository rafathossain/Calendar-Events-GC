FROM python:3.9.4
ENV PYTHONUNBUFFERED=1
WORKDIR /gcevent
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
#CMD ["python", "manage.py", "runserver", "0.0.0.0:8181"]
CMD ["gunicorn", "--bind", ":8181", "calendar_events.wsgi"]