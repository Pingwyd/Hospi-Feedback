import { expect, test } from "@playwright/test";

const ACCESS_CODE = "unit-test-access-code-fixture";
const TICKET_CODE = "ABCD2345";

function mockReporterApi(page: import("@playwright/test").Page) {
  return Promise.all([
    page.route("**/api/access/verify", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        headers: {
          "Set-Cookie":
            "hospi_access_session=mock-session-token; Path=/; HttpOnly; SameSite=Lax",
        },
        body: JSON.stringify({
          expires_at: "2026-09-04T12:00:00Z",
          session_token: null,
        }),
      });
    }),
    page.route("**/api/_phase2/public-ping", async (route) => {
      const cookie = route.request().headers()["cookie"] ?? "";
      if (!cookie.includes("hospi_access_session")) {
        await route.fulfill({
          status: 401,
          contentType: "application/json",
          body: JSON.stringify({
            error: { code: "unauthorized", message: "Access session required." },
          }),
        });
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ ok: true }),
      });
    }),
    page.route("**/api/reports", async (route) => {
      if (route.request().method() !== "POST") {
        await route.continue();
        return;
      }
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({
          ticket_code: TICKET_CODE,
          status: "new",
          created_at: "2026-09-03T12:00:00Z",
        }),
      });
    }),
    page.route(`**/api/reports/ticket/${TICKET_CODE}`, async (route) => {
      if (route.request().method() !== "GET") {
        await route.continue();
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          status: "new",
          report_type: "complaint",
          description: "Playwright verification report.",
          reported_member_name: null,
          severity: null,
          created_at: "2026-09-03T12:00:00Z",
          updated_at: "2026-09-03T12:00:00Z",
          messages: [],
        }),
      });
    }),
  ]);
}

test.describe("Step 4 reporter UI verification", () => {
  test("wax seal hides ticket code until explicit interaction", async ({ page }) => {
    await mockReporterApi(page);
    await page.context().addCookies([
      {
        name: "hospi_access_session",
        value: "mock-session-token",
        url: "http://127.0.0.1:3000",
      },
    ]);

    await page.goto("/report");
    await expect(page.getByRole("heading", { name: "Submit a report" })).toBeVisible();

    await page.getByLabel(/^Description/).fill("Playwright verification report.");
    await page.getByRole("checkbox").check();
    await page.getByRole("button", { name: "Submit report" }).click();

    await expect(page.getByRole("heading", { name: "Report received" })).toBeVisible();
    await expect(page.getByTestId("revealed-ticket-code")).toHaveCount(0);
    await expect(page.getByText(TICKET_CODE)).toHaveCount(0);

    await page.getByRole("button", { name: /Break the wax seal/i }).click();

    await expect(page.getByTestId("revealed-ticket-code")).toHaveText(TICKET_CODE);
    await expect(page.getByRole("link", { name: new RegExp(TICKET_CODE) })).toBeVisible();
  });

  test("report page redirects when session cookie is cleared", async ({ page }) => {
    await mockReporterApi(page);
    await page.context().addCookies([
      {
        name: "hospi_access_session",
        value: "mock-session-token",
        url: "http://127.0.0.1:3000",
      },
    ]);

    await page.goto("/report");
    await expect(page.getByRole("heading", { name: "Submit a report" })).toBeVisible();

    await page.context().clearCookies();
    await page.goto("/report");
    await expect(page).toHaveURL(/\/access$/);
    await expect(page.getByRole("heading", { name: "Unit access" })).toBeVisible();
  });

  test("status page loads ticket thread after submit flow link", async ({ page }) => {
    await mockReporterApi(page);
    await page.context().addCookies([
      {
        name: "hospi_access_session",
        value: "mock-session-token",
        url: "http://127.0.0.1:3000",
      },
    ]);

    await page.goto(`/status/${TICKET_CODE}`);
    await expect(page.getByRole("heading", { level: 1 })).toContainText(TICKET_CODE);
    await expect(page.getByText("Playwright verification report.")).toBeVisible();
  });
});
