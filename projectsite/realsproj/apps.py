from django.apps import AppConfig
import os


class RealsprojConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'realsproj'
    
    def ready(self):
        import realsproj.signals
        
        # Auto-start the expiration check scheduler
        # This will run automatically when Django starts
        if os.environ.get('RUN_MAIN') == 'true':  # Prevent duplicate scheduler in dev mode
            from realsproj.scheduler import start_scheduler
            start_scheduler() 
