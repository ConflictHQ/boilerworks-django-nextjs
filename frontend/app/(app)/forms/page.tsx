"use client";

import Link from "next/link";
import { Loader2Icon, PlusIcon } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useFormDefinitions } from "@/graphql/forms/forms.hooks";

const statusColors: Record<string, string> = {
  draft: "bg-gray-500",
  published: "bg-green-500",
  archived: "bg-yellow-500",
};

export default function FormsPage() {
  const { forms, loading, error } = useFormDefinitions();

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Forms</h1>
          <p className="text-muted-foreground mt-1 text-sm">
            Manage form definitions, view submissions, and publish forms.
          </p>
        </div>
        <Button asChild>
          <Link href="/forms/new">
            <PlusIcon className="mr-2 h-4 w-4" />
            New Form
          </Link>
        </Button>
      </div>
      <Separator />

      {loading && (
        <div className="flex items-center justify-center p-12">
          <Loader2Icon className="text-muted-foreground h-6 w-6 animate-spin" />
        </div>
      )}

      {error && (
        <div className="rounded-md bg-red-50 p-4 text-red-800">
          Error loading forms: {error.message}
        </div>
      )}

      {!loading && forms.length === 0 && (
        <div className="text-muted-foreground py-12 text-center">
          No forms yet. Create your first form to get started.
        </div>
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
                <Badge variant="secondary" className={`text-white ${statusColors[form.status] ?? "bg-gray-500"}`}>
                  {form.status}
                </Badge>
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
