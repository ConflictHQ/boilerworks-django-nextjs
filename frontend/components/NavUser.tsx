"use client";

import { useEffect, useState } from "react";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "@/components/ui/sidebar";
import {
  BellIcon,
  BadgeCheckIcon,
  ChevronsUpDownIcon,
  LogOutIcon,
  ZapIcon,
  AlertTriangleIcon,
  InfoIcon,
  CheckCircle2Icon,
} from "lucide-react";
import { useTranslations } from "next-intl";
import { useMe } from "@/graphql/user/user.hooks";
import { clearToken } from "@/lib/auth/token-store";
import { setSentryUser } from "@/lib/sentry";
import type { CurrentUser } from "@/graphql/user/user.types";

export const NavUser = ({ ssrUser }: { ssrUser: CurrentUser | null }) => {
  const t = useTranslations("user");
  const { isMobile } = useSidebar();
  const { data: meData, user, loading: meLoading } = useMe();
  const [accountOpen, setAccountOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);

  useEffect(() => {
    setSentryUser(user ?? null);
  }, [user]);

  const name = user?.profile?.username ?? "User";
  const email = user?.email ?? "";
  const avatar = "";
  const initials = name.slice(0, 2).toUpperCase();

  const handleLogout = () => {
    setSentryUser(null);
    clearToken();
    const apiRoot = process.env.NEXT_PUBLIC_API_ROOT ?? "";
    window.location.href = `${apiRoot}/app/auth1/logout`;
  };

  return (
    <>
      <SidebarMenu>
        <SidebarMenuItem>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <SidebarMenuButton
                size="lg"
                className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
              >
                <Avatar className="h-8 w-8 rounded-lg">
                  <AvatarImage src={avatar} alt={name} />
                  <AvatarFallback className="rounded-lg">{initials}</AvatarFallback>
                </Avatar>
                <div className="grid flex-1 text-left text-sm leading-tight">
                  <span className="truncate font-medium">{name}</span>
                  <span className="truncate text-xs">{email}</span>
                </div>
                <ChevronsUpDownIcon className="ml-auto size-4" />
              </SidebarMenuButton>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              className="w-(--radix-dropdown-menu-trigger-width) min-w-56 rounded-lg"
              side={isMobile ? "bottom" : "right"}
              align="end"
              sideOffset={4}
            >
              <DropdownMenuLabel className="p-0 font-normal">
                <div className="flex items-center gap-2 px-1 py-1.5 text-left text-sm">
                  <Avatar className="h-8 w-8 rounded-lg">
                    <AvatarImage src={avatar} alt={name} />
                    <AvatarFallback className="rounded-lg">{initials}</AvatarFallback>
                  </Avatar>
                  <div className="grid flex-1 text-left text-sm leading-tight">
                    <span className="truncate font-medium">{name}</span>
                    <span className="truncate text-xs">{email}</span>
                  </div>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuGroup>
                <DropdownMenuItem onSelect={() => setAccountOpen(true)}>
                  <BadgeCheckIcon />
                  {t("account")}
                </DropdownMenuItem>
                <DropdownMenuItem onSelect={() => setNotificationsOpen(true)}>
                  <BellIcon />
                  {t("notifications")}
                </DropdownMenuItem>
              </DropdownMenuGroup>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout}>
                <LogOutIcon />
                {t("logout")}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </SidebarMenuItem>
      </SidebarMenu>

      <Sheet open={notificationsOpen} onOpenChange={setNotificationsOpen}>
        <SheetContent>
          <SheetHeader>
            <SheetTitle>{t("notifications")}</SheetTitle>
          </SheetHeader>
          <div className="flex flex-col gap-1 py-4">
            {NOTIFICATIONS.map((n) => (
              <NotificationRow key={n.id} {...n} />
            ))}
          </div>
        </SheetContent>
      </Sheet>

      <Sheet open={accountOpen} onOpenChange={setAccountOpen}>
        <SheetContent>
          <SheetHeader>
            <SheetTitle>Account</SheetTitle>
          </SheetHeader>

          <div className="flex flex-col items-center gap-3 py-6">
            <Avatar className="h-20 w-20 rounded-xl">
              <AvatarImage src={avatar} alt={name} />
              <AvatarFallback className="rounded-xl text-2xl">{initials}</AvatarFallback>
            </Avatar>
            <div className="text-center">
              <p className="text-lg font-semibold">{name}</p>
              <p className="text-muted-foreground text-sm">{email}</p>
            </div>
          </div>

          <Separator />

          <div className="flex flex-col gap-6 px-1 py-6">
            <section className="flex flex-col gap-3">
              <p className="text-muted-foreground text-xs font-semibold tracking-wider uppercase">
                SSR · getClient
              </p>
              <Row label="me.id" value={ssrUser?.id ?? "—"} />
              <Row label="me.profile.id" value={ssrUser?.profile?.id ?? "—"} />
              <Row label="me.profile.username" value={ssrUser?.profile?.username ?? "—"} />
            </section>

            <Separator />

            <section className="flex flex-col gap-3">
              <p className="text-muted-foreground text-xs font-semibold tracking-wider uppercase">
                Client · useMe{" "}
                {meLoading && <span className="font-normal normal-case">loading…</span>}
              </p>
              <Row label="me.id" value={meData?.me?.id ?? "—"} />
              <Row label="me.profile.id" value={meData?.me?.profile?.id ?? "—"} />
              <Row label="me.profile.username" value={meData?.me?.profile?.username ?? "—"} />
            </section>

          </div>
        </SheetContent>
      </Sheet>
    </>
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
    icon: <AlertTriangleIcon className="h-4 w-4 text-yellow-500" />,
    title: "Usage threshold reached",
    description: "You have used 80% of your monthly token quota. Consider upgrading your plan.",
    time: "1 hr ago",
    unread: true,
  },
  {
    id: 3,
    icon: <CheckCircle2Icon className="h-4 w-4 text-green-500" />,
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
  {
    id: 5,
    icon: <CheckCircle2Icon className="h-4 w-4 text-green-500" />,
    title: "API key rotated",
    description: "Your API key was successfully rotated. Update your integrations if needed.",
    time: "2 days ago",
    unread: false,
  },
];

const NotificationRow = ({ icon, title, description, time, unread }: Notification) => (
  <div className={`flex gap-3 rounded-lg px-3 py-3 ${unread ? "bg-accent/50" : ""}`}>
    <div className="bg-muted flex h-8 w-8 shrink-0 items-center justify-center rounded-full">
      {icon}
    </div>
    <div className="flex min-w-0 flex-1 flex-col gap-0.5">
      <div className="flex items-center justify-between gap-2">
        <span className={`truncate text-sm ${unread ? "font-semibold" : "font-medium"}`}>
          {title}
        </span>
        {unread && <span className="bg-primary h-2 w-2 shrink-0 rounded-full" />}
      </div>
      <p className="text-muted-foreground text-xs leading-relaxed">{description}</p>
      <span className="text-muted-foreground mt-0.5 text-xs">{time}</span>
    </div>
  </div>
);
