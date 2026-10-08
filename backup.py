import os
import csv
import smtplib

from time import sleep
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from email.message import EmailMessage


# ------------------ constants -----------------------------------------------------------------------------------------


load_dotenv()

# email sender and recipient addresses
SENDER = os.getenv("SENDER")
RECIPIENT = os.getenv("RECIPIENT")

# sunlime dev app password
SMTP_KEY = os.getenv("SMTP_KEY")

# google mail server
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

# daily shop hours
WED_CLOSE_HOUR = 16   # 4pm
THU_CLOSE_HOUR = 20   # 8pm
SAT_CLOSE_HOUR = 14   # 2pm

# directory for csv files
FORM_DATA_FOLDER = "logs"


# ------------------ functions -----------------------------------------------------------------------------------------


# aggregate current day data into monthly file
def aggregate(file_path, month, year, close_datetime):
    monthly_data_file_path = Path(f"{FORM_DATA_FOLDER}/{month}-{year}.csv")

    timestamp_format = "%Y-%m-%d %H:%M:%S"

    with open(file_path, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        headers = next(reader)

        dates = []
        names = []
        types = []
        reasons = []
        emails = []
        phones = []
        hours = []

        for row in reader:
            dates.append(row[0])
            names.append(row[1])
            types.append(row[2])
            reasons.append(row[3])
            emails.append(row[4])
            phones.append(row[5])
            hours.append(row[6])

    with open(file_path, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)

        # adjust hours of volunteer since they are being signed out
        for i in range(len(names)):
            if types[i] == "volunteer" and hours[i] == "0":
                start_time = datetime.strptime(dates[i], timestamp_format)
                hours[i] = str(round(((close_datetime - start_time).total_seconds() / 3600) + 0.01, ndigits=2))

            # rebuild the file
            writer.writerow([dates[i], names[i], types[i], reasons[i], emails[i], phones[i], hours[i]])

    just_created = not monthly_data_file_path.is_file()

    with open(monthly_data_file_path, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        if just_created:
            writer.writerow(headers)

        for i in range(len(names)):
            writer.writerow([dates[i], names[i], types[i], reasons[i], emails[i], phones[i], hours[i]])

    return


# send a provided file to a specific recipient
def send_email(month, year):
    # build the email data
    msg = EmailMessage()
    msg["Subject"] = f"Backup Visitor/Volunteer Data"
    msg["From"] = SENDER
    msg["To"] = RECIPIENT
    msg.set_content(f"Hello,\n\nThe up-to-date visitor and volunteer log for {month} {year} is attached to this email.\n\nHave a nice day.")

    file_path = Path(f"logs/{month}-{year}.csv")

    # get the csv file
    try:
        with open(file_path, "rb") as file:
            file_data = file.read()

        msg.add_attachment(
            file_data,
            maintype="text",
            subtype="csv",
            filename=file_path.name,
        )
    except FileNotFoundError:
        print(f"Error: The file at {file_path} was not found.")
        return False

    # connect to smtp server and send email
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER, SMTP_KEY)
            server.send_message(msg)

        return True
    except Exception as e:
        print(f"An error occurred while sending the email: {e}")
        return False


# ------------------ main ----------------------------------------------------------------------------------------------


def main():
    while True:
        now = datetime.now()
        month = now.strftime("%B")
        year = now.strftime("%Y")
        today = now.strftime("%Y-%m-%d")

        # create email send bounds
        wed_close_time = now.replace(hour=WED_CLOSE_HOUR, minute=0, second=0, microsecond=0)
        wed_send_deadline = now.replace(hour=WED_CLOSE_HOUR, minute=5, second=0, microsecond=0)
        thu_close_time = now.replace(hour=THU_CLOSE_HOUR, minute=0, second=0, microsecond=0)
        thu_send_deadline = now.replace(hour=THU_CLOSE_HOUR, minute=5, second=0, microsecond=0)
        sat_close_time = now.replace(hour=SAT_CLOSE_HOUR, minute=0, second=0, microsecond=0)
        sat_send_deadline = now.replace(hour=SAT_CLOSE_HOUR, minute=5, second=0, microsecond=0)

        # check if form data exists for today
        file_path = Path(f"{FORM_DATA_FOLDER}/{today}.csv")

        # send email if file exists and within bounds
        if file_path.is_file():
            # wednesday
            if now.weekday() == 2:
                if wed_close_time < now < wed_send_deadline:
                    aggregate(file_path, month, year, wed_close_time)
                    _ = send_email(month, year)
                    sleep(300)
                    continue
            # thursday
            elif now.weekday() == 3:
                if thu_close_time < now < thu_send_deadline:
                    aggregate(file_path, month, year, thu_close_time)
                    _ = send_email(month, year)
                    sleep(300)
                    continue
            # saturday
            elif now.weekday() == 5:
                if sat_close_time < now < sat_send_deadline:
                    aggregate(file_path, month, year, sat_close_time)
                    _ = send_email(month, year)
                    sleep(300)
                    continue

        sleep(5)


if __name__ == "__main__":
    main()