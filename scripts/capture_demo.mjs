#!/usr/bin/env node
/** Capture a reproducible README demo GIF from the running local dashboard. */

import { execFileSync } from "node:child_process";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

import { chromium } from "@playwright/test";

const dashboardUrl =
  process.env.QUALITYPILOT_DASHBOARD_URL ?? "http://127.0.0.1:8501";
const output = resolve("docs/assets/qualitypilot-demo.gif");
const frames = mkdtempSync(join(tmpdir(), "qualitypilot-demo-"));
const browser = await chromium.launch({ headless: true });
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

async function frame(number) {
  await page.screenshot({
    path: join(frames, `frame-${String(number).padStart(2, "0")}.png`),
  });
}

try {
  await page.goto(dashboardUrl, { waitUntil: "networkidle" });
  await page.getByRole("heading", { name: "QualityPilot TestOps" }).waitFor();
  await page.getByText("Total", { exact: true }).waitFor();
  await frame(1);

  await page.getByRole("tab", { name: "Requirement Lab" }).click();
  await page.getByRole("button", { name: "Generate validated tests" }).click();
  await page
    .getByRole("button", { name: "Download QualityPilot JSON" })
    .waitFor();
  await frame(2);

  await page.getByRole("tab", { name: "Traceability" }).click();
  await page
    .getByRole("heading", { name: "Requirements traceability matrix" })
    .waitFor();
  await frame(3);

  await page.getByRole("tab", { name: "Demo Console" }).click();
  await page
    .getByRole("button", { name: "Analyze and generate defect" })
    .click();
  await page.getByText("and persisted").waitFor();
  await frame(4);

  await page.getByRole("tab", { name: "Release Gate" }).click();
  await page.getByRole("button", { name: "Evaluate release" }).click();
  await page.getByText("Release approved at 100.0% pass rate").waitFor();
  await frame(5);
} finally {
  await browser.close();
}

execFileSync(
  "ffmpeg",
  [
    "-y",
    "-framerate",
    "0.4",
    "-i",
    join(frames, "frame-%02d.png"),
    "-vf",
    "fps=10,scale=1200:-1:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer",
    output,
  ],
  { stdio: "inherit" },
);

console.log(`Wrote ${output}`);
