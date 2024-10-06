import logging
import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration
from os import getenv
from dotenv import load_dotenv

load_dotenv()

SENTRY_DSN = getenv("SENTRY_DSN", None)
ENVIRONMENT = getenv("ENVIRONMENT", None)

sentry_logging = LoggingIntegration(
    level=logging.INFO,  
    event_level=logging.ERROR 
)

if ENVIRONMENT == "prod":
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[sentry_logging],
        traces_sample_rate=1.0,
    )

logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()  
    ]
)

logger = logging.getLogger(__name__)
