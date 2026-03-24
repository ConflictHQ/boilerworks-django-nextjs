import Link from "next/link";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ZapIcon, CompassIcon, AtomIcon } from "lucide-react";

const models = [
  {
    slug: "genesis",
    name: "Genesis",
    icon: ZapIcon,
    description: "Our flagship model. Balanced performance for a wide range of everyday tasks.",
    tags: ["General purpose", "Fast", "Cost-effective"],
  },
  {
    slug: "explorer",
    name: "Explorer",
    icon: CompassIcon,
    description: "Optimised for code generation, analysis, and technical reasoning.",
    tags: ["Code", "Analysis", "Structured output"],
  },
  {
    slug: "quantum",
    name: "Quantum",
    icon: AtomIcon,
    description: "Maximum capability model for complex reasoning and long-context tasks.",
    tags: ["Long context", "Reasoning", "Vision"],
  },
];

export default function ModelsPage() {
  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <div>
        <h1 className="text-xl font-semibold">Models</h1>
        <p className="text-muted-foreground mt-1 text-sm">
          Choose the right model for your use case.
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {models.map(({ slug, name, icon: Icon, description, tags }) => (
          <Card key={slug} className="flex flex-col">
            <CardHeader className="flex flex-row items-center gap-3">
              <div className="bg-primary/10 flex h-10 w-10 items-center justify-center rounded-lg">
                <Icon className="text-primary h-5 w-5" />
              </div>
              <CardTitle>{name}</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-1 flex-col gap-4">
              <CardDescription>{description}</CardDescription>
              <div className="flex flex-wrap gap-1">
                {tags.map((tag) => (
                  <Badge key={tag} variant="secondary">
                    {tag}
                  </Badge>
                ))}
              </div>
              <Button asChild variant="outline" className="mt-auto">
                <Link href={`/models/${slug}`}>View details</Link>
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
