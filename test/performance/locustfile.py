from os import getenv

from dotenv import load_dotenv
from locust import HttpUser, task

load_dotenv()

STRESS_TEST_USER_TOKEN = getenv("STRESS_TEST_USER_TOKEN", None)


class FastAPIUser(HttpUser):
    @task
    def test_api(self):
        headers = {"Authorization": f"Bearer {STRESS_TEST_USER_TOKEN}"}
        self.client.get("http://localhost:8000/api/asset/v1/asset-field", headers=headers)
        self.client.get("http://localhost:8000/api/asset/v1/assetstock", headers=headers)
        self.client.get("http://localhost:8000/api/chart/v1/asset-save-trend", headers=headers)
        self.client.get("http://localhost:8000/api/chart/v1/estimate-dividend", headers=headers)
        self.client.get("http://localhost:8000/api/chart/v1/composition", headers=headers)
        self.client.get("http://localhost:8000/api/chart/v1/performance-analysis", headers=headers)
        self.client.get("http://localhost:8000/api/chart/v1/my-stock", headers=headers)
        self.client.get("http://localhost:8000/api/chart/v1/indice", headers=headers)
        self.client.get("http://localhost:8000/api/chart/v1/rich-portfolio", headers=headers)
        self.client.get("http://localhost:8000/api/chart/v1/rich-pick", headers=headers)
        self.client.get("http://localhost:8000/api/chart/v1/people-portfolio", headers=headers)
        self.client.get("http://localhost:8000/api/chart/v1/tip", headers=headers)
