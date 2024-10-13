import logging
from os import getenv

import sentry_sdk
from dotenv import load_dotenv
from sentry_sdk.integrations.logging import LoggingIntegration

from database.enum import EnvironmentType

load_dotenv()

SENTRY_DSN = getenv("SENTRY_DSN", None)
ENVIRONMENT = getenv("ENVIRONMENT", None)
if ENVIRONMENT == EnvironmentType.PROD:
    sentry_logging = LoggingIntegration(level=logging.ERROR, event_level=logging.ERROR)

    sentry_sdk.init(dsn=SENTRY_DSN, integrations=[sentry_logging], traces_sample_rate=1.0)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )
else:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
