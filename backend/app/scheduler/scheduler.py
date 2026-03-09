
from apscheduler.schedulers.background import BackgroundScheduler
from ..services.alert_service import AlertService

scheduler = BackgroundScheduler()

def start_scheduler():
    """Start the background scheduler for periodic tasks."""
    scheduler.add_job(AlertService.generate_alerts, 'interval', hours=24, id='generate_alerts')
    scheduler.start()
