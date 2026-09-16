import { expect, test } from "@playwright/test";
import path from "path";

const TICKET_CODE = "ABCD2345";

function mockStatusPageApi(
  page: import("@playwright/test").Page,
  options: { onUpload?: () => void } = {},
) {
  return Promise.all([
    page.route("**/api/_phase2/public-ping", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ ok: true }),
      });
    }),
    page.route("**/api/access/ws-bootstrap", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          access_token: "mock-session-token",
          expires_at: "2026-09-04T12:00:00Z",
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
          report_attachments: [],
          messages: [],
        }),
      });
    }),
    page.route(`**/api/reports/ticket/${TICKET_CODE}/attachments**`, async (route) => {
      if (route.request().method() !== "POST") {
        await route.continue();
        return;
      }
      const url = route.request().url();
      if (!url.includes("/attachments/batch")) {
        await route.continue();
        return;
      }
      options.onUpload?.();
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({
          report_id: "report-playwright-1",
          message_id: "msg-playwright-1",
          attachments: [
            {
              id: "att-playwright-1",
              file_type: "image/png",
              uploaded_at: "2026-09-03T13:00:00Z",
              preview_url: `/api/reports/ticket/${TICKET_CODE}/attachments/att-playwright-1`,
            },
          ],
        }),
      });
    }),
  ]);
}

const FIXTURE_PNG = path.join(__dirname, "fixtures", "tiny.png");

