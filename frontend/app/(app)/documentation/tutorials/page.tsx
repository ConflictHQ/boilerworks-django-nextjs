import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ClockIcon, ArrowRightIcon } from "lucide-react";
import { tutorials } from "./data";

const levelVariant = (level: string): "default" | "secondary" | "outline" =>
  level === "Beginner" ? "secondary" : level === "Advanced" ? "default" : "outline";

export default function TutorialsPage() {
  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <div>
        <h1 className="text-2xl font-semibold">Tutorials</h1>
        <p className="text-muted-foreground mt-2 text-sm">
          Step-by-step guides to help you build with the platform.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        {tutorials.map((t) => (
          <Link key={t.slug} href={`/documentation/tutorials/${t.slug}`} className="group">
            <Card className="flex h-full flex-col transition-colors group-hover:border-foreground/20">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between gap-2">
                  <Badge variant={levelVariant(t.level)}>{t.level}</Badge>
                  <span className="text-muted-foreground flex items-center gap-1 text-xs">
                    <ClockIcon className="h-3.5 w-3.5" />
                    {t.duration}
                  </span>
                </div>
                <CardTitle className="mt-2 text-base">{t.title}</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-1 flex-col justify-between gap-3">
                <CardDescription>{t.description}</CardDescription>
                <span className="text-muted-foreground group-hover:text-foreground flex items-center gap-1 text-xs transition-colors">
                  Read tutorial
                  <ArrowRightIcon className="h-3 w-3" />
                </span>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
