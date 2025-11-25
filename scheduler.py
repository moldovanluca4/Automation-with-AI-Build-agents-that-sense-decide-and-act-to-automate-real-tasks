import schedule
import time
import subprocess
import sys
import datetime

#script that ensures that the market research pipeline runs reguraly without manual intervetion 
#every Monday at 9AM the script will run and the agent will start working it will do its job and then migrate the data from the db into the google sheets and the n8n process starts since theres a googlesheet trigger there, n8n workflow starts and add every processed data inside the notion db and then the web interface automatically updates the web interface
#the script enter an infinite loop checking every minute if the scheduled time arrived
#if the scheduled time arrives it automatically launches the full workflow

pipeline_scheduler = "main_pipeline.py" 

def job():
    print(f"Starting weekly job at {datetime.datetime.now()}")
    try:
        result = subprocess.run([sys.executable, "-u", pipeline_scheduler], check=True)
        print("success")
    except subprocess.CalledProcessError as e:
        print(f"error code = {e.returncode}")
    except Exception as e:
        print(f"error = {e}")


schedule.every().monday.at("09:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(60)