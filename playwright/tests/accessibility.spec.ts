import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

test("login has no automatically detectable critical violations", async ({
  page,
}) => {
  await page.goto("/");
  const result = await new AxeBuilder({ page }).analyze();
  expect(
    result.violations.filter((v) =>
      ["critical", "serious"].includes(v.impact ?? ""),
    ),
  ).toEqual([]);
});

test("login visual baseline", async ({ page }) => {
  test.skip(!process.env.VISUAL_TESTS, "opt-in until baseline is approved");
  await page.goto("/");
  await expect(page).toHaveScreenshot("login-page.png", { fullPage: true });
});
