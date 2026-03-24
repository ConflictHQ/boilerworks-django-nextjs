import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { StarIcon } from "lucide-react";

const starred = [
  {
    title: "Unit test generator",
    prompt:
      "Write a comprehensive unit test suite for the following TypeScript function. Cover edge cases, null inputs, and boundary conditions.",
    model: "Explorer",
    date: "2026-02-20",
  },
  {
    title: "SQL optimiser",
    prompt:
      "Analyse this SQL query and suggest optimisations for performance. Identify missing indexes and rewrite subqueries where appropriate.",
    model: "Quantum",
    date: "2026-02-18",
  },
  {
    title: "Email drafter",
    prompt:
      "Draft a professional email to announce a new product feature. Tone should be enthusiastic but concise. Include a call to action.",
    model: "Genesis",
    date: "2026-02-15",
  },
  {
    title: "Code review checklist",
    prompt:
      "Review the following code diff and provide structured feedback: correctness, security, readability, and performance.",
    model: "Quantum",
    date: "2026-02-12",
  },
  {
    title: "Meeting summariser",
    prompt:
      "Summarise the following meeting transcript into bullet points grouped by topic. Highlight action items and owners.",
    model: "Genesis",
    date: "2026-02-10",
  },
  {
    title: "API documentation writer",
    prompt:
      "Generate OpenAPI-style documentation for the following endpoint, including descriptions, parameter types, and example responses.",
    model: "Explorer",
    date: "2026-02-08",
  },
];

export default function PlaygroundStarredPage() {
  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <div>
        <h1 className="text-xl font-semibold">Starred prompts</h1>
        <p className="text-muted-foreground mt-1 text-sm">Your saved prompt templates.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {starred.map((item) => (
          <Card key={item.title} className="flex flex-col">
            <CardHeader className="flex flex-row items-start justify-between gap-2 pb-2">
              <CardTitle className="text-base">{item.title}</CardTitle>
              <StarIcon className="h-4 w-4 shrink-0 fill-yellow-400 text-yellow-400" />
            </CardHeader>
            <CardContent className="flex flex-1 flex-col gap-3">
              <p className="text-muted-foreground line-clamp-3 text-sm">{item.prompt}</p>
              <div className="mt-auto flex items-center justify-between">
                <Badge variant="outline">{item.model}</Badge>
                <span className="text-muted-foreground text-xs">{item.date}</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
