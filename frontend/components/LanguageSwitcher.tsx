"use client";

import { useLocale, useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useTransition } from "react";
import { GlobeIcon } from "lucide-react";
import { setLocale } from "@/app/actions/locale";
import { locales, type Locale } from "@/i18n/config";
import { SidebarMenu, SidebarMenuButton, SidebarMenuItem } from "@/components/ui/sidebar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

type Props = {
  variant?: "sidebar" | "select";
};

export const LanguageSwitcher = ({ variant = "sidebar" }: Props) => {
  const t = useTranslations("language");
  const locale = useLocale();
  const router = useRouter();
  const [isPending, startTransition] = useTransition();

  const handleChange = (next: Locale) => {
    startTransition(async () => {
      await setLocale(next);
      router.refresh();
    });
  };

  if (variant === "select") {
    return (
      <Select value={locale} onValueChange={(v) => handleChange(v as Locale)} disabled={isPending}>
        <SelectTrigger className="w-48">
          <GlobeIcon className="size-4" />
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {locales.map((l) => (
            <SelectItem key={l} value={l}>
              {t(l)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    );
  }

  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <SidebarMenuButton
              size="sm"
              tooltip={t("label")}
              disabled={isPending}
              className="text-muted-foreground"
            >
              <GlobeIcon className="size-4" />
              <span>{t(locale as Locale)}</span>
            </SidebarMenuButton>
          </DropdownMenuTrigger>
          <DropdownMenuContent side="top" align="start">
            {locales.map((l) => (
              <DropdownMenuItem
                key={l}
                onSelect={() => handleChange(l)}
                data-active={l === locale}
                className="data-[active=true]:font-medium"
              >
                {t(l)}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      </SidebarMenuItem>
    </SidebarMenu>
  );
};
