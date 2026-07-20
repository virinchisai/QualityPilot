import { expect, type Page } from "@playwright/test";

export class DashboardPage {
  constructor(private readonly page: Page) {}
  async expectLoaded() {
    await expect(
      this.page.getByRole("heading", { name: "User dashboard" }),
    ).toBeVisible();
  }
  async updateName(name: string) {
    await this.page.getByLabel("Display name").fill(name);
    await this.page.getByRole("button", { name: "Save profile" }).click();
    await expect(this.page.getByRole("alert")).toHaveText("Profile updated");
  }
  async logout() {
    await this.page.getByRole("button", { name: "Log out" }).click();
  }
}
