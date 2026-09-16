import { expect, test, type Page, type Route } from "@playwright/test";

const MANAGE_ADMINS_PROFILE = {
  id: "11111111-1111-1111-1111-111111111111",
  full_name: "Ada Okonkwo",
  role: "hoh",
  subunit: null,
  permissions: ["view", "manage_admins"],
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

async function mockAdminSettingsApi(page: Page) {
  await page.route("**/api/admin/**", async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname;

    if (path.endsWith("/api/admin/me")) {
      await fulfillJson(route, 200, { data: MANAGE_ADMINS_PROFILE });
      return;
    }
    if (path.endsWith("/api/admin/admins") && route.request().method() === "GET") {
      await fulfillJson(route, 200, {
        data: [
          {
            id: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
            full_name: "Legacy Subunit",
            role: "subunit_head",
            subunit: "legacy_team",
            active: true,
            permissions: ["view"],
          },
          {
            id: "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            full_name: "Welfare Head",
            role: "subunit_head",
            subunit: "welfare",
            active: true,
            permissions: ["view"],
          },
        ],
      });
      return;
    }
    await fulfillJson(route, 404, {
      error: { code: "not_found", message: "Unhandled mock route." },
    });
  });
}

test.describe("Admin subunit create modal", () => {
  test("switching away from subunit-scoped role clears subunit picker state", async ({
    page,
  }) => {
    await seedAdminSession(page);
    await mockAdminSettingsApi(page);

    await page.goto("/admin/settings");
    await page.getByRole("tab", { name: "Admin users" }).click();
    await expect(page.getByRole("heading", { name: "Admin users" })).toBeVisible();

    await page.getByRole("button", { name: "Create admin" }).click();
    await expect(page.getByRole("dialog", { name: "Create admin user" })).toBeVisible();

    const dialog = page.getByRole("dialog", { name: "Create admin user" });
    const roleSelect = dialog.locator("select");
    await roleSelect.selectOption("subunit_head");

    const subunitTrigger = dialog.getByRole("button", { name: /Subunit/i });
    await expect(subunitTrigger).toBeVisible();
    await subunitTrigger.click();
    await page.getByRole("option", { name: "Welfare" }).click();
    await expect(subunitTrigger).toContainText("Welfare");

    await roleSelect.selectOption("hoh");
    await expect(subunitTrigger).toHaveCount(0);

    await roleSelect.selectOption("subunit_asst");
    const subunitTriggerAgain = dialog.getByRole("button", { name: /Subunit/i });
    await expect(subunitTriggerAgain).toBeVisible();
    await expect(subunitTriggerAgain).toContainText("Select subunit");
  });

  test("list shows label for canonical subunit and flag for unlisted value", async ({
    page,
  }) => {
    await seedAdminSession(page);
    await mockAdminSettingsApi(page);

    await page.goto("/admin/settings");
    await page.getByRole("tab", { name: "Admin users" }).click();
    await expect(page.getByRole("cell", { name: "Welfare", exact: true })).toBeVisible();
    await expect(page.getByText("legacy_team")).toBeVisible();
    await expect(page.getByText("(Unlisted value)")).toBeVisible();
  });
});
