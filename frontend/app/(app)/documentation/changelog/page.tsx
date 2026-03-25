import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

const entries = [
  {
    version: "1.12.0",
    date: "2026-03-25",
    type: "feature",
    changes: [
      "Easter egg: documentation pages now contain real Boilerworks platform docs.",
      "Tutorial pages are fully navigable with step-by-step code walkthroughs.",
    ],
  },
  {
    version: "1.11.0",
    date: "2026-03-20",
    type: "fix",
    changes: [
      "Replaced legacy Graphene test client with Strawberry-compatible wrapper.",
      "Removed legacy Graphene-era test files and snapshots.",
      "Updated README with history and contributing sections for open source launch.",
    ],
  },
  {
    version: "1.10.0",
    date: "2026-03-10",
    type: "feature",
    changes: [
      "Visual builders for forms and workflows with drag-and-drop canvas.",
      "Frontend workflow CRUD with auth gate and TagInput component.",
      "All (app) routes now gate-check authentication — redirect to /auth/login if not logged in.",
    ],
  },
  {
    version: "1.9.0",
    date: "2026-02-28",
    type: "fix",
    changes: [
      "Fixed auth callback to redirect to frontend instead of Django admin.",
      "Fixed health URL and admin header links.",
      "Fixed time picker, signature cursor, and validation errors in form widgets.",
      "Fixed hooks error in DynamicForm — use CSS hidden instead of return null.",
    ],
  },
  {
    version: "1.8.0",
    date: "2026-02-20",
    type: "feature",
    changes: [
      "Form widgets v2: 10 new and improved widget types.",
      "Fixed formDefinition query to return latest version for drafts, not just published.",
      "FormDefinitionType.description now nullable.",
    ],
  },
  {
    version: "1.7.0",
    date: "2026-02-10",
    type: "feature",
    changes: [
      "Form builder live preview panel with split layout.",
      "Resizable split pane using react-resizable-panels.",
      "Field type hints and explainer text in form builder.",
      "Form Builder v0.2: bug fixes and per-type configuration panels.",
    ],
  },
  {
    version: "1.6.0",
    date: "2026-01-30",
    type: "feature",
    changes: [
      "Visual builders: React Form Builder and Workflow Builder with Django admin JSON widgets.",
      "WorkflowDefinitionType.description now nullable, npm install fix in container.",
    ],
  },
  {
    version: "1.5.0",
    date: "2026-01-15",
    type: "feature",
    changes: [
      "Workflow Engine: DB-configurable state machines with Celery-driven transitions.",
      "Mutation audit log with frontend wiring updates.",
      "Agent interface: platform schema export and scaffold form/workflow commands.",
      "WebSocket subscriptions, form analytics, component config, and schema detection.",
    ],
  },
  {
    version: "1.4.0",
    date: "2025-12-20",
    type: "feature",
    changes: [
      "GraphQL health check endpoint and rate limiting.",
      "Client-side logic rule engine for DynamicForm conditional fields.",
      "Form create page: /forms/new with name, slug, and schema input.",
      "DynamicForm React component for rendering JSON Schema forms.",
    ],
  },
  {
    version: "1.3.0",
    date: "2025-12-05",
    type: "feature",
    changes: [
      "Form Engine wired into frontend with Apollo hooks.",
      "Modular feature toggles and run.sh commands.",
      "Public and anonymous form submissions.",
      "Form event notifications via Celery.",
      "Form file uploads and Django admin improvements.",
    ],
  },
  {
    version: "1.2.0",
    date: "2025-11-15",
    type: "feature",
    changes: [
      "Form Engine: versioned form definitions with JSON Schema validation.",
      "Test coverage pushed to 80% — 180 tests across resolvers, types, and mutations.",
      "Permission analysis tool and type resolver tests.",
      "Mutation integration tests and Flower added to Docker Compose.",
    ],
  },
  {
    version: "1.1.0",
    date: "2025-10-30",
    type: "feature",
    changes: [
      "Migrated GraphQL layer from Graphene to Strawberry.",
      "MinIO added to Docker Compose for local S3-compatible storage.",
      "Updated CI pipeline for Strawberry migration.",
      "Lint and schema export targets added to Makefile.",
      "Agent readiness: updated bootstrap.md and scaffold commands.",
    ],
  },
  {
    version: "1.0.0",
    date: "2025-10-01",
    type: "feature",
    changes: [
      "Initial Boilerworks release.",
      "Django API with Tracking base model — created/updated/deleted by+at, version, audit history.",
      "BaseCoreModel with GUID, slug, soft deletes — integer PKs never exposed.",
      "Session-based auth via auth1 with rate limiting.",
      "Celery worker + beat with Redis broker and DatabaseScheduler.",
      "OpenSearch integration with ProfileDocument and incremental indexing signals.",
      "MinIO for local S3-compatible file uploads, SES for production email.",
      "Django admin dark theme with BaseCoreAdmin, import/export on all models.",
      "Feature flags via django-constance with admin UI.",
      "Docker Compose: Postgres, Redis, OpenSearch, MinIO, Celery, Mailpit, Next.js UI.",
      "GitHub Actions CI: lint (pre-commit) and tests (Postgres + Redis services).",
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
