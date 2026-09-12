import { expect, test, type Page, type Route } from "@playwright/test";

const ADMIN_ID = "11111111-1111-1111-1111-111111111111";
const REPORT_ID = "22222222-2222-2222-2222-222222222222";

const ADMIN_PROFILE = {
  id: ADMIN_ID,
  full_name: "Ada Okonkwo",
  role: "hoh",
  subunit: null,
  permissions: ["view", "respond", "assign", "close", "export"],
};

function baseReport() {
  return {
    id: REPORT_ID,
    source: "web",
    report_type: "complaint",
    reported_member_name: "Someone else",
    reported_member_admin_id: null,
    description: "Theme verification report.",
    severity: "medium",
    status: "under_review",
    assigned_admin_id: null,
    created_at: "2026-09-01T10:00:00Z",
    updated_at: "2026-09-01T10:00:00Z",
  };
}

async function fulfillJson(route: Route, status: number, body: unknown) {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

async function mockAdminReportDetail(page: Page) {
  await page.addInitScript(() => {
    sessionStorage.setItem("hospi_admin_access_token", "mock-admin-token");
    sessionStorage.setItem("hospi_admin_refresh_token", "mock-admin-refresh");
    sessionStorage.setItem("hospi_admin_expires_at", "2099-01-01T00:00:00.000Z");
  });

  await page.route("**/api/admin/**", async (route) => {
    const path = new URL(route.request().url()).pathname;

    if (path.endsWith("/api/admin/me")) {
      await fulfillJson(route, 200, { data: ADMIN_PROFILE });
      return;
    }
    if (path.endsWith("/api/admin/team")) {
      await fulfillJson(route, 200, { data: [] });
      return;
    }
    if (path.endsWith("/api/admin/escalation-contacts")) {
      await fulfillJson(route, 200, { data: [] });
      return;
    }
    if (path.endsWith(`/api/admin/reports/${REPORT_ID}`)) {
      await fulfillJson(route, 200, {
        report: baseReport(),
        messages: [],
        internal_notes: [],
      });
      return;
    }
    await fulfillJson(route, 404, {
      error: { code: "not_found", message: `Unmocked admin route: ${path}` },
    });
  });
}

async function setTheme(page: Page, theme: "light" | "dark") {
  await page.evaluate((value) => {
    localStorage.setItem("hospi-theme", value);
    document.documentElement.setAttribute("data-theme", value);
  }, theme);
}

async function seedTheme(page: Page, theme: "light" | "dark") {
  await page.addInitScript((value) => {
    localStorage.setItem("hospi-theme", value);
    document.documentElement.setAttribute("data-theme", value);
  }, theme);
}

async function openReportDetail(page: Page) {
  await page.goto(`/admin/reports/${REPORT_ID}`);
  await expect(page.getByRole("navigation")).toBeVisible({ timeout: 15000 });
  await expect(page.getByRole("heading", { name: /complaint/i })).toBeVisible({
    timeout: 15000,
  });
}

test.describe("BL-011 dark mode component screenshots", () => {
  test("capture BL-005/006/009 patterns in light and dark", async ({ page }) => {
    test.setTimeout(60_000);
    await mockAdminReportDetail(page);
    await seedTheme(page, "light");
    await openReportDetail(page);

    await page.screenshot({
      path: "test-results/theme-step2-status-picker-light.png",
    });

    await page.getByRole("button", { name: "Change status to closed" }).click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await page.screenshot({
      path: "test-results/theme-step2-admin-confirm-light.png",
    });
    await page.getByRole("button", { name: "Cancel" }).click();

    await page.getByRole("button", { name: "Delete and archive" }).click();
    await expect(page.getByText("Delete reason is required.")).toBeVisible();
    await page.screenshot({
      path: "test-results/theme-step2-delete-error-light.png",
    });

    await seedTheme(page, "dark");
    await page.reload();
    await expect(page.getByRole("heading", { name: /complaint/i })).toBeVisible({
      timeout: 15000,
    });
    await page.screenshot({
      path: "test-results/theme-step2-status-picker-dark.png",
    });

    await page.getByRole("button", { name: "Change status to closed" }).click();
    await expect(page.getByRole("dialog")).toBeVisible();
    await page.screenshot({
      path: "test-results/theme-step2-admin-confirm-dark.png",
    });
    await page.getByRole("button", { name: "Cancel" }).click();

    await page.getByRole("button", { name: "Delete and archive" }).click();
    await expect(page.getByText("Delete reason is required.")).toBeVisible();
    await page.screenshot({
      path: "test-results/theme-step2-delete-error-dark.png",
    });
  });
});
