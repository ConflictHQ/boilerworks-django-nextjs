import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AtomIcon, CheckIcon } from "lucide-react";

const specs = [
  { label: "Context window", value: "1 000 000 tokens" },
  { label: "Max output", value: "16 384 tokens" },
  { label: "Speed", value: "~60 tokens / s" },
  { label: "Pricing tier", value: "Premium" },
];

const capabilities = [
  "Function calling",
  "Streaming",
  "System prompts",
  "JSON mode",
  "Tool use",
  "Vision",
  "Code execution",
  "Structured output",
  "Extended thinking",
];

const snippet = `import { Anthropic } from "@anthropic-ai/sdk";

const client = new Anthropic();

const response = await client.messages.create({
  model: "quantum-1",
  max_tokens: 4096,
  thinking: { type: "enabled", budget_tokens: 2000 },
  messages: [
    {
      role: "user",
      content: "Reason step-by-step through this complex problem…",
    },
  ],
});

console.log(response.content[0].text);`;

export default function QuantumPage() {
  return (
    <div className="flex max-w-3xl flex-1 flex-col gap-6 p-6">
      <div className="flex items-center gap-4">
        <div className="bg-primary/10 flex h-12 w-12 items-center justify-center rounded-xl">
          <AtomIcon className="text-primary h-6 w-6" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold">Quantum</h1>
          <p className="text-muted-foreground text-sm">
            Maximum capability for complex reasoning and long-context tasks.
          </p>
        </div>
      </div>

      <p className="text-muted-foreground text-sm leading-relaxed">
        Quantum is our most powerful model, built for tasks that demand deep reasoning, multi-step
        planning, and handling very long documents. Its one-million-token context window can
        accommodate entire codebases or lengthy research corpora. Extended thinking mode allows the
        model to reason internally before responding, dramatically improving accuracy on hard
        problems.
      </p>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Specifications</CardTitle>
        </CardHeader>
        <CardContent>
          <dl className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            {specs.map(({ label, value }) => (
              <div key={label}>
                <dt className="text-muted-foreground text-xs">{label}</dt>
                <dd className="mt-1 text-sm font-medium">{value}</dd>
              </div>
            ))}
          </dl>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Capabilities</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="flex flex-wrap gap-2">
            {capabilities.map((cap) => (
              <li key={cap} className="flex items-center gap-1.5 text-sm">
                <CheckIcon className="h-4 w-4 text-green-500" />
                {cap}
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">API usage</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="bg-muted overflow-x-auto rounded-md p-4 text-xs leading-relaxed">
            <code>{snippet}</code>
          </pre>
        </CardContent>
      </Card>
    </div>
  );
}
