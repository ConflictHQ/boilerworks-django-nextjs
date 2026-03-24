import { redirect } from "next/navigation";
import { cookies } from "next/headers";

export default async function RootPage() {
  const cookieStore = await cookies();
  const token = cookieStore.get("backend_jwt");

  if (token) {
    redirect("/dashboard");
  } else {
    redirect("/auth/login");
  }
}
