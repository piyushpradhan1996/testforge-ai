import { expect, test } from "@playwright/test";

test("generates QA output and runs eval dashboard", async ({ page }) => {
  await page.goto("/");

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
  await page.getByLabel("Supporting docs / API notes / product context").fill(
    "Discount service rejects expired codes before payment and records rejection reasons for audit review.",
  );

  await page.getByRole("button", { name: "Generate QA Output" }).click();

  await expect(page.getByRole("heading", { name: "Checkout discount validation", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Positive Test Cases" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Retrieved Context" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Guardrail Result" })).toBeVisible();

  await page.getByRole("button", { name: "Evals" }).click();
  await page.getByRole("button", { name: "Run Evals" }).click();

  await expect(page.getByText("Payment API Requirement")).toBeVisible();
  await expect(page.getByText("%").first()).toBeVisible();
});
