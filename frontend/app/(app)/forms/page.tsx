"use client";

import {
  Button,
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
  StatusBadge,
  type StatusTone,
} from "@calliopelabs/ui";
import Link from "next/link";
import { PlusIcon } from "lucide-react";
import { Separator } from "@/ui-app/primitives/separator";
import { Badge } from "@/ui-app/primitives/badge";
import { useFormDefinitions } from "@/graphql/forms/forms.hooks";

/** Form states on the library's status tones, once. */
const STATUS_TONE: Record<string, StatusTone> = {
  draft: "muted",
  published: "ok",
  archived: "warn",
};

export default function FormsPage() {
  const { forms, loading, error } = useFormDefinitions();

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title="Forms"
        description="Manage form definitions, view submissions, and publish forms."
        primaryAction={
          <Button asChild size="sm">
            <Link href="/forms/new">
              <PlusIcon />
              New Form
            </Link>
          </Button>
        }
      />
      <Separator />

      {loading && forms.length === 0 && <LoadingState label="Loading forms" />}

      {error && <ErrorState title="Could not load forms" error={error} />}

      {!loading && !error && forms.length === 0 && (
        <EmptyState
          title="No forms yet"
          description="Create your first form to get started."
          actionHref="/forms/new"
          actionLabel="New Form"
        />
      )}

      <div className="grid gap-4">
        {forms.map((form) => (
          <Link
            key={`${form.slug}-${form.version}`}
            href={`/forms/${form.slug}`}
            className="hover:bg-muted/50 flex items-center justify-between rounded-lg border p-4 transition-colors"
          >
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <span className="font-medium">{form.name}</span>
                <StatusBadge tone={STATUS_TONE[form.status] ?? "muted"}>{form.status}</StatusBadge>
                {form.isPublic && <Badge variant="outline">Public</Badge>}
              </div>
              <span className="text-muted-foreground text-sm">{form.description || form.slug}</span>
            </div>
            <div className="text-muted-foreground flex items-center gap-4 text-sm">
              <span>v{form.version}</span>
              <span>{form.submissionCount} submissions</span>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}
