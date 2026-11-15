import { AppearancePicker, PageHeader } from "@calliopelabs/ui";
import { getTranslations } from "next-intl/server";
import { Separator } from "@/ui-app/primitives/separator";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";

export default async function SettingsPage() {
  const t = await getTranslations("settings");

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader title={t("title")} description={t("description")} />

      <Separator />

      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <div>
          <h2 className="text-sm font-medium">{t("language.title")}</h2>
          <p className="text-muted-foreground mt-0.5 text-sm">{t("language.description")}</p>
        </div>
        <div className="col-span-full md:col-span-2">
          <LanguageSwitcher />
        </div>
      </div>

      <Separator />

      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <div>
          <h2 className="text-sm font-medium">{t("theme.title")}</h2>
          <p className="text-muted-foreground mt-1 text-sm">{t("theme.description")}</p>
        </div>
        <div className="col-span-full md:col-span-2">
          <AppearancePicker />
        </div>
      </div>
    </div>
  );
}
