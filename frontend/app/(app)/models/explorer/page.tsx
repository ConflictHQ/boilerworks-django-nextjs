import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CompassIcon, CheckIcon } from "lucide-react";

const specs = [
  { label: "Context window", value: "200 000 tokens" },
  { label: "Max output", value: "8 192 tokens" },
  { label: "Speed", value: "~120 tokens / s" },
  { label: "Pricing tier", value: "Standard" },
];

const capabilities = [
  "Function calling",
  "Streaming",
  "System prompts",
  "JSON mode",
  "Tool use",
  "Code execution",
  "Structured output",
];

const snippet = `import { Anthropic } from "@anthropic-ai/sdk";

const client = new Anthropic();

const response = await client.messages.create({
  model: "explorer-1",
  max_tokens: 2048,
  messages: [
    {
      role: "user",
      content: "Write a TypeScript function that validates an email address.",
    },
  ],
});

console.log(response.content[0].text);`;

export default function ExplorerPage() {
  return (
    <div className="flex max-w-3xl flex-1 flex-col gap-6 p-6">
      <div className="flex items-center gap-4">
        <div className="bg-primary/10 flex h-12 w-12 items-center justify-center rounded-xl">
          <CompassIcon className="text-primary h-6 w-6" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold">Explorer</h1>
          <p className="text-muted-foreground text-sm">
            Optimised for code generation, analysis, and technical reasoning.
          </p>
        </div>
      </div>

      <p className="text-muted-foreground text-sm leading-relaxed">
        Explorer excels at software engineering tasks: writing, reviewing, and explaining code
        across all major languages. Its extended context window makes it ideal for analysing large
        codebases or processing lengthy technical documents. Structured output mode lets you extract
        typed data reliably from unstructured input.
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
