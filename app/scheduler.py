import schedule
import time
import subprocess
import sys
import datetime
from settings import APP_DIR, SCHEDULE_DAY, SCHEDULE_TIME, SCHEDULE_POLL_INTERVAL

#script that ensures that the market research pipeline runs reguraly without manual intervetion 
#every Monday at 9AM the script will run and the agent will start working it will do its job and then migrate the data from the db into the google sheets and the n8n process starts since theres a googlesheet trigger there, n8n workflow starts and add every processed data inside the notion db and then the web interface automatically updates the web interface
#the script enter an infinite loop checking every minute if the scheduled time arrived
#if the scheduled time arrives it automatically launches the full workflow

pipeline_scheduler = str(APP_DIR / "main_script.py")

def job():
    print(f"Starting weekly job at {datetime.datetime.now()}")
    try:
        result = subprocess.run([sys.executable, "-u", pipeline_scheduler], check=True, cwd=APP_DIR)
        print("success")
    except subprocess.CalledProcessError as e:
        print(f"error code = {e.returncode}")
    except Exception as e:
        print(f"error = {e}")


def main():
    getattr(schedule.every(), SCHEDULE_DAY).at(SCHEDULE_TIME).do(job)
    while True:
        schedule.run_pending()
        time.sleep(SCHEDULE_POLL_INTERVAL)


if __name__ == "__main__":
    main()
