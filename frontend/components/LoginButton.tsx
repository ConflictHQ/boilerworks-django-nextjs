"use client";

import { Button } from "@/components/ui/button";

export default function LoginButton() {
  return (
    <Button asChild>
      <a href="/auth/login">Log in</a>
    </Button>
  );
}
