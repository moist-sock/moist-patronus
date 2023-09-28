import time
import datetime
import pytz


async def run_daily_task(times, timezone='US/Eastern'):
    time_list = [int(num) for num in times.split(':')]

    timezone = pytz.timezone(timezone)
    target_time = timezone.localize(datetime.datetime.now().replace(hour=time_list[0], minute=time_list[1], second=time_list[3]))

    current_time = timezone.localize(datetime.datetime.now())
    if current_time >= target_time:
        target_time += datetime.timedelta(days=1)

    time_difference = target_time - current_time
    time.sleep(time_difference.total_seconds())
