from datetime import timedelta
from django.utils import timezone


def get_exam_end_time(time_limit):
    try:
        minutes = int(time_limit)
    except (TypeError, ValueError):
        minutes = 0

    if minutes > 0:
        return timezone.now() + timedelta(minutes=minutes)
    return None