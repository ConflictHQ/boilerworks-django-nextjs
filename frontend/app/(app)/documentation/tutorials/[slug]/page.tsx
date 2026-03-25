import { notFound } from "next/navigation";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ArrowLeftIcon, ClockIcon } from "lucide-react";
import { tutorials } from "../data";

const levelVariant = (level: string): "default" | "secondary" | "outline" =>
  level === "Beginner" ? "secondary" : level === "Advanced" ? "default" : "outline";

export function generateStaticParams() {
  return tutorials.map((t) => ({ slug: t.slug }));
}

export default async function TutorialPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const tutorial = tutorials.find((t) => t.slug === slug);

  if (!tutorial) notFound();

  return (
    <article className="flex max-w-2xl flex-1 flex-col gap-6 p-6">
      <div>
        <Link
          href="/documentation/tutorials"
          className="text-muted-foreground hover:text-foreground mb-4 inline-flex items-center gap-1.5 text-sm transition-colors"
        >
          <ArrowLeftIcon className="h-3.5 w-3.5" />
          Back to tutorials
        </Link>
        <h1 className="text-2xl font-semibold">{tutorial.title}</h1>
        <p className="text-muted-foreground mt-2 text-sm">{tutorial.description}</p>
        <div className="mt-3 flex items-center gap-3">
          <Badge variant={levelVariant(tutorial.level)}>{tutorial.level}</Badge>
          <span className="text-muted-foreground flex items-center gap-1 text-xs">
            <ClockIcon className="h-3.5 w-3.5" />
            {tutorial.duration}
          </span>
        </div>
      </div>

      <Separator />

      <div className="flex flex-col gap-8">
        {tutorial.steps.map((step, i) => (
          <section key={i} className="flex flex-col gap-3">
            <h2 className="text-lg font-medium">
              <span className="text-muted-foreground mr-2 font-normal">Step {i + 1}.</span>
              {step.title}
            </h2>
            <p className="text-muted-foreground text-sm leading-relaxed">{step.body}</p>
            {step.code && (
              <pre className="bg-muted overflow-x-auto rounded-md p-4 text-xs leading-relaxed">
                <code>{step.code}</code>
              </pre>
            )}
          </section>
        ))}
      </div>
    </article>
  );
}
