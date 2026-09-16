import { expect, test, type Page, type Route } from "@playwright/test";

const ADMIN_PROFILE = {
  id: "11111111-1111-1111-1111-111111111111",
  full_name: "Ada Okonkwo",
  role: "hoh",
  subunit: null,
  permissions: ["view", "respond", "export"],
};

const SAMPLE_REPORT = {
  id: "22222222-2222-2222-2222-222222222222",
  report_type: "complaint",
  reported_member_name: "Someone",
  severity: "high",
  status: "new",
  created_at: "2026-01-15T10:00:00Z",
};

async function fulfillJson(route: Route, status: number, body: unknown) {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

async function seedAdminSession(page: Page) {
  await page.addInitScript(() => {
    sessionStorage.setItem("hospi_admin_access_token", "mock-admin-token");
    sessionStorage.setItem("hospi_admin_refresh_token", "mock-admin-refresh");
    sessionStorage.setItem("hospi_admin_expires_at", "2099-01-01T00:00:00.000Z");
  });
}

async function mockInboxApi(
  page: Page,
  options: { onListRequest?: (url: URL) => void } = {},
) {
  await page.route("**/api/admin/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;

    if (path.endsWith("/api/admin/me")) {
      await fulfillJson(route, 200, { data: ADMIN_PROFILE });
      return;
    }
    if (
      path.endsWith("/api/admin/reports") &&
      route.request().method() === "GET"
    ) {
      options.onListRequest?.(url);
      await fulfillJson(route, 200, { data: [SAMPLE_REPORT] });
      return;
    }
    await fulfillJson(route, 404, {
      error: { code: "not_found", message: "Unhandled mock route." },
    });
  });
}

test.describe("Admin inbox filters (BL-002 extension)", () => {
  test("URL query restores and maps to list API params", async ({ page }) => {
    await seedAdminSession(page);
    const listUrls: URL[] = [];
    await mockInboxApi(page, {
      onListRequest: (url) => listUrls.push(new URL(url)),
    });

    const filterPath =
      "/admin/reports?status=new&q=welfare&type=complaint&severity=high" +
      "&from=2026-01-01&to=2026-01-31";

    await page.goto(filterPath);
    await expect(page.getByRole("heading", { name: "Report inbox" })).toBeVisible();

    await expect.poll(() => listUrls.length).toBeGreaterThan(0);
    const apiUrl = listUrls[listUrls.length - 1]!;
    expect(apiUrl.searchParams.get("status")).toBe("new");
    expect(apiUrl.searchParams.get("keyword")).toBe("welfare");
    expect(apiUrl.searchParams.get("report_type")).toBe("complaint");
    expect(apiUrl.searchParams.get("severity")).toBe("high");
    expect(apiUrl.searchParams.get("created_from")).toBe("2026-01-01T00:00:00.000Z");
    expect(apiUrl.searchParams.get("created_to")).toBe("2026-01-31T23:59:59.999Z");

    await page.goto("about:blank");
    await page.goto(filterPath);
    await expect.poll(() => listUrls.length).toBeGreaterThan(1);
    expect(page.url()).toContain("type=complaint");
    expect(page.url()).toContain("from=2026-01-01");
  });

  test("Status AdminSelect keyboard select and escape without change", async ({
    page,
  }) => {
    await seedAdminSession(page);
    await mockInboxApi(page);

    await page.goto("/admin/reports");
    await expect(page.getByRole("heading", { name: "Report inbox" })).toBeVisible();

    const statusTrigger = page.locator("#inbox-filter-status");
    await statusTrigger.focus();
    await page.keyboard.press("Enter");
    await expect(statusTrigger).toHaveAttribute("aria-expanded", "true");

    await page.keyboard.press("ArrowDown");
    await page.keyboard.press("Enter");
    await expect(page).toHaveURL(/status=new/);
    await expect(statusTrigger).toHaveAttribute("aria-expanded", "false");

    await statusTrigger.focus();
    await page.keyboard.press("Enter");
    await page.keyboard.press("ArrowDown");
    await page.keyboard.press("Escape");
    await expect(page).toHaveURL(/status=new/);
    await expect(statusTrigger).toHaveAttribute("aria-expanded", "false");
  });

  test("Submitted from AdminDatePicker keyboard open and escape", async ({
    page,
  }) => {
    await seedAdminSession(page);
    await mockInboxApi(page);

    await page.goto("/admin/reports");
    const fromTrigger = page.locator("#inbox-filter-from");
    await fromTrigger.focus();
    await page.keyboard.press("Enter");
    await expect(fromTrigger).toHaveAttribute("aria-expanded", "true");

    await page.keyboard.press("ArrowRight");
    await page.keyboard.press("Escape");
    await expect(page.url()).not.toContain("from=");
    await expect(fromTrigger).toHaveAttribute("aria-expanded", "false");
    await expect(fromTrigger).toBeFocused();
  });
});
