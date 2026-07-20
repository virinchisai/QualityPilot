"""One executable Selenium login smoke test for legacy-suite compatibility."""

import json
import os
import time
import urllib.request

import pytest

webdriver = pytest.importorskip("selenium.webdriver")
from selenium.webdriver.common.by import By  # noqa: E402
from selenium.webdriver.support import expected_conditions as conditions  # noqa: E402
from selenium.webdriver.support.ui import WebDriverWait  # noqa: E402

pytestmark = [
    pytest.mark.selenium,
    pytest.mark.skipif(
        os.getenv("SELENIUM_COMPATIBILITY") != "true",
        reason="set SELENIUM_COMPATIBILITY=true for the opt-in legacy smoke suite",
    ),
]


def register(base_url: str, email: str, password: str) -> None:
    request = urllib.request.Request(
        f"{base_url}/api/register",
        data=json.dumps(
            {"email": email, "password": password, "display_name": "Selenium User"}
        ).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        assert response.status == 201


def test_valid_login_smoke():
    base_url = os.getenv("DEMO_APP_URL", "http://127.0.0.1:8000")
    email = f"selenium-{time.time_ns()}@example.com"
    password = "StrongPass!123"
    register(base_url, email, password)

    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(base_url)
        driver.find_element(By.ID, "email").send_keys(email)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.ID, "login-button").click()
        WebDriverWait(driver, 10).until(conditions.url_contains("/dashboard"))
        heading = WebDriverWait(driver, 10).until(
            conditions.visibility_of_element_located((By.TAG_NAME, "h1"))
        )
        assert heading.text == "User dashboard"
    finally:
        driver.quit()
