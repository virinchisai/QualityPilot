import { expect, test } from "@playwright/test";
import { LoginPage } from "../pages/login.page";
import { DashboardPage } from "../pages/dashboard.page";

const user = {
  email: `pw-${Date.now()}@example.com`,
  password: "StrongPass!123",
  display_name: "PW User",
};

test.beforeAll(async ({ request }) => {
  const response = await request.post("/api/register", { data: user });
  expect([201, 409]).toContain(response.status());
});

test("valid login, profile update, and logout", async ({ page }) => {
  const login = new LoginPage(page);
  await login.goto();
  await login.login(user.email, user.password);
  const dashboard = new DashboardPage(page);
  await dashboard.expectLoaded();
  await dashboard.updateName("Updated by Playwright");
  await dashboard.logout();
  await expect(page).toHaveURL("/");
});

test("invalid login and form validation", async ({ page }) => {
  const login = new LoginPage(page);
  await login.goto();
  await login.login(user.email, "wrong-password");
  await login.expectError();
  await page.getByLabel("Email").fill("not-an-email");
  await page.getByRole("button", { name: "Sign in" }).click();
  await expect(page.getByLabel("Email")).toHaveAttribute("type", "email");
});

test("protected dashboard redirects without session", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page).toHaveURL("/");
});

test("standard user has no admin navigation", async ({ page }) => {
  const login = new LoginPage(page);
  await login.goto();
  await login.login(user.email, user.password);
  await expect(
    page.getByRole("heading", { name: "Administration" }),
  ).toBeHidden();
});

test("session expiration clears invalid access token", async ({ page }) => {
  await page.goto("/");
  await page.evaluate(() =>
    sessionStorage.setItem("access_token", "expired.invalid.token"),
  );
  await page.goto("/dashboard");
  await expect(page).toHaveURL("/");
});

test("responsive layout has no horizontal overflow", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  expect(
    await page.evaluate(
      () =>
        document.documentElement.scrollWidth <=
        document.documentElement.clientWidth,
    ),
  ).toBeTruthy();
});

test("intentional flaky timing demo", async ({ page }) => {
  test.skip(
    process.env.QUALITYPILOT_FLAKY_DEMO !== "true",
    "opt-in demonstration only",
  );
  await page.goto("/");
  await expect(page.getByRole("heading")).toBeVisible({
    timeout: 10 + Math.floor(Math.random() * 50),
  });
});
