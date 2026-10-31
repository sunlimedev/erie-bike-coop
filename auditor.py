# Application Log Auditor Script


# ------------------ imports -------------------------------------------------------------------------------------------


from time import sleep
from datetime import datetime

from database import sign_out_all
from config import WED_CLOSE, THU_CLOSE, SAT_CLOSE, FALLBACK


# ------------------ loop ----------------------------------------------------------------------------------------------


while True:
    # get current time
    now = datetime.now()

    # sign out all volunteers two hours after close
    if now.weekday() == 2 and now.hour >= WED_CLOSE + 2:
        sign_out_all()
        print(f"Signed out all volunteers for Wednesday {now.strftime("%Y-%m-%d")}")
        sleep((24 - WED_CLOSE + 2) * 3600)
        continue
    if now.weekday() == 3 and now.hour >= THU_CLOSE + 2:
        sign_out_all()
        print(f"Signed out all volunteers for Thursday {now.strftime("%Y-%m-%d")}")
        sleep((24 - THU_CLOSE + 2) * 3600)
        continue
    if now.weekday() == 5 and now.hour >= SAT_CLOSE + 2:
        sign_out_all()
        print(f"Signed out all volunteers for Saturday {now.strftime("%Y-%m-%d")}")
        sleep((24 - SAT_CLOSE + 2) * 3600)
        continue
    # fallback if not a typically open day
    if now.hour >= FALLBACK:
        sign_out_all()
        print(f"Signed out all volunteers for {now.strftime("%Y-%m-%d")}")
        sleep((24 - FALLBACK) * 3600)
        continue

    sleep(1)
