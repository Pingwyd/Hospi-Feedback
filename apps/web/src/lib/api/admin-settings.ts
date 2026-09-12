import { adminFetch } from "./admin-fetch";

export type Category = {
  id: string;
  name: string;
  active: boolean;
};

export async function listCategories(): Promise<Category[]> {
  const payload = await adminFetch<{ data: Category[] }>("/api/admin/categories");
  return payload.data;
}

export async function createCategory(name: string): Promise<Category> {
  const payload = await adminFetch<{ data: Category }>("/api/admin/categories", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
  return payload.data;
}

export async function updateCategory(
  categoryId: string,
  fields: { name?: string; active?: boolean },
): Promise<Category> {
  const payload = await adminFetch<{ data: Category }>(
    `/api/admin/categories/${categoryId}`,
    {
      method: "PATCH",
      body: JSON.stringify(fields),
    },
  );
  return payload.data;
}

export type EscalationContact = {
  id: string;
  name: string;
  role_label: string;
  contact_email: string | null;
  contact_phone: string | null;
  active: boolean;
};

export type EscalationContactInput = {
  name: string;
  role_label: string;
  contact_email?: string | null;
  contact_phone?: string | null;
};

export async function listEscalationContacts(): Promise<EscalationContact[]> {
  const payload = await adminFetch<{ data: EscalationContact[] }>(
    "/api/admin/escalation-contacts",
  );
  return payload.data;
}

export async function createEscalationContact(
  input: EscalationContactInput,
): Promise<EscalationContact> {
  const payload = await adminFetch<{ data: EscalationContact }>(
    "/api/admin/escalation-contacts",
    {
      method: "POST",
      body: JSON.stringify(input),
    },
  );
  return payload.data;
}

export async function updateEscalationContact(
  contactId: string,
  fields: Partial<EscalationContactInput> & { active?: boolean },
): Promise<EscalationContact> {
  const payload = await adminFetch<{ data: EscalationContact }>(
    `/api/admin/escalation-contacts/${contactId}`,
    {
      method: "PATCH",
      body: JSON.stringify(fields),
    },
  );
  return payload.data;
}

export const ADMIN_PERMISSIONS = [
  "view",
  "respond",
  "assign",
  "close",
  "export",
  "manage_categories",
  "manage_admins",
  "manage_escalation_contacts",
] as const;

export type AdminPermission = (typeof ADMIN_PERMISSIONS)[number];

export const ADMIN_ROLES = [
  { value: "hoh", label: "Head of Hospi" },
  { value: "asst_head", label: "Assistant Head" },
  { value: "gen_sec", label: "General Secretary" },
  { value: "fin_sec", label: "Financial Secretary" },
  { value: "subunit_head", label: "Sub-unit Head" },
  { value: "subunit_asst", label: "Sub-unit Assistant" },
  { value: "custom", label: "Custom" },
] as const;

export type AdminRole = (typeof ADMIN_ROLES)[number]["value"];

export type AdminUser = {
  id: string;
  full_name: string;
  role: AdminRole | string;
  subunit: string | null;
  active: boolean;
  permissions: string[];
};

export type CreateAdminInput = {
  email: string;
  password: string;
  full_name: string;
  role: AdminRole;
  subunit?: string | null;
  permissions: string[];
};

export async function listAdminUsers(): Promise<AdminUser[]> {
  const payload = await adminFetch<{ data: AdminUser[] }>("/api/admin/admins");
  return payload.data;
}

export async function createAdminUser(input: CreateAdminInput): Promise<AdminUser> {
  const payload = await adminFetch<{ data: AdminUser }>("/api/admin/admins", {
    method: "POST",
    body: JSON.stringify({
      ...input,
      subunit: input.subunit?.trim() || null,
    }),
  });
  return payload.data;
}

export async function updateAdminUserPermissions(
  adminId: string,
  permissions: string[],
): Promise<{ id: string; permissions: string[] }> {
  const payload = await adminFetch<{ data: { id: string; permissions: string[] } }>(
    `/api/admin/admins/${adminId}/permissions`,
    {
      method: "PATCH",
      body: JSON.stringify({ permissions }),
    },
  );
  return payload.data;
}

export async function deactivateAdminUser(
  adminId: string,
): Promise<Partial<AdminUser>> {
  const payload = await adminFetch<{ data: Partial<AdminUser> }>(
    `/api/admin/admins/${adminId}/deactivate`,
    { method: "PATCH" },
  );
  return payload.data;
}
