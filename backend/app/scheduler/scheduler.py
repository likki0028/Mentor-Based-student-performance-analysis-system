
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from ..services.alert_service import AlertService
from ..services.attendance_reminder import check_and_remind_attendance

scheduler = BackgroundScheduler()

def start_scheduler():
    """Start the background scheduler for periodic tasks."""
    # Existing: Generate low-attendance / low-marks alerts every 24 hours
    scheduler.add_job(AlertService.generate_alerts, 'interval', hours=24, id='generate_alerts')

    # NEW: Send attendance reminder emails daily at 2:00 PM IST
    scheduler.add_job(
        check_and_remind_attendance,
        CronTrigger(hour=14, minute=0),  # 2:00 PM
        id='attendance_reminder',
        replace_existing=True
    )

    scheduler.start()
