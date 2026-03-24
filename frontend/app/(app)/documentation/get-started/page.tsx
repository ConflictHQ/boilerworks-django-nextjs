export default function GetStartedPage() {
  return (
    <article className="flex max-w-2xl flex-1 flex-col gap-6 p-6">
      <div>
        <h1 className="text-2xl font-semibold">Get Started</h1>
        <p className="text-muted-foreground mt-2 text-sm">Up and running in five minutes.</p>
      </div>

      <section className="flex flex-col gap-4">
        <div className="flex flex-col gap-2">
          <h2 className="text-lg font-medium">Step 1 — Create an account</h2>
          <p className="text-muted-foreground text-sm leading-relaxed">
            Sign up at the login page. Once authenticated, you will land on the dashboard. Your
            account comes with a free-tier allowance so you can explore the API without adding a
            payment method.
          </p>
        </div>

        <div className="flex flex-col gap-2">
          <h2 className="text-lg font-medium">Step 2 — Obtain your API key</h2>
          <p className="text-muted-foreground text-sm leading-relaxed">
            Navigate to <strong>Settings → Billing</strong> and click <em>Generate API key</em>.
            Store it securely — it will not be shown again. Treat it like a password.
          </p>
          <pre className="bg-muted overflow-x-auto rounded-md p-4 text-xs leading-relaxed">
            <code>{`export API_KEY="sk-platform-xxxxxxxxxxxxxxxxxxxxxxxx"`}</code>
          </pre>
        </div>

        <div className="flex flex-col gap-2">
          <h2 className="text-lg font-medium">Step 3 — Install the SDK</h2>
          <p className="text-muted-foreground text-sm leading-relaxed">
            The official SDK is available on npm and supports both Node.js and browser environments.
          </p>
          <pre className="bg-muted overflow-x-auto rounded-md p-4 text-xs leading-relaxed">
            <code>{`npm install @anthropic-ai/sdk`}</code>
          </pre>
        </div>

        <div className="flex flex-col gap-2">
          <h2 className="text-lg font-medium">Step 4 — Send your first message</h2>
          <p className="text-muted-foreground text-sm leading-relaxed">
            The snippet below sends a single user message and prints the assistant reply.
          </p>
          <pre className="bg-muted overflow-x-auto rounded-md p-4 text-xs leading-relaxed">
            <code>{`import { Anthropic } from "@anthropic-ai/sdk";

const client = new Anthropic({ apiKey: process.env.API_KEY });

const msg = await client.messages.create({
  model: "genesis-1",
  max_tokens: 256,
  messages: [{ role: "user", content: "What can you help me with?" }],
});

console.log(msg.content[0].text);`}</code>
          </pre>
        </div>

        <div className="flex flex-col gap-2">
          <h2 className="text-lg font-medium">Step 5 — Explore the Playground</h2>
          <p className="text-muted-foreground text-sm leading-relaxed">
            Before committing to a model and prompt, use the <strong>Playground</strong> to iterate
            interactively. You can star prompts that work well and revisit them from the Starred
            page.
          </p>
        </div>
      </section>
    </article>
  );
}
