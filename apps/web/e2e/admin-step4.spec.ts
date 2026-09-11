import { expect, test, type Page, type Route } from "@playwright/test";

const ADMIN_ID = "11111111-1111-1111-1111-111111111111";
const OTHER_ADMIN_ID = "33333333-3333-3333-3333-333333333333";
const REPORT_ID = "22222222-2222-2222-2222-222222222222";
const CONTACT_ID = "44444444-4444-4444-4444-444444444444";

const ADMIN_PROFILE = {
  id: ADMIN_ID,
  full_name: "Ada Okonkwo",
  role: "hoh",
  subunit: null,
  permissions: [
    "view",
    "respond",
    "assign",
    "close",
    "export",
    "manage_admins",
    "manage_categories",
    "manage_escalation_contacts",
  ],
};

function baseReport(overrides: Record<string, unknown> = {}) {
  return {
    id: REPORT_ID,
    source: "web",
    report_type: "complaint",
    reported_member_name: "Someone else",
    reported_member_admin_id: null,
    description: "Playwright admin verification report.",
    severity: "medium",
    status: "under_review",
    assigned_admin_id: null,
    created_at: "2026-09-01T10:00:00Z",
    updated_at: "2026-09-01T10:00:00Z",
    ...overrides,
  };
}

async function seedAdminSession(page: Page) {
  await page.addInitScript(() => {
    sessionStorage.setItem("hospi_admin_access_token", "mock-admin-token");
    sessionStorage.setItem("hospi_admin_refresh_token", "mock-admin-refresh");
    sessionStorage.setItem("hospi_admin_expires_at", "2099-01-01T00:00:00.000Z");
  });
}

async function fulfillJson(route: Route, status: number, body: unknown) {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

async function mockAdminApi(
  page: Page,
  options: {
    reportOverrides?: Record<string, unknown>;
    statusHandler?: (route: Route) => Promise<void>;
    trackCalls?: string[];
    reportState?: { current: ReturnType<typeof baseReport> };
  } = {},
) {
  const reportState = options.reportState ?? { current: baseReport(options.reportOverrides) };
  if (options.reportOverrides) {
    reportState.current = baseReport(options.reportOverrides);
  }

  await page.route("**/api/admin/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;

    if (path.endsWith("/api/admin/me")) {
      await fulfillJson(route, 200, { data: ADMIN_PROFILE });
      return;
    }
    if (path.endsWith("/api/admin/team")) {
      await fulfillJson(route, 200, {
        data: [
          {
            id: OTHER_ADMIN_ID,
            full_name: "Backup Admin",
            role: "asst_head",
          },
        ],
      });
      return;
    }
    if (path.endsWith("/api/admin/escalation-contacts")) {
      await fulfillJson(route, 200, {
        data: [{ id: CONTACT_ID, name: "Duty Manager", role_label: "On call", active: true }],
      });
      return;
    }
    if (path.endsWith("/api/admin/dashboard/stats")) {
      await fulfillJson(route, 200, {
        data: {
          total_reports: 1,
          by_status: { under_review: 1 },
          by_category: { complaint: 1 },
          by_subunit: { general: 1 },
          oldest_unresolved_days: 2,
          average_resolution_hours: 12,
        },
      });
      return;
    }
    if (path.endsWith("/api/admin/login")) {
      await fulfillJson(route, 200, {
        access_token: "mock-admin-token",
        refresh_token: "mock-admin-refresh",
        expires_at: "2099-01-01T00:00:00.000Z",
      });
      return;
    }
    if (path.endsWith("/api/admin/reports") && route.request().method() === "GET") {
      await fulfillJson(route, 200, { data: [reportState.current] });
      return;
    }
    if (path.endsWith(`/api/admin/reports/${REPORT_ID}`) && route.request().method() === "GET") {
      await fulfillJson(route, 200, {
        report: reportState.current,
        messages: [],
        internal_notes: [],
      });
      return;
    }
    if (path.endsWith(`/api/admin/reports/${REPORT_ID}/assign`)) {
      options.trackCalls?.push("assign");
      reportState.current = baseReport({ ...reportState.current, status: "assigned" });
      await fulfillJson(route, 200, { data: reportState.current });
      return;
    }
    if (path.endsWith(`/api/admin/reports/${REPORT_ID}/message`)) {
      options.trackCalls?.push("message");
      await fulfillJson(route, 200, {
        data: {
          id: "msg-1",
          content: "Following up with the reporter.",
          created_at: "2026-09-09T10:00:00Z",
        },
      });
      return;
    }
    if (path.endsWith(`/api/admin/reports/${REPORT_ID}/escalate`)) {
      options.trackCalls?.push("escalate");
      await fulfillJson(route, 200, {
        data: {
          report: baseReport({ status: "escalated" }),
          escalation: { id: "esc-1" },
        },
      });
      return;
    }
    if (path.endsWith(`/api/admin/reports/${REPORT_ID}/status`) && options.statusHandler) {
      await options.statusHandler(route);
      return;
    }
    if (path.endsWith(`/api/admin/reports/${REPORT_ID}/status`)) {
      options.trackCalls?.push("close");
      reportState.current = baseReport({ ...reportState.current, status: "closed" });
      await fulfillJson(route, 200, { data: reportState.current });
      return;
    }

    await fulfillJson(route, 404, {
      error: { code: "not_found", message: `Unmocked admin route: ${path}` },
    });
  });
}

