"use client";

import { Button } from "@calliopelabs/ui";

export default function LoginButton() {
  return (
    <Button asChild>
      <a href="/auth/login">Log in</a>
    </Button>
  );
}
