"""Small working load profile: locust -f tests/load/locustfile.py --headless -u 10 -r 2 -t 30s."""

from locust import HttpUser, between, task


class HealthAndLoginUser(HttpUser):
    wait_time = between(0.2, 1)

    @task(4)
    def health(self):
        self.client.get("/health")

    @task(1)
    def invalid_login(self):
        self.client.post("/api/login", json={"email": "load@example.com", "password": "invalid"})
