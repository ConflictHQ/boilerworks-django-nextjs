import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

const entries = [
  {
    version: "2.4.0",
    date: "2026-02-17",
    type: "feature",
    changes: [
      "Added Quantum model with 1M-token context window and extended thinking mode.",
      "Streaming responses now include usage statistics in the final chunk.",
      "Playground: starred prompts are now synced across devices.",
    ],
  },
  {
    version: "2.3.2",
    date: "2026-01-30",
    type: "fix",
    changes: [
      "Fixed a race condition in the streaming parser that could drop the last token.",
      "Resolved an issue where the API key rotation dialog closed prematurely on mobile.",
    ],
  },
  {
    version: "2.3.0",
    date: "2026-01-15",
    type: "feature",
    changes: [
      "Introduced structured output mode (JSON schema enforcement) for all models.",
      "Dashboard now shows per-model token usage breakdown.",
      "Explorer model upgraded: improved code generation accuracy on benchmarks by 18%.",
    ],
  },
  {
    version: "2.2.1",
    date: "2025-12-20",
    type: "fix",
    changes: [
      "Pagination in the History table now preserves applied filters.",
      "Fixed incorrect token count displayed for streamed responses.",
    ],
  },
  {
    version: "2.2.0",
    date: "2025-12-05",
    type: "feature",
    changes: [
      "Tool use (function calling) is now generally available for all models.",
      "Added multi-modal support to Quantum: images can be included in message content.",
      "New Changelog page in the documentation section.",
    ],
  },
  {
    version: "2.1.0",
    date: "2025-11-10",
    type: "feature",
    changes: [
      "Launched Explorer model, optimised for code and structured data tasks.",
      "API key management: rotate, revoke, and label keys from the Settings page.",
      "Rate limit headers now included in every API response.",
    ],
  },
];

const typeVariant = (type: string): "default" | "secondary" | "destructive" =>
  type === "feature" ? "default" : type === "fix" ? "secondary" : "destructive";

export default function ChangelogPage() {
  return (
    <article className="flex max-w-2xl flex-1 flex-col gap-6 p-6">
      <div>
        <h1 className="text-2xl font-semibold">Changelog</h1>
        <p className="text-muted-foreground mt-2 text-sm">
          New features and fixes, most recent first.
        </p>
      </div>

      <div className="flex flex-col gap-8">
        {entries.map((entry, i) => (
          <div key={entry.version}>
            {i > 0 && <Separator className="mb-8" />}
            <div className="mb-3 flex items-center gap-3">
              <span className="text-base font-semibold">v{entry.version}</span>
              <Badge variant={typeVariant(entry.type)}>{entry.type}</Badge>
              <span className="text-muted-foreground ml-auto text-xs">{entry.date}</span>
            </div>
            <ul className="flex flex-col gap-1.5">
              {entry.changes.map((c) => (
                <li key={c} className="text-muted-foreground flex gap-2 text-sm">
                  <span className="bg-muted-foreground mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full" />
                  {c}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </article>
  );
}
