export default function IntroductionPage() {
  return (
    <article className="flex max-w-2xl flex-1 flex-col gap-6 p-6">
      <div>
        <h1 className="text-2xl font-semibold">Introduction</h1>
        <p className="text-muted-foreground mt-2 text-sm">Welcome to the platform documentation.</p>
      </div>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-medium">What is this platform?</h2>
        <p className="text-muted-foreground text-sm leading-relaxed">
          This platform gives you unified API access to our suite of language models — Genesis,
          Explorer, and Quantum. Whether you are building a customer-facing chatbot, an internal
          knowledge assistant, or a code-review pipeline, you can switch models without changing
          your integration code.
        </p>
        <p className="text-muted-foreground text-sm leading-relaxed">
          The platform handles authentication, rate limiting, and usage metering, so you can focus
          on building features rather than infrastructure. A single API key grants access to all
          models; billing is consolidated and shown on the dashboard.
        </p>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-medium">Key concepts</h2>
        <ul className="text-muted-foreground flex flex-col gap-2 text-sm">
          <li>
            <strong className="text-foreground">Models</strong> — the AI engines that power your
            completions. Each model has different capability / cost trade-offs.
          </li>
          <li>
            <strong className="text-foreground">Playground</strong> — an interactive interface to
            experiment with prompts before embedding them in code.
          </li>
          <li>
            <strong className="text-foreground">Sessions</strong> — a session groups related
            messages into a conversation. Sessions are persisted and can be revisited.
          </li>
          <li>
            <strong className="text-foreground">Tokens</strong> — the unit of consumption. One token
            is roughly four characters of English text.
          </li>
        </ul>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-medium">Architecture overview</h2>
        <p className="text-muted-foreground text-sm leading-relaxed">
          Requests flow from your application through our edge network to the model inference
          cluster. Responses are streamed back token-by-token over a Server-Sent Events connection,
          minimising time-to-first-token latency. All traffic is encrypted in transit and at rest.
        </p>
        <pre className="bg-muted overflow-x-auto rounded-md p-4 text-xs leading-relaxed">
          <code>{`Your app  →  Edge proxy  →  Auth & rate-limit  →  Model cluster
                                                          ↓
                                                     Streaming response`}</code>
        </pre>
      </section>
    </article>
  );
}
