import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ClockIcon } from "lucide-react";

const tutorials = [
  {
    title: "Build a streaming chatbot",
    description:
      "Learn how to use the streaming API to display token-by-token output in a React UI. Covers SSE handling, abort signals, and error boundaries.",
    level: "Beginner",
    duration: "20 min",
  },
  {
    title: "Structured data extraction",
    description:
      "Use JSON mode and function calling to reliably extract typed entities from unstructured text. Includes a real-world invoice parsing example.",
    level: "Intermediate",
    duration: "35 min",
  },
  {
    title: "RAG with vector search",
    description:
      "Connect a vector database to give your model access to a private knowledge base. Step-by-step guide using pgvector and Next.js server actions.",
    level: "Intermediate",
    duration: "50 min",
  },
  {
    title: "Multi-turn conversations",
    description:
      "Manage conversation state server-side to build stateful chat applications. Includes session persistence, context truncation, and summarisation.",
    level: "Intermediate",
    duration: "30 min",
  },
  {
    title: "Agentic tool use",
    description:
      "Give your model tools it can invoke — web search, code execution, and database queries. Understand the tool-use loop and handle errors gracefully.",
    level: "Advanced",
    duration: "60 min",
  },
  {
    title: "Fine-tuning with RLHF data",
    description:
      "Prepare a preference dataset and submit a fine-tuning job via the API. Monitor progress and evaluate the resulting checkpoint against the base model.",
    level: "Advanced",
    duration: "90 min",
  },
];

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
          <Card key={t.title} className="flex flex-col">
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
            <CardContent>
              <CardDescription>{t.description}</CardDescription>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
