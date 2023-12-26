from datetime import datetime


async def parse_time(data):
    # Розділити рядок на години, хвилини і дні
    time_parts = data.split(' - ')
    time_str = time_parts[0]
    day_str = time_parts[1]

    # Розділити години та хвилини
    hours, minutes = map(int, time_str.split(':'))

    # Повернути результат у вигляді словника
    result = {
        'hours': hours,
        'minutes': minutes,
        'day': day_str
    }

    print(result)
    return result

async def seconds_to_dhms(seconds):
    # Розраховуємо кількість днів, годин і хвилин
    days = seconds // (24 * 3600)
    hours = (seconds % (24 * 3600)) // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    print(f"{days} днів, {hours} годин, {minutes} минут, {seconds} секунд.")
    # Повертаємо результат у вигляді кортежу
    return days, hours, minutes, seconds


async def time_until(hours, minutes, day):
    time_now = datetime.now()
    date_now = datetime.now()

    received_hours_in_seconds = int(hours) * 3600
    received_minutes_in_seconds = int(minutes) * 60
    received_day_in_seconds = int(day) * 86400
    current_hours_in_seconds = int(time_now.strftime("%H")) * 3600
    current_minutes_in_seconds = int(time_now.strftime("%M")) * 60
    current_day_in_seconds = int(date_now.strftime('%d')) * 86400

    current_time = current_hours_in_seconds + current_minutes_in_seconds + int(time_now.strftime("%S")) + current_day_in_seconds
    received_time = received_hours_in_seconds + received_minutes_in_seconds + received_day_in_seconds

    if received_time > current_time:
        waiting_time = received_time - current_time
        await seconds_to_dhms(waiting_time)
        return waiting_time
    if current_time > received_time:
        waiting_time = (86400 - current_time) + received_time
        await seconds_to_dhms(waiting_time)
        return waiting_time


#if __name__ == '__main__':
   # data = "2:9 - 2"
    #parsed_data = parse_time(data)
   # print(parsed_data)
