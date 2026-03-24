import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ZapIcon, CheckIcon } from "lucide-react";

const specs = [
  { label: "Context window", value: "128 000 tokens" },
  { label: "Max output", value: "4 096 tokens" },
  { label: "Speed", value: "~180 tokens / s" },
  { label: "Pricing tier", value: "Standard" },
];

const capabilities = ["Function calling", "Streaming", "System prompts", "JSON mode", "Tool use"];

const snippet = `import { Anthropic } from "@anthropic-ai/sdk";

const client = new Anthropic();

const response = await client.messages.create({
  model: "genesis-1",
  max_tokens: 1024,
  messages: [{ role: "user", content: "Hello, Genesis!" }],
});

console.log(response.content[0].text);`;

export default function GenesisPage() {
  return (
    <div className="flex max-w-3xl flex-1 flex-col gap-6 p-6">
      <div className="flex items-center gap-4">
        <div className="bg-primary/10 flex h-12 w-12 items-center justify-center rounded-xl">
          <ZapIcon className="text-primary h-6 w-6" />
        </div>
        <div>
          <h1 className="text-2xl font-semibold">Genesis</h1>
          <p className="text-muted-foreground text-sm">
            Our flagship general-purpose model, optimised for speed and cost.
          </p>
        </div>
      </div>

      <p className="text-muted-foreground text-sm leading-relaxed">
        Genesis is designed to handle a broad spectrum of tasks — from drafting content and
        answering questions to summarising documents and light reasoning. It offers an excellent
        balance between capability, latency, and cost, making it the default choice for most
        production workloads.
      </p>

      {/* Specs */}
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

      {/* Capabilities */}
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

      {/* Usage */}
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
