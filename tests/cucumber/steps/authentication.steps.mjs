import assert from "node:assert/strict";

import { Given, Then, When } from "@cucumber/cucumber";

const baseUrl = process.env.DEMO_APP_URL ?? "http://127.0.0.1:8000";
const password = "StrongPass!123";

Given("the demo API is healthy", async function () {
  const response = await fetch(`${baseUrl}/health`);
  assert.equal(response.status, 200);
});

Given("a unique registered Cucumber user", async function () {
  this.email = `cucumber-${Date.now()}-${Math.random().toString(16).slice(2)}@example.com`;
  const response = await fetch(`${baseUrl}/api/register`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      email: this.email,
      password,
      display_name: "Cucumber User",
    }),
  });
  assert.equal(response.status, 201);
});

When("the Cucumber user submits valid credentials", async function () {
  this.response = await fetch(`${baseUrl}/api/login`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ email: this.email, password }),
  });
  this.tokens = await this.response.json();
});

Then("access and refresh tokens are returned by the API", function () {
  assert.equal(this.response.status, 200);
  assert.ok(this.tokens.access_token);
  assert.ok(this.tokens.refresh_token);
});

When("the Cucumber user logs in and requests admin audit", async function () {
  const login = await fetch(`${baseUrl}/api/login`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ email: this.email, password }),
  });
  const tokens = await login.json();
  this.response = await fetch(`${baseUrl}/api/admin/audit`, {
    headers: { authorization: `Bearer ${tokens.access_token}` },
  });
});

Then("the Cucumber user receives forbidden", function () {
  assert.equal(this.response.status, 403);
});
