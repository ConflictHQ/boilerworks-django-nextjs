"use client";

import { useAppearance } from "@calliopelabs/ui";
import { Toaster as SonnerToaster } from "sonner";

export const Toaster = () => {
  const { mode } = useAppearance();
  return <SonnerToaster theme={mode} richColors />;
};
