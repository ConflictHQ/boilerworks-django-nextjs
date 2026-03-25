"use client";

import * as React from "react";
import { useTranslations } from "next-intl";

import { NavMain } from "@/components/NavMain";
import { NavProjects } from "@/components/NavProjects";
import { NavUser } from "@/components/NavUser";
import { TeamSwitcher } from "@/components/TeamSwitcher";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { ThemeToggle } from "@/components/ThemeToggle";
import type { CurrentUser } from "@/graphql/user/user.types";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
  SidebarSeparator,
} from "@/components/ui/sidebar";
import {
  GalleryVerticalEndIcon,
  TerminalSquareIcon,
  BotIcon,
  BookOpenIcon,
  Settings2Icon,
  TableIcon,
  ClipboardListIcon,
  ZapIcon,
  ShieldIcon,
} from "lucide-react";

const teams = [
  { name: "Boilerworks", logo: <GalleryVerticalEndIcon />, plan: "Enterprise" },
  {
    name: "Boilerworks",
    logo: <GalleryVerticalEndIcon />,
    plan: "Agency",
    url: "https://boilerworks.dev/",
  },
];

const projects: { name: string; url: string; icon: React.ReactNode }[] = [];

type AppSidebarProps = React.ComponentProps<typeof Sidebar> & {
  ssrUser: CurrentUser | null;
};

export function AppSidebar({ ssrUser, ...props }: AppSidebarProps) {
  const t = useTranslations("nav");

  const navMain = [
    {
      title: t("playground"),
      url: "/playground",
      icon: <TerminalSquareIcon />,
      items: [
        { title: t("history"), url: "/playground/history" },
        { title: t("starred"), url: "/playground/starred" },
        { title: t("settings"), url: "/settings" },
      ],
    },
    {
      title: t("models"),
      url: "/models",
      icon: <BotIcon />,
      items: [
        { title: t("genesis"), url: "/models/genesis" },
        { title: t("explorer"), url: "/models/explorer" },
        { title: t("quantum"), url: "/models/quantum" },
      ],
    },
    {
      title: t("documentation"),
      url: "/documentation/introduction",
      icon: <BookOpenIcon />,
      items: [
        { title: t("introduction"), url: "/documentation/introduction" },
        { title: t("getStarted"), url: "/documentation/get-started" },
        { title: t("tutorials"), url: "/documentation/tutorials" },
        { title: t("changelog"), url: "/documentation/changelog" },
      ],
    },
    {
      title: t("table"),
      url: "/table",
      icon: <TableIcon />,
    },
    {
      title: t("form"),
      url: "/form",
      icon: <ClipboardListIcon />,
    },
    {
      title: "Form Engine",
      url: "/forms",
      icon: <ClipboardListIcon />,
      items: [
        { title: "All Forms", url: "/forms" },
        { title: "Create New", url: "/forms/new" },
      ],
    },
    {
      title: "Workflows",
      url: "/workflows",
      icon: <ZapIcon />,
      items: [
        { title: "All Workflows", url: "/workflows" },
        { title: "New Workflow", url: "/workflows/new" },
      ],
    },
    {
      title: t("hooks"),
      url: "/hooks",
      icon: <ZapIcon />,
    },
    {
      title: t("secured"),
      url: "/secured",
      icon: <ShieldIcon />,
    },
    {
      title: t("settings"),
      url: "/settings",
      icon: <Settings2Icon />,
    },
  ];

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <TeamSwitcher teams={teams} />
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={navMain} />
        <NavProjects projects={projects} />
      </SidebarContent>
      <SidebarFooter>
        <LanguageSwitcher />
        <ThemeToggle />
        <SidebarSeparator />
        <NavUser ssrUser={ssrUser} />
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
}
