import { getTranslations } from "next-intl/server";
import { Separator } from "@/components/ui/separator";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { ThemeToggle } from "@/components/ThemeToggle";

export default async function SettingsPage() {
  const t = await getTranslations("settings");

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <div>
        <h1 className="text-xl font-semibold">{t("title")}</h1>
        <p className="text-muted-foreground mt-1 text-sm">{t("description")}</p>
      </div>

      <Separator />

      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <div>
          <h2 className="text-sm font-medium">{t("language.title")}</h2>
          <p className="text-muted-foreground mt-0.5 text-sm">{t("language.description")}</p>
        </div>
        <div className="col-span-full md:col-span-2">
          <LanguageSwitcher variant="select" />
        </div>
      </div>

      <Separator />

      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <div>
          <h2 className="text-sm font-medium">{t("theme.title")}</h2>
          <p className="text-muted-foreground mt-1 text-sm">{t("theme.description")}</p>
        </div>
        <div className="col-span-full md:col-span-2">
          <ThemeToggle variant="select" />
        </div>
      </div>
    </div>
  );
}
