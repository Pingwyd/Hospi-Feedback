import { expect, test } from "@playwright/test";
import fs from "fs";
import path from "path";

const TICKET_CODE = "ABCD2345";
const FIXTURE_PNG = path.join(__dirname, "fixtures", "tiny.png");
const PNG_BYTES = fs.readFileSync(FIXTURE_PNG);

const MSG_BATCH = "msg-batch-three";
const MSG_SINGLE = "msg-single-one";

function attachmentSummary(id: string, uploadedAt: string) {
  return {
    id,
    file_type: "image/png",
    uploaded_at: uploadedAt,
    preview_url: `/api/reports/ticket/${TICKET_CODE}/attachments/${id}`,
  };
}

async function mockStatusThreadWithMixedBubbles(page: import("@playwright/test").Page) {
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
        description: "Thread shape regression fixture.",
        reported_member_name: null,
        severity: null,
        created_at: "2026-09-03T12:00:00Z",
        updated_at: "2026-09-03T13:00:00Z",
        report_attachments: [],
        messages: [
          {
            id: MSG_BATCH,
            sender_type: "reporter",
            content: "Photo attached",
            created_at: "2026-09-03T12:30:00Z",
            attachments: [
              attachmentSummary("att-a1", "2026-09-03T12:30:00Z"),
              attachmentSummary("att-a2", "2026-09-03T12:30:01Z"),
              attachmentSummary("att-a3", "2026-09-03T12:30:02Z"),
            ],
          },
          {
            id: MSG_SINGLE,
            sender_type: "reporter",
            content: "Photo attached",
            created_at: "2026-09-03T12:45:00Z",
            attachment: attachmentSummary("att-b1", "2026-09-03T12:45:00Z"),
          },
        ],
      }),
    });
  });
  await page.route(
    `**/api/reports/ticket/${TICKET_CODE}/attachments/**`,
    async (route) => {
      if (route.request().method() !== "GET") {
        await route.continue();
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "image/png",
        body: PNG_BYTES,
      });
    },
  );
}

test.describe("Reporter status thread (Model A attachment shapes)", () => {
  test.beforeEach(async ({ page }) => {
    await page.context().addCookies([
      {
        name: "hospi_access_session",
        value: "mock-session-token",
        url: "http://127.0.0.1:3000",
      },
    ]);
  });

  test("renders one bubble with three thumbnails and one bubble with one thumbnail", async ({
    page,
  }) => {
    await mockStatusThreadWithMixedBubbles(page);
    await page.goto(`/status/${TICKET_CODE}`);

    const conversation = page
      .getByRole("heading", { name: "Conversation" })
      .locator("xpath=ancestor::section[1]");
    const messageBubbles = conversation.locator("ul.space-y-3 > li");
    await expect(messageBubbles).toHaveCount(2);

    const threeUp = messageBubbles.nth(0).locator("ul.flex.flex-wrap.gap-2 > li");
    await expect(threeUp).toHaveCount(3);
    await expect(
      messageBubbles.nth(0).getByRole("button", { name: "View full size: Follow-up photo 1" }),
    ).toBeVisible();
    await expect(
      messageBubbles.nth(0).getByRole("button", { name: "View full size: Follow-up photo 3" }),
    ).toBeVisible();

    const oneUp = messageBubbles.nth(1).locator("ul.flex.flex-wrap.gap-2 > li");
    await expect(oneUp).toHaveCount(1);
    await expect(
      messageBubbles.nth(1).getByRole("button", { name: "View full size: Follow-up photo" }),
    ).toBeVisible();

    await expect(messageBubbles.nth(0)).not.toContainText("Photo attached");
    await expect(messageBubbles.nth(1)).not.toContainText("Photo attached");
  });
});