async function waitForAdminShell(page: Page) {
  await expect(page.getByRole("navigation")).toBeVisible({ timeout: 15000 });
}

async function openReportDetail(page: Page) {
  await page.goto(`/admin/reports/${REPORT_ID}`);
  await waitForAdminShell(page);
  await expect(page.getByRole("heading", { name: /complaint/i })).toBeVisible({
    timeout: 15000,
  });
}

test.describe("Step 4 admin UI verification", () => {
  test("authenticated session lands on dashboard", async ({ page }) => {
    await seedAdminSession(page);
    await mockAdminApi(page);

    await page.goto("/admin/dashboard");
    await waitForAdminShell(page);
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible({
      timeout: 15000,
    });
  });

  test("login form hydrates session and lands on dashboard", async ({ page }) => {
    await mockAdminApi(page);

    await page.goto("/admin/login");
    await page.getByLabel(/^Email/).fill("admin@example.test");
    await page.getByLabel(/^Password/).fill("Test123!");
    await page.getByRole("button", { name: "Sign in" }).click();

    await expect(page).toHaveURL(/\/admin\/dashboard$/, { timeout: 15000 });
    await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible({
      timeout: 15000,
    });
  });

  test("recusal block surfaces in report detail UI", async ({ page }) => {
    await seedAdminSession(page);
    await mockAdminApi(page, {
      reportOverrides: {
        reported_member_name: "Ada Okonkwo",
        reported_member_admin_id: ADMIN_ID,
      },
      statusHandler: async (route) => {
        await fulfillJson(route, 409, {
          error: {
            code: "recusal_blocked",
            message: "You cannot act on a report that names you.",
          },
        });
      },
    });

    await openReportDetail(page);
    await page.getByRole("button", { name: "closed" }).click();
    await expect(
      page.getByRole("alert").filter({ hasText: /cannot act on a report/i }),
    ).toBeVisible();
    await expect(page.getByRole("dialog")).toHaveCount(0);
  });

  test("recusal warn requires confirmation dialog in UI", async ({ page }) => {
    let confirmSeen = false;
    const reportState = { current: baseReport() };
    await seedAdminSession(page);
    await mockAdminApi(page, {
      reportState,
      reportOverrides: {
        reported_member_name: "Complaint about ada during hall meeting",
        reported_member_admin_id: null,
      },
      statusHandler: async (route) => {
        const body = route.request().postDataJSON() as {
          confirm_recusal_override?: boolean;
        };
        if (!confirmSeen && !body.confirm_recusal_override) {
          await fulfillJson(route, 409, {
            error: {
              code: "recusal_confirmation_required",
              message: "This report may name you. Confirm to continue.",
            },
          });
          return;
        }
        confirmSeen = true;
        reportState.current = baseReport({
          ...reportState.current,
          status: "closed",
        });
        await fulfillJson(route, 200, { data: reportState.current });
      },
    });

    await openReportDetail(page);
    await page.getByRole("button", { name: "closed" }).click();
    await expect(page.getByRole("dialog", { name: /Recusal warning/i })).toBeVisible();
    await page.getByRole("button", { name: "Confirm override" }).click();
    await expect(page.getByRole("dialog")).toHaveCount(0);
    await expect(page.getByText("Status:")).toContainText("closed");
  });

  test("admin lifecycle actions call expected endpoints", async ({ page }) => {
    const called: string[] = [];
    await seedAdminSession(page);
    await mockAdminApi(page, { trackCalls: called });

    await openReportDetail(page);
    await page.locator("select").first().selectOption(OTHER_ADMIN_ID);
    await page.getByRole("button", { name: "Assign report" }).click();
    await page.getByPlaceholder("Reply to reporter").fill("Following up with the reporter.");
    await page.getByRole("button", { name: "Send" }).click();
    await page.locator("select").nth(2).selectOption(CONTACT_ID);
    await page.getByRole("button", { name: "Escalate report" }).click();
    await page.getByRole("button", { name: "closed" }).click();

    await expect.poll(() => called).toEqual(["assign", "message", "escalate", "close"]);
  });
});
