/**
 * The app as a product of @calliopelabs/ui: its brand (name, accent, sidebar
 * colour, grounds) and its navigation model. AppearanceScript, the
 * AppearanceProvider and the shell all read this one definition.
 *
 * A generated app renames the product here: `id` (a lowercase slug, also the
 * appearance storage namespace), `name` (what the brand mark shows), and,
 * if it wants, the accent and sidebar. A shipped brand works too:
 * `defineProduct({ ...astroliftBrand, nav: NAV })`.
 */
import { defineProduct, type NavModel } from "@calliopelabs/ui";
import {
  BookOpenIcon,
  BotIcon,
  ClipboardListIcon,
  FlaskConicalIcon,
  HistoryIcon,
  LayoutDashboardIcon,
  ScrollTextIcon,
  Settings2Icon,
  ShieldIcon,
  StarIcon,
  TableIcon,
  TerminalSquareIcon,
  WorkflowIcon,
  ZapIcon,
} from "lucide-react";

/**
 * Areas hold the sidebar's rows (functions). A row's `key` is also its
 * message key in the `nav` namespace (messages/*.json), so the sidebar and
 * the breadcrumb are translated through `localizeNav`. Add `requires` to a
 * row to show it only to people with that capability.
 */
export const NAV: NavModel = [
  {
    key: "home",
    label: "Home",
    icon: LayoutDashboardIcon,
    flat: true,
    groups: [
      {
        functions: [
          { key: "dashboard", label: "Dashboard", href: "/dashboard", icon: LayoutDashboardIcon },
        ],
      },
    ],
  },
  {
    key: "build",
    label: "Build",
    icon: ClipboardListIcon,
    groups: [
      {
        functions: [
          { key: "forms", label: "Forms", href: "/forms", icon: ClipboardListIcon },
          { key: "workflows", label: "Workflows", href: "/workflows", icon: WorkflowIcon },
          { key: "table", label: "Table", href: "/table", icon: TableIcon },
          { key: "form", label: "Form", href: "/form", icon: ClipboardListIcon },
          { key: "hooks", label: "Hooks", href: "/hooks", icon: ZapIcon },
        ],
      },
    ],
  },
  {
    key: "playground",
    label: "Playground",
    icon: TerminalSquareIcon,
    groups: [
      {
        functions: [
          { key: "playground", label: "Playground", href: "/playground", icon: TerminalSquareIcon },
          { key: "history", label: "History", href: "/playground/history", icon: HistoryIcon },
          { key: "starred", label: "Starred", href: "/playground/starred", icon: StarIcon },
        ],
      },
    ],
  },
  {
    key: "models",
    label: "Models",
    icon: BotIcon,
    groups: [
      {
        functions: [
          { key: "models", label: "Models", href: "/models", icon: BotIcon },
          { key: "genesis", label: "Genesis", href: "/models/genesis", icon: FlaskConicalIcon },
          { key: "explorer", label: "Explorer", href: "/models/explorer", icon: FlaskConicalIcon },
          { key: "quantum", label: "Quantum", href: "/models/quantum", icon: FlaskConicalIcon },
        ],
      },
    ],
  },
  {
    key: "documentation",
    label: "Documentation",
    icon: BookOpenIcon,
    groups: [
      {
        functions: [
          {
            key: "introduction",
            label: "Introduction",
            href: "/documentation/introduction",
            icon: BookOpenIcon,
          },
          {
            key: "getStarted",
            label: "Get Started",
            href: "/documentation/get-started",
            icon: BookOpenIcon,
          },
          {
            key: "tutorials",
            label: "Tutorials",
            href: "/documentation/tutorials",
            icon: BookOpenIcon,
          },
          {
            key: "changelog",
            label: "Changelog",
            href: "/documentation/changelog",
            icon: ScrollTextIcon,
          },
        ],
      },
    ],
  },
  {
    key: "admin",
    label: "Admin",
    icon: Settings2Icon,
    groups: [
      {
        functions: [
          { key: "settings", label: "Settings", href: "/settings", icon: Settings2Icon },
          { key: "secured", label: "Secured page", href: "/secured", icon: ShieldIcon },
        ],
      },
    ],
  },
];

export const product = defineProduct({
  id: "boilerworks",
  name: "Boilerworks",
  accent: "periwinkle",
  sidebar: "#16181d",
  grounds: ["black", "charcoal", "graphite", "paper", "mist"],
  defaultGround: { dark: "graphite", light: "mist" },
  nav: NAV,
});
