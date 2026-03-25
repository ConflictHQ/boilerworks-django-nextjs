export default function IntroductionPage() {
  return (
    <article className="flex max-w-2xl flex-1 flex-col gap-6 p-6">
      <div>
        <h1 className="text-2xl font-semibold">Introduction</h1>
        <p className="text-muted-foreground mt-2 text-sm">
          Welcome to the platform documentation.
        </p>
      </div>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-medium">What is this platform?</h2>
        <p className="text-muted-foreground text-sm leading-relaxed">
          This platform is a full-stack production boilerplate built on Django, Strawberry GraphQL,
          and Next.js. It ships with session-based auth, role permissions, Celery task processing,
          OpenSearch, file uploads via MinIO/S3, email via SES, feature flags, and a dark-themed
          admin — all wired together with Docker Compose and ready to extend.
        </p>
        <p className="text-muted-foreground text-sm leading-relaxed">
          The platform handles authentication, rate limiting, permissions, audit trails, and
          background processing so you can focus on building domain features rather than
          infrastructure. A single Docker Compose command brings up the entire stack locally.
        </p>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-medium">Key concepts</h2>
        <ul className="text-muted-foreground flex flex-col gap-2 text-sm">
          <li>
            <strong className="text-foreground">Tracking models</strong> — every business model
            inherits from Tracking, giving you created/updated/deleted timestamps, user attribution,
            version numbers, and full audit history via django-simple-history.
          </li>
          <li>
            <strong className="text-foreground">GUIDs over PKs</strong> — integer primary keys are
            never exposed in the API. All external references use UUID guid fields or Relay global
            IDs.
          </li>
          <li>
            <strong className="text-foreground">Soft deletes</strong> — business objects are never
            hard-deleted. Set deleted_at and deleted_by instead of calling .delete().
          </li>
          <li>
            <strong className="text-foreground">Permission checks</strong> — every GraphQL resolver
            and mutation begins with an auth check. Permissions are defined per-model and per-field,
            assigned to groups, never directly to users.
          </li>
          <li>
            <strong className="text-foreground">Strawberry GraphQL</strong> — the API layer uses
            Strawberry with django integration, async dataloaders, and a custom context providing
            user, organization, and cached permission state.
          </li>
        </ul>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-medium">Architecture overview</h2>
        <p className="text-muted-foreground text-sm leading-relaxed">
          Requests flow from the Next.js frontend through Apollo Client to the Django API. GraphQL
          queries hit Strawberry resolvers backed by the Django ORM, while background work is
          dispatched to Celery workers via Redis. All services run in Docker containers orchestrated
          by Compose.
        </p>
        <pre className="bg-muted overflow-x-auto rounded-md p-4 text-xs leading-relaxed">
          <code>{`Next.js (3000)  →  Apollo Client  →  Django API (8000)  →  Strawberry GQL
                                                                  ↓
                                              PostgreSQL ← ORM ← Resolvers → Celery → Redis
                                                                  ↓
                                              OpenSearch    MinIO/S3    Mailpit/SES`}</code>
        </pre>
      </section>

      <section className="flex flex-col gap-3">
        <h2 className="text-lg font-medium">App structure</h2>
        <ul className="text-muted-foreground flex flex-col gap-2 text-sm">
          <li>
            <strong className="text-foreground">auth1</strong> — session-based authentication, login
            views, rate limiting
          </li>
          <li>
            <strong className="text-foreground">core</strong> — User, Profile, Address,
            Notification, ResourceFile, OpenSearch, telemetry, signals
          </li>
          <li>
            <strong className="text-foreground">organization</strong> — Organization and
            OrganizationMember models, member status management
          </li>
          <li>
            <strong className="text-foreground">core_rule_engine</strong> — rule definitions,
            conditions, actions, model signal triggers
          </li>
          <li>
            <strong className="text-foreground">scheduled_task</strong> — DFA state machine,
            cron-scheduled transitions via Celery beat
          </li>
          <li>
            <strong className="text-foreground">testdata</strong> — dev fixtures and the seed
            management command
          </li>
        </ul>
      </section>
    </article>
  );
}
