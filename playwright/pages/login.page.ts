import { expect, type Page } from "@playwright/test";

export class LoginPage {
  constructor(private readonly page: Page) {}
  async goto() {
    await this.page.goto("/");
  }
  async login(email: string, password: string) {
    await this.page.getByLabel("Email").fill(email);
    await this.page.getByLabel("Password").fill(password);
    await this.page.getByRole("button", { name: "Sign in" }).click();
  }
  async expectError() {
    await expect(this.page.getByRole("alert")).toHaveText(
      "Invalid email or password",
    );
  }
}
