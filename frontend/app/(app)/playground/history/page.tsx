import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

const sessions = [
  {
    date: "2026-02-23",
    prompt: "Explain zero-shot prompting in simple terms",
    model: "Genesis",
    tokens: 312,
    status: "completed",
  },
  {
    date: "2026-02-22",
    prompt: "Write a unit test for a TypeScript function that validates email",
    model: "Explorer",
    tokens: 541,
    status: "completed",
  },
  {
    date: "2026-02-22",
    prompt: "Summarise the key points from this research paper excerpt…",
    model: "Quantum",
    tokens: 1024,
    status: "completed",
  },
  {
    date: "2026-02-21",
    prompt: "Translate the following paragraph to Spanish",
    model: "Genesis",
    tokens: 198,
    status: "completed",
  },
  {
    date: "2026-02-21",
    prompt: "Generate SQL to find top 10 customers by revenue",
    model: "Explorer",
    tokens: 287,
    status: "completed",
  },
  {
    date: "2026-02-20",
    prompt: "Draft a product launch announcement email for our new API",
    model: "Genesis",
    tokens: 623,
    status: "completed",
  },
  {
    date: "2026-02-20",
    prompt: "What are the pros and cons of microservices?",
    model: "Quantum",
    tokens: 445,
    status: "completed",
  },
  {
    date: "2026-02-19",
    prompt: "Create a Python script to parse CSV files and output JSON",
    model: "Explorer",
    tokens: 789,
    status: "completed",
  },
  {
    date: "2026-02-18",
    prompt: "Review this code for security vulnerabilities",
    model: "Quantum",
    tokens: 932,
    status: "error",
  },
  {
    date: "2026-02-17",
    prompt: "List 10 creative names for a SaaS analytics product",
    model: "Genesis",
    tokens: 156,
    status: "completed",
  },
];

const statusVariant = (status: string) => (status === "completed" ? "default" : "destructive");

export default function PlaygroundHistoryPage() {
  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <div>
        <h1 className="text-xl font-semibold">History</h1>
        <p className="text-muted-foreground mt-1 text-sm">Past playground sessions.</p>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="overflow-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-muted/50 border-b">
                  <th className="px-4 py-3 text-left font-medium">Date</th>
                  <th className="px-4 py-3 text-left font-medium">Prompt</th>
                  <th className="px-4 py-3 text-left font-medium">Model</th>
                  <th className="px-4 py-3 text-right font-medium">Tokens</th>
                  <th className="px-4 py-3 text-left font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {sessions.map((s, i) => (
                  <tr key={i} className="hover:bg-muted/30 border-b last:border-0">
                    <td className="text-muted-foreground px-4 py-3 whitespace-nowrap">{s.date}</td>
                    <td className="max-w-xs truncate px-4 py-3">{s.prompt}</td>
                    <td className="px-4 py-3">
                      <Badge variant="outline">{s.model}</Badge>
                    </td>
                    <td className="px-4 py-3 text-right tabular-nums">{s.tokens}</td>
                    <td className="px-4 py-3">
                      <Badge variant={statusVariant(s.status)}>{s.status}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