test.describe("Follow-up photo confirm before upload", () => {
  test.beforeEach(async ({ page }) => {
    await page.context().addCookies([
      {
        name: "hospi_access_session",
        value: "mock-session-token",
        url: "http://127.0.0.1:3000",
      },
    ]);
  });

  test("selecting a photo opens confirm modal without uploading", async ({ page }) => {
    let uploadCount = 0;
    await mockStatusPageApi(page, { onUpload: () => { uploadCount += 1; } });

    await page.goto(`/status/${TICKET_CODE}`);
    await page.getByRole("button", { name: "Add photo" }).click();
    await page.locator("#status-photo").setInputFiles(FIXTURE_PNG);

    await expect(page.getByRole("dialog", { name: "Photos ready to send" })).toBeVisible();
    await expect(page.getByText("1 photo selected")).toBeVisible();
    expect(uploadCount).toBe(0);
  });

  test("cancel closes modal without uploading", async ({ page }) => {
    let uploadCount = 0;
    await mockStatusPageApi(page, { onUpload: () => { uploadCount += 1; } });

    await page.goto(`/status/${TICKET_CODE}`);
    await page.getByRole("button", { name: "Add photo" }).click();
    await page.locator("#status-photo").setInputFiles(FIXTURE_PNG);
    await page.getByRole("button", { name: "Cancel and discard photo" }).click();

    await expect(page.getByRole("dialog")).toHaveCount(0);
    expect(uploadCount).toBe(0);
  });

  test("confirm uploads once from modal", async ({ page }) => {
    let uploadCount = 0;
    await mockStatusPageApi(page, { onUpload: () => { uploadCount += 1; } });

    await page.goto(`/status/${TICKET_CODE}`);
    await page.getByRole("button", { name: "Add photo" }).click();
    await page.locator("#status-photo").setInputFiles(FIXTURE_PNG);
    await page.getByRole("button", { name: "Send photo to thread" }).click();
    await expect(page.getByText("Photo sent.")).toBeVisible();
    expect(uploadCount).toBe(1);
  });

  test("send locks modal actions before upload finishes", async ({ page }) => {
    let uploadCount = 0;
    let releaseUpload: (() => void) | null = null;
    const uploadGate = new Promise<void>((resolve) => {
      releaseUpload = resolve;
    });

    await page.route("**/api/_phase2/public-ping", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ ok: true }),
      });
    });
    await page.route("**/api/access/ws-bootstrap", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          access_token: "mock-session-token",
          expires_at: "2026-09-04T12:00:00Z",
        }),
      });
    });
    await page.route(`**/api/reports/ticket/${TICKET_CODE}`, async (route) => {
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
          report_attachments: [],
          messages: [],
        }),
      });
    });
    await page.route(`**/api/reports/ticket/${TICKET_CODE}/attachments**`, async (route) => {
      if (route.request().method() !== "POST") {
        await route.continue();
        return;
      }
      const url = route.request().url();
      if (!url.includes("/attachments/batch")) {
        await route.continue();
        return;
      }
      uploadCount += 1;
      await uploadGate;
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({
          report_id: "report-playwright-2",
          message_id: "msg-playwright-2",
          attachments: [
            {
              id: "att-playwright-2",
              file_type: "image/png",
              uploaded_at: "2026-09-03T13:00:00Z",
              preview_url: `/api/reports/ticket/${TICKET_CODE}/attachments/att-playwright-2`,
            },
          ],
        }),
      });
    });

    await page.goto(`/status/${TICKET_CODE}`);
    await page.getByRole("button", { name: "Add photo" }).click();
    await page.locator("#status-photo").setInputFiles(FIXTURE_PNG);

    const sendButton = page.getByRole("button", { name: "Send photo to thread" });
    await sendButton.click();

    const dialog = page.getByRole("dialog", { name: "Photos ready to send" });
    await expect(dialog.getByRole("button", { name: "Uploading..." })).toBeDisabled();
    await expect(dialog.getByRole("button", { name: "Add more photos" })).toBeDisabled();

    releaseUpload?.();
    await expect(page.getByText("Photo sent.")).toBeVisible();
    expect(uploadCount).toBe(1);
  });

  test("multi-select opens one dialog with all previews before upload", async ({ page }) => {
    let uploadCount = 0;
    await mockStatusPageApi(page, { onUpload: () => { uploadCount += 1; } });

    await page.goto(`/status/${TICKET_CODE}`);
    await page.getByRole("button", { name: "Add photo" }).click();
    await page.locator("#status-photo").setInputFiles([FIXTURE_PNG, FIXTURE_PNG]);

    await expect(page.getByText("2 photos selected")).toBeVisible();
    expect(uploadCount).toBe(0);

    await page.getByRole("button", { name: "Send 2 photos to thread" }).click();
    await expect(page.getByText("2 photos sent.")).toBeVisible();
    expect(uploadCount).toBe(1);
  });

  test("mobile viewport shows dialog and explicit action labels", async ({ page }) => {
    let uploadCount = 0;
    await mockStatusPageApi(page, { onUpload: () => { uploadCount += 1; } });
    await page.setViewportSize({ width: 390, height: 844 });

    await page.goto(`/status/${TICKET_CODE}`);
    await page.getByRole("button", { name: "Add photo" }).click();
    await page.locator("#status-photo").setInputFiles(FIXTURE_PNG);

    const dialog = page.getByRole("dialog", { name: "Photos ready to send" });
    await expect(dialog).toBeVisible();
    await expect(dialog.getByRole("heading", { name: "Photos ready to send" })).toBeVisible();
    await expect(dialog.getByRole("button", { name: "Send photo to thread" })).toBeVisible();
    await expect(dialog.getByRole("button", { name: "Cancel and discard photo" })).toBeVisible();
    await expect(dialog.getByRole("button", { name: "Add more photos" })).toBeVisible();
    expect(uploadCount).toBe(0);
  });

  test("rapid send then add-more in modal does not double upload", async ({ page }) => {
    let uploadCount = 0;
    let releaseUpload: (() => void) | null = null;
    const uploadGate = new Promise<void>((resolve) => {
      releaseUpload = resolve;
    });

    await page.route("**/api/_phase2/public-ping", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ ok: true }),
      });
    });
    await page.route("**/api/access/ws-bootstrap", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          access_token: "mock-session-token",
          expires_at: "2026-09-04T12:00:00Z",
        }),
      });
    });
    await page.route(`**/api/reports/ticket/${TICKET_CODE}`, async (route) => {
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
          report_attachments: [],
          messages: [],
        }),
      });
    });
    await page.route(`**/api/reports/ticket/${TICKET_CODE}/attachments**`, async (route) => {
      if (route.request().method() !== "POST") {
        await route.continue();
        return;
      }
      const url = route.request().url();
      if (!url.includes("/attachments/batch")) {
        await route.continue();
        return;
      }
      uploadCount += 1;
      await uploadGate;
      await route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({
          report_id: "report-playwright-3",
          message_id: "msg-playwright-3",
          attachments: [
            {
              id: "att-playwright-3",
              file_type: "image/png",
              uploaded_at: "2026-09-03T13:00:00Z",
              preview_url: `/api/reports/ticket/${TICKET_CODE}/attachments/att-playwright-3`,
            },
          ],
        }),
      });
    });

    await page.goto(`/status/${TICKET_CODE}`);
    await page.getByRole("button", { name: "Add photo" }).click();
    await page.locator("#status-photo").setInputFiles(FIXTURE_PNG);

    await page.evaluate(() => {
      const send = Array.from(document.querySelectorAll("button")).find(
        (el) => el.textContent?.trim() === "Send photo to thread",
      ) as HTMLButtonElement | undefined;
      const addMore = Array.from(document.querySelectorAll("button")).find(
        (el) => el.textContent?.trim() === "Add more photos",
      ) as HTMLButtonElement | undefined;
      send?.click();
      addMore?.click();
    });

    const dialog = page.getByRole("dialog", { name: "Photos ready to send" });
    await expect(dialog.getByRole("button", { name: "Uploading..." })).toBeDisabled();
    expect(uploadCount).toBe(1);

    releaseUpload?.();
    await expect(page.getByText("Photo sent.")).toBeVisible();
    expect(uploadCount).toBe(1);
  });
});
