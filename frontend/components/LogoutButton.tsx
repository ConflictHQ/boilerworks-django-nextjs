"use client";

import { Button } from "@/components/ui/button";
import { clearToken } from "@/lib/auth/token-store";

export default function LogoutButton() {
  const handleLogout = () => {
    clearToken();
    window.location.href = "/auth/logout";
  };

  return (
    <Button variant="outline" onClick={handleLogout}>
      Log out
    </Button>
  );
}
