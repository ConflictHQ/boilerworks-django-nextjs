import { NextResponse } from "next/server";
import { fetchToken } from "@/lib/auth/fetch-token";

export async function POST() {
  console.log("[getToken] called");
  try {
    const token = await fetchToken();
    if (!token) {
      console.log("[getToken] no token — unauthorized");
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }
    console.log("[getToken] token resolved ✓");
    return NextResponse.json({ Authorization: token });
  } catch (error) {
    console.error("[getToken] error:", error);
    return NextResponse.json(
      { error: "Internal Server Error", message: String(error) },
      { status: 500 }
    );
  }
}
