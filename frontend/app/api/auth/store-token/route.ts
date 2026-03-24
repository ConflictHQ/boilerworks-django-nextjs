import { cookies } from "next/headers";
import { NextResponse } from "next/server";

export async function POST(request: Request) {
  const { token } = await request.json();
  if (!token || typeof token !== "string") {
    return NextResponse.json({ error: "invalid token" }, { status: 400 });
  }

  const cookieStore = await cookies();
  cookieStore.set("backend_jwt", token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
  });

  return NextResponse.json({ ok: true });
}
