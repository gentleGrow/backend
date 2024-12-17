import json

from dotenv import find_dotenv, load_dotenv

from app.common.util.aws_s3 import AwsFileReader
from app.data.common.config import (
    BILL_ACKMAN_FILEPATH,
    DAVID_TEPPER_FILEPATH,
    GEORGE_SOROS_FILEPATH,
    JOHN_PAULSON_FILEPATH,
    NELSON_PELTZ_FILEPATH,
    RAY_DAILO_FILEPATH,
    RICH_PORTFOLIO_FILEPATH,
    WARREN_BUFFETT_FILEPATH,
)
from app.module.asset.enum import RichPeople

load_dotenv(find_dotenv())


class RichPortfolioFileReader:
    @classmethod
    def get_rich_portfolio_object_bundle(cls) -> dict[RichPeople, dict]:
        warren_buffett_object = cls._read_rich_portfolio_file(
            AwsFileReader._get_path(WARREN_BUFFETT_FILEPATH, RICH_PORTFOLIO_FILEPATH)
        )
        bill_ackman_object = cls._read_rich_portfolio_file(
            AwsFileReader._get_path(BILL_ACKMAN_FILEPATH, RICH_PORTFOLIO_FILEPATH)
        )
        ray_dailo_object = cls._read_rich_portfolio_file(
            AwsFileReader._get_path(RAY_DAILO_FILEPATH, RICH_PORTFOLIO_FILEPATH)
        )
        nelson_peltz_object = cls._read_rich_portfolio_file(
            AwsFileReader._get_path(NELSON_PELTZ_FILEPATH, RICH_PORTFOLIO_FILEPATH)
        )
        john_paulson_object = cls._read_rich_portfolio_file(
            AwsFileReader._get_path(JOHN_PAULSON_FILEPATH, RICH_PORTFOLIO_FILEPATH)
        )
        george_soros_object = cls._read_rich_portfolio_file(
            AwsFileReader._get_path(GEORGE_SOROS_FILEPATH, RICH_PORTFOLIO_FILEPATH)
        )
        david_tepper_object = cls._read_rich_portfolio_file(
            AwsFileReader._get_path(DAVID_TEPPER_FILEPATH, RICH_PORTFOLIO_FILEPATH)
        )

        return {
            RichPeople.WARRENBUFFETT: warren_buffett_object,
            RichPeople.BILLACKMAN: bill_ackman_object,
            RichPeople.RAYDALIO: ray_dailo_object,
            RichPeople.NELSONPELTZ: nelson_peltz_object,
            RichPeople.JOHNPAULSON: john_paulson_object,
            RichPeople.GEORGESOROS: george_soros_object,
            RichPeople.DAVIDTEPPER: david_tepper_object,
        }

    @classmethod
    def _read_rich_portfolio_file(cls, filepath: str):
        with open(filepath, "r", encoding="utf-8") as file:
            return json.load(file)
