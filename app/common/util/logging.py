import logging
from os import getenv

import sentry_sdk
from dotenv import load_dotenv
from sentry_sdk.integrations.logging import LoggingIntegration

load_dotenv()

SENTRY_DSN = getenv("SENTRY_DSN", None)
ENVIRONMENT = getenv("ENVIRONMENT", None)

sentry_logging = LoggingIntegration(level=logging.INFO, event_level=logging.ERROR)

if ENVIRONMENT == "prod":
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[sentry_logging],
        traces_sample_rate=1.0,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

