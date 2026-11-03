# Application Database Exporter File


# ------------------ import --------------------------------------------------------------------------------------------


import smtplib

from pathlib import Path
from email.message import EmailMessage

from config import DATABASE_FILE, SENDER, RECIPIENT, SMTP_SERVER, SMTP_PORT, SMTP_KEY


# ------------------ script --------------------------------------------------------------------------------------------


def export_database(db: Path):
    # create the message object
    message = EmailMessage()

    # configure the message
    message["From"] = SENDER
    message["To"] = RECIPIENT
    message["Subject"] = "Application Database Backup"
    message.set_content("Attached is the database file for the Erie Bike Co-op logging application.")

    # read the database file
    with open(db, 'rb') as file:
        data = file.read()

    # construct the attachment
    message.add_attachment(
        data,
        maintype='application',
        subtype='octet-stream',
        filename=db.name
    )

    # connect to smtp server and send email
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER, SMTP_KEY)
            server.send_message(message)

        print("Email sent successfully")
        return True
    except Exception as e:
        print(f"Failed to connect to Gmail: {e}")
        return False


# ------------------ execution guard -----------------------------------------------------------------------------------


if __name__ == "__main__":
    export_database(DATABASE_FILE)
