import { mkdir } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { chromium } from "@playwright/test";

const __dirname = dirname(fileURLToPath(import.meta.url));
const outputDir = resolve(__dirname, "../../docs/screenshots");
const baseUrl = process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:5173";

await mkdir(outputDir, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 1100 }, deviceScaleFactor: 1 });

await page.goto(baseUrl);
await page.screenshot({ path: resolve(outputDir, "generate-page.png"), fullPage: true });

await page.getByLabel("Title").fill("Checkout discount validation");
await page.getByLabel("Requirement / User Story").fill(
  "As a shopper, I want to apply a valid discount code during checkout so that my order total is reduced.",
);
await page.getByLabel("Acceptance Criteria").fill(
  "Valid discount codes reduce the order total. Expired codes show an error. Discount totals are visible before payment.",
);
await page.getByLabel("API Notes / Payload Notes").fill(
  "POST /api/checkout/discount with code and cartId. Returns adjustedTotal and discountAmount.",
);
await page.getByLabel("Feature Area").fill("Checkout");
await page.getByLabel("Supporting docs / API notes / product context").fill(
  "Discount service rejects expired codes before payment and records rejection reasons for audit review.",
);
await page.getByRole("button", { name: "Generate QA Output" }).click();
await page.getByRole("heading", { name: "Checkout discount validation", exact: true }).waitFor();
await page.screenshot({ path: resolve(outputDir, "results-page.png"), fullPage: true });

await page.getByRole("button", { name: "Evals" }).click();
await page.getByRole("button", { name: "Run Evals" }).click();
await page.getByText("Payment API Requirement").waitFor();
await page.screenshot({ path: resolve(outputDir, "eval-dashboard.png"), fullPage: true });

await browser.close();
