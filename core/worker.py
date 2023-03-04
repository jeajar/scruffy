from celery import Celery
from core.janitor import Janitor
from celery.schedules import crontab

"""
celery -A core.worker worker -B -l INFO
"""

app = Celery(
    'scruffy_worker',
    broker="amqp://guest@localhost//")

cleaner = Janitor()
app.conf.enable_utc = False
app.conf.timezone = "America/Toronto"

app.conf.beat_schedule = {
    'run-movies-every-minute': {
        'task': 'core.worker.run',
        'schedule': crontab(day_of_week=6, minute=14, hour=15),
    },
    'run-test': {
        'task': 'core.worker.test',
        'schedule': crontab(minute="*", hour=15, day_of_week=6)
    }
}

@app.task
def run():
    #print("Hello mom")
    movies = cleaner.process_movie_requests()
    return movies

@app.task
def test():
    print("Hello from test Celery")