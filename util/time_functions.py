import datetime
import pytz
import asyncio


async def run_daily_task(times, timezone='US/Eastern'):
    time_list = [int(num) for num in times.split(':')]

    timezone = pytz.timezone(timezone)
    target_time = timezone.localize(datetime.datetime.now().replace(hour=time_list[0], minute=time_list[1], second=time_list[2]))

    current_time = timezone.localize(datetime.datetime.now())
    if current_time >= target_time:
        target_time += datetime.timedelta(days=1)

    time_difference = target_time - current_time
    await asyncio.sleep(time_difference.total_seconds())


async def run_half_hourly_task(timezone='US/Eastern'):
    current_time = datetime.datetime.now(pytz.timezone(timezone))

    # Calculate the time until the next 30-minute mark
    minutes_until_next_30 = (30 - current_time.minute % 30) % 30
    seconds_until_next_30 = 60 - current_time.second

    # Calculate the total time difference
    time_difference = datetime.timedelta(minutes=minutes_until_next_30, seconds=seconds_until_next_30)

    # Sleep for the calculated time difference
    await asyncio.sleep(time_difference.total_seconds())


async def time_ago(timestamp):
    current_time = datetime.datetime.utcnow()
    timestamp_datetime = datetime.datetime.utcfromtimestamp(timestamp)
    time_difference = current_time - timestamp_datetime
    seconds_ago = int(time_difference.total_seconds())

    msg = []
    if seconds_ago // 86400 >= 1:
        days_ago = seconds_ago // 86400
        seconds_ago -= days_ago * 86400
        msg.append(f'{days_ago} {["day", "days"][days_ago > 1]}')

    if seconds_ago // 3600 >= 1:
        hours_ago = seconds_ago // 3600
        seconds_ago -= hours_ago * 3600
        msg.append(f'{hours_ago} {["hour", "hours"][hours_ago > 1]}')

    if seconds_ago // 60 >= 1:
        minutes_ago = seconds_ago // 60
        seconds_ago -= minutes_ago * 60
        msg.append(f'{minutes_ago} {["minute", "minutes"][minutes_ago > 1]}')

    if seconds_ago:
        msg.append(f'{seconds_ago} {["second", "seconds"][seconds_ago > 1]}')

    if not msg:
        msg.append("less than 1 second")

    return ' '.join(msg)
