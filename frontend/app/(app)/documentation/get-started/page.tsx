export default function GetStartedPage() {
  return (
    <article className="flex max-w-2xl flex-1 flex-col gap-6 p-6">
      <div>
        <h1 className="text-2xl font-semibold">Get Started</h1>
        <p className="text-muted-foreground mt-2 text-sm">Up and running in five minutes.</p>
      </div>

      <section className="flex flex-col gap-4">
        <div className="flex flex-col gap-2">
          <h2 className="text-lg font-medium">Step 1 — Start the stack</h2>
          <p className="text-muted-foreground text-sm leading-relaxed">
            The entire platform runs in Docker Compose. A single command brings up Postgres, Redis,
            OpenSearch, MinIO, Celery workers, the Django API, and the Next.js frontend.
          </p>
          <pre className="bg-muted overflow-x-auto rounded-md p-4 text-xs leading-relaxed">
            <code>{`make up        # start all containers
make build     # rebuild and start (after Dockerfile changes)
make ps        # check container status`}</code>
          </pre>
        </div>

        <div className="flex flex-col gap-2">
          <h2 className="text-lg font-medium">Step 2 — Run migrations</h2>
          <p className="text-muted-foreground text-sm leading-relaxed">
            Apply database migrations to set up the schema. If this is a fresh clone, you will also
            want to create a superuser for the admin panel.
          </p>
          <pre className="bg-muted overflow-x-auto rounded-md p-4 text-xs leading-relaxed">
            <code>{`make migrate
make superuser`}</code>
          </pre>
        </div>

        <div className="flex flex-col gap-2">
          <h2 className="text-lg font-medium">Step 3 — Seed development data</h2>
          <p className="text-muted-foreground text-sm leading-relaxed">
            Load numbered fixtures to populate the database with sample organizations, users,
            profiles, and permissions. Use the --flush flag to reset first.
          </p>
          <pre className="bg-muted overflow-x-auto rounded-md p-4 text-xs leading-relaxed">
            <code>{`make seed`}</code>
          </pre>
        </div>

        <div className="flex flex-col gap-2">
          <h2 className="text-lg font-medium">Step 4 — Explore the services</h2>
          <p className="text-muted-foreground text-sm leading-relaxed">
            With the stack running, all services are accessible on localhost. The Django admin
            includes a custom dark theme with import/export on every model.
          </p>
          <pre className="bg-muted overflow-x-auto rounded-md p-4 text-xs leading-relaxed">
            <code>{`Django API        http://localhost:8000
Next.js UI        http://localhost:3000
Django Admin      http://localhost:8000/app/admin/
GraphQL           http://localhost:8000/app/gql/config/
Mailpit           http://localhost:8025
MinIO Console     http://localhost:9001  (minioadmin/minioadmin)
Flower (Celery)   http://localhost:5555
OpenSearch        http://localhost:9200`}</code>
          </pre>
        </div>

        <div className="flex flex-col gap-2">
          <h2 className="text-lg font-medium">Step 5 — Run the checks</h2>
          <p className="text-muted-foreground text-sm leading-relaxed">
            Before committing any code, run the linter and test suite. The linter enforces PEP 8
            with a 140-character line limit via flake8 and isort. Tests run against a real Postgres
            and Redis.
          </p>
          <pre className="bg-muted overflow-x-auto rounded-md p-4 text-xs leading-relaxed">
            <code>{`make lint      # flake8 + isort checks
make test      # run Django test suite
make schema    # export GraphQL SDL`}</code>
          </pre>
        </div>
      </section>
    </article>
  );
}
