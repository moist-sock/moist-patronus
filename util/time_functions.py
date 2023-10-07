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


# todo this function sucks help it!!!
async def time_ago(timestamp):
    current_time = datetime.datetime.utcnow()
    timestamp_datetime = datetime.datetime.utcfromtimestamp(timestamp)
    time_difference = current_time - timestamp_datetime
    seconds_ago = int(time_difference.seconds)

    time_ago = []
    if seconds_ago // 3600 >= 1:
        hours_ago = seconds_ago // 3600
        seconds_ago -= hours_ago * 3600
        time_ago.append(f'{hours_ago} {["hour", "hours"][hours_ago > 1]}')

    if seconds_ago // 60 >= 1:
        minutes_ago = seconds_ago // 60
        seconds_ago -= minutes_ago * 60
        time_ago.append(f'{minutes_ago} {["minute", "minutes"][minutes_ago > 1]}')

    if seconds_ago:
        time_ago.append(f'{seconds_ago} {["second", "seconds"][seconds_ago > 1]}')

    if not time_ago:
        time_ago.append("less than 1 second")

    return ' '.join(time_ago)
