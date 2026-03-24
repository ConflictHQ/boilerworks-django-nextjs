"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BookOpenIcon, RocketIcon, GraduationCapIcon, ScrollIcon } from "lucide-react";

const navLinks = [
  { href: "/documentation/introduction", label: "Introduction", icon: BookOpenIcon },
  { href: "/documentation/get-started", label: "Get Started", icon: RocketIcon },
  { href: "/documentation/tutorials", label: "Tutorials", icon: GraduationCapIcon },
  { href: "/documentation/changelog", label: "Changelog", icon: ScrollIcon },
];

export default function DocumentationLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="flex flex-1">
      <aside className="hidden w-56 shrink-0 border-r lg:flex lg:flex-col">
        <div className="flex flex-col gap-1 p-4">
          <p className="text-muted-foreground mb-2 px-2 text-xs font-semibold tracking-wider uppercase">
            Documentation
          </p>
          {navLinks.map(({ href, label, icon: Icon }) => {
            const isActive = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                aria-current={isActive ? "page" : undefined}
                className={`flex items-center gap-2.5 rounded-md px-2 py-2 text-sm transition-colors ${
                  isActive
                    ? "bg-accent text-accent-foreground font-medium"
                    : "hover:bg-accent hover:text-accent-foreground text-muted-foreground"
                }`}
              >
                <Icon className="h-4 w-4 shrink-0" />
                {label}
              </Link>
            );
          })}
        </div>
      </aside>

      <div className="flex flex-1 flex-col">{children}</div>
    </div>
  );
}
