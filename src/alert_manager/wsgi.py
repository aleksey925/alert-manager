from alert_manager.config import get_config
from alert_manager.main import app_factory

app = app_factory(config=get_config())
