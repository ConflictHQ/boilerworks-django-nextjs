"use client";

import { useLocale, useTranslations } from "next-intl";
import { useRouter } from "next/navigation";
import { useTransition } from "react";
import { GlobeIcon } from "lucide-react";
import { setLocale } from "@/app/actions/locale";
import { locales, type Locale } from "@/i18n/config";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/ui-app/primitives/select";

export const LanguageSwitcher = () => {
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

  return (
    <Select value={locale} onValueChange={(v) => handleChange(v as Locale)} disabled={isPending}>
      <SelectTrigger className="w-48" aria-label={t("label")}>
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
};
