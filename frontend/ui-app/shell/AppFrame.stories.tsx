import { PageHeader } from "@calliopelabs/ui";
import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { BadgeCheckIcon, BellIcon } from "lucide-react";

import { NAV } from "@/ui-app/product";

import { AppFrame } from "./AppFrame";

/**
 * The signed-in frame: the library's AppShell, Sidebar, BrandMark and
 * UserMenu with the product's navigation, and the breadcrumb read from it.
 * `[` folds the sidebar; below `md` it opens as a drawer from the top bar.
 */
const meta = {
  title: "App/Shell/AppFrame",
  component: AppFrame,
  parameters: { layout: "fullscreen" },
  args: {
    nav: NAV,
    pathname: "/dashboard",
    user: { name: "Ada Lovelace", email: "ada@example.com" },
    menu: [
      [
        { label: "Account", icon: BadgeCheckIcon, onSelect: () => {} },
        { label: "Notifications", icon: BellIcon, onSelect: () => {} },
      ],
      [{ label: "Settings", href: "/settings" }],
    ],
    onSignOut: () => {},
    children: null,
  },
  render: (args) => (
    <div className="h-[640px]">
      <AppFrame {...args}>
        <div className="p-6">
          <PageHeader title="Dashboard" description="What changed since you last looked." />
        </div>
      </AppFrame>
    </div>
  ),
} satisfies Meta<typeof AppFrame>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Home: Story = {};

/** A row inside an area: the first crumb switches between the area's rows. */
export const InArea: Story = { args: { pathname: "/workflows" } };

/** A page below its row (/forms/<slug>): the row's crumb links back to it. */
export const BelowARow: Story = {
  args: { pathname: "/forms/customer-intake", pageLabel: () => "Customer intake" },
};

export const LongName: Story = {
  args: {
    user: {
      name: "Maximiliana Alexandrina von Hohenzollern-Sigmaringen",
      email: "maximiliana.alexandrina@a-very-long-company-domain.example.com",
    },
  },
};
