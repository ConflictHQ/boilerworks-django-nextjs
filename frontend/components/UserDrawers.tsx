"use client";

import {
  Drawer,
  DrawerContent,
  DrawerDescription,
  DrawerHeader,
  DrawerTitle,
} from "@calliopelabs/ui";
import { AlertTriangleIcon, CheckCircle2Icon, InfoIcon, ZapIcon } from "lucide-react";
import { useTranslations } from "next-intl";
import { Separator } from "@/ui-app/primitives/separator";
import type { CurrentUser } from "@/graphql/user/user.types";

type DrawerProps = { open: boolean; onOpenChange: (open: boolean) => void };

/** The signed-in person, as the server rendered them and as the client sees them. */
export const AccountDrawer = ({
  open,
  onOpenChange,
  ssrUser,
  clientUser,
  loading,
}: DrawerProps & {
  ssrUser: CurrentUser | null;
  clientUser: CurrentUser | null;
  loading: boolean;
}) => {
  const t = useTranslations("user");
  return (
    <Drawer open={open} onOpenChange={onOpenChange}>
      <DrawerContent>
        <DrawerHeader>
          <DrawerTitle>{t("account")}</DrawerTitle>
          <DrawerDescription>
            {clientUser?.username ?? ssrUser?.username ?? "—"} ·{" "}
            {clientUser?.email ?? ssrUser?.email}
          </DrawerDescription>
        </DrawerHeader>
        <div className="flex flex-col gap-6 px-4 py-2">
          <section className="flex flex-col gap-3">
            <p className="text-muted-foreground text-xs font-semibold tracking-wider uppercase">
              SSR · getClient
            </p>
            <Row label="me.id" value={ssrUser?.id ?? "—"} />
            <Row label="me.profile.guid" value={ssrUser?.profile?.guid ?? "—"} />
            <Row label="me.profile.displayName" value={ssrUser?.profile?.displayName ?? "—"} />
          </section>

          <Separator />

          <section className="flex flex-col gap-3">
            <p className="text-muted-foreground text-xs font-semibold tracking-wider uppercase">
              Client · useMe {loading && <span className="font-normal normal-case">loading…</span>}
            </p>
            <Row label="me.id" value={clientUser?.id ?? "—"} />
            <Row label="me.profile.guid" value={clientUser?.profile?.guid ?? "—"} />
            <Row label="me.profile.displayName" value={clientUser?.profile?.displayName ?? "—"} />
          </section>
        </div>
      </DrawerContent>
    </Drawer>
  );
};

const Row = ({ label, value }: { label: string; value: string }) => (
  <div className="flex items-center justify-between text-sm">
    <span className="text-muted-foreground">{label}</span>
    <span className="font-mono">{value}</span>
  </div>
);

type Notification = {
  id: number;
  icon: React.ReactNode;
  title: string;
  description: string;
  time: string;
  unread: boolean;
};

const NOTIFICATIONS: Notification[] = [
  {
    id: 1,
    icon: <ZapIcon className="text-primary h-4 w-4" />,
    title: "Quantum model released",
    description:
      "The new Quantum model is now available with 1M-token context and extended thinking.",
    time: "2 min ago",
    unread: true,
  },
  {
    id: 2,
    icon: <AlertTriangleIcon className="text-warning-fg h-4 w-4" />,
    title: "Usage threshold reached",
    description: "You have used 80% of your monthly token quota. Consider upgrading your plan.",
    time: "1 hr ago",
    unread: true,
  },
  {
    id: 3,
    icon: <CheckCircle2Icon className="text-success-fg h-4 w-4" />,
    title: "Fine-tuning job complete",
    description: "Your fine-tuning job 'customer-support-v2' finished successfully.",
    time: "3 hr ago",
    unread: true,
  },
  {
    id: 4,
    icon: <InfoIcon className="text-muted-foreground h-4 w-4" />,
    title: "Scheduled maintenance",
    description: "Brief downtime planned on 2026-03-01 between 02:00–03:00 UTC.",
    time: "Yesterday",
    unread: false,
  },
];

/** A sample notifications feed; wire it to the notifications query in a real app. */
export const NotificationsDrawer = ({ open, onOpenChange }: DrawerProps) => {
  const t = useTranslations("user");
  return (
    <Drawer open={open} onOpenChange={onOpenChange}>
      <DrawerContent>
        <DrawerHeader>
          <DrawerTitle>{t("notifications")}</DrawerTitle>
        </DrawerHeader>
        <div className="flex flex-col gap-1 px-2 py-2">
          {NOTIFICATIONS.map((n) => (
            <NotificationRow key={n.id} {...n} />
          ))}
        </div>
      </DrawerContent>
    </Drawer>
  );
};

const NotificationRow = ({ icon, title, description, time, unread }: Notification) => (
  <div className={`flex gap-3 rounded-lg px-3 py-3 ${unread ? "bg-accent/50" : ""}`}>
    <div className="bg-muted flex h-8 w-8 shrink-0 items-center justify-center rounded-full">
      {icon}
    </div>
    <div className="flex min-w-0 flex-1 flex-col gap-0.5">
      <span className={`truncate text-sm ${unread ? "font-semibold" : "font-medium"}`}>
        {title}
      </span>
      <p className="text-muted-foreground text-xs leading-relaxed">{description}</p>
      <span className="text-muted-foreground mt-0.5 text-xs">{time}</span>
    </div>
  </div>
);
