
from apscheduler.schedulers.background import BackgroundScheduler

# from ..services.alert_service import AlertService

scheduler = BackgroundScheduler()

def start_scheduler():
    # TODO: Add jobs
    # scheduler.add_job(AlertService.generate_alerts, 'interval', hours=24)
    scheduler.start()
