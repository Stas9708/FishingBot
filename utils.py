import datetime


def send_date():
    current_date = datetime.datetime.now().strftime("%d-%m-%Y")
    return current_date
