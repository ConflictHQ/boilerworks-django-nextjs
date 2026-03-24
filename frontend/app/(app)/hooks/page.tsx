"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { Separator } from "@/components/ui/separator";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { useDebounce } from "@/hooks/use-debounce";
import { useLocalStorage } from "@/hooks/use-local-storage";
import { useCopyToClipboard } from "@/hooks/use-copy-to-clipboard";
import { useConfirm } from "@/hooks/use-confirm";

export default function HooksPage() {
  const t = useTranslations("hooks");

  // useDebounce
  const [rawValue, setRawValue] = useState("");
  const debouncedValue = useDebounce(rawValue);

  // useLocalStorage
  const [count, setCount] = useLocalStorage("hooks-demo-count", 0);

  // useCopyToClipboard
  const [copyText, setCopyText] = useState("Hello, world!");
  const [copied, copy] = useCopyToClipboard();

  // useConfirm
  const confirm = useConfirm();
  const [confirmResult, setConfirmResult] = useState<string | null>(null);

  const handleDelete = async () => {
    const ok = await confirm({
      title: t("confirm.dialogTitle"),
      description: t("confirm.dialogDescription"),
      confirmLabel: t("confirm.confirmLabel"),
      cancelLabel: t("confirm.cancelLabel"),
    });
    setConfirmResult(ok ? t("confirm.resultConfirmed") : t("confirm.resultCancelled"));
  };

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <div>
        <h1 className="text-xl font-semibold">{t("title")}</h1>
        <p className="text-muted-foreground mt-1 text-sm">{t("description")}</p>
      </div>
      <Separator />

      {/* useDebounce */}
      <section className="flex flex-col gap-3">
        <div>
          <h2 className="font-semibold">{t("debounce.title")}</h2>
          <p className="text-muted-foreground text-sm">{t("debounce.description")}</p>
        </div>
        <div className="flex max-w-sm flex-col gap-2">
          <Label>{t("debounce.label")}</Label>
          <Input
            placeholder={t("debounce.placeholder")}
            value={rawValue}
            onChange={(e) => setRawValue(e.target.value)}
          />
        </div>
        <dl className="text-sm">
          <div className="flex gap-2">
            <dt className="text-muted-foreground">{t("debounce.raw")}:</dt>
            <dd className="font-mono">{rawValue || "—"}</dd>
          </div>
          <div className="flex gap-2">
            <dt className="text-muted-foreground">{t("debounce.debounced")}:</dt>
            <dd className="font-mono">{debouncedValue || "—"}</dd>
          </div>
        </dl>
      </section>

      <Separator />

      {/* useLocalStorage */}
      <section className="flex flex-col gap-3">
        <div>
          <h2 className="font-semibold">{t("localStorage.title")}</h2>
          <p className="text-muted-foreground text-sm">{t("localStorage.description")}</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm">
            {t("localStorage.label")}: <span className="font-mono font-semibold">{count}</span>
          </span>
          <Button size="sm" onClick={() => setCount(count + 1)}>
            {t("localStorage.increment")}
          </Button>
          <Button size="sm" variant="outline" onClick={() => setCount(0)}>
            {t("localStorage.reset")}
          </Button>
        </div>
      </section>

      <Separator />

      {/* useCopyToClipboard */}
      <section className="flex flex-col gap-3">
        <div>
          <h2 className="font-semibold">{t("clipboard.title")}</h2>
          <p className="text-muted-foreground text-sm">{t("clipboard.description")}</p>
        </div>
        <div className="flex max-w-sm flex-col gap-2">
          <Label>{t("clipboard.label")}</Label>
          <div className="flex gap-2">
            <Input value={copyText} onChange={(e) => setCopyText(e.target.value)} />
            <Button size="sm" onClick={() => copy(copyText)} disabled={copied}>
              {copied ? t("clipboard.copied") : t("clipboard.copy")}
            </Button>
          </div>
        </div>
      </section>

      <Separator />

      {/* useConfirm */}
      <section className="flex flex-col gap-3">
        <div>
          <h2 className="font-semibold">{t("confirm.title")}</h2>
          <p className="text-muted-foreground text-sm">{t("confirm.description")}</p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="destructive" size="sm" onClick={handleDelete}>
            {t("confirm.trigger")}
          </Button>
          {confirmResult && <p className="text-sm">{confirmResult}</p>}
        </div>
      </section>
    </div>
  );
}
