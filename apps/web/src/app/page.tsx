import { cookies } from "next/headers";
import { redirect } from "next/navigation";

const ACCESS_COOKIE = "hospi_access_session";

export default async function HomePage() {
  const cookieStore = await cookies();
  const hasSessionCookie = cookieStore.has(ACCESS_COOKIE);
  redirect(hasSessionCookie ? "/report" : "/access");
}
