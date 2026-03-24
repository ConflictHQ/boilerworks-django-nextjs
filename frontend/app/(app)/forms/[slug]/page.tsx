"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { Loader2Icon, SendIcon, PenLineIcon } from "lucide-react";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useFormDefinition, useFormSubmissions, usePublishForm, useArchiveForm } from "@/graphql/forms/forms.hooks";
import { toast } from "sonner";

export default function FormDetailPage() {
  const { slug } = useParams<{ slug: string }>();
  const { form, loading, error } = useFormDefinition(slug);
  const { submissions, loading: subsLoading } = useFormSubmissions(slug);
  const [publishForm] = usePublishForm();
  const [archiveForm] = useArchiveForm();

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center p-6">
        <Loader2Icon className="text-muted-foreground h-6 w-6 animate-spin" />
      </div>
    );
  }

  if (error || !form) {
    return (
      <div className="flex flex-1 flex-col gap-6 p-6">
        <div className="rounded-md bg-red-50 p-4 text-red-800">
          {error ? `Error: ${error.message}` : `No published form found for "${slug}"`}
        </div>
      </div>
    );
  }

  const handlePublish = async () => {
    const { data } = await publishForm({ variables: { slug } });
    if (data?.publishForm?.ok) {
      toast.success("Form published");
    } else {
      toast.error("Failed to publish");
    }
  };

  const handleArchive = async () => {
    const { data } = await archiveForm({ variables: { slug } });
    if (data?.archiveForm?.ok) {
      toast.success("Form archived");
    } else {
      toast.error("Failed to archive");
    }
  };

  const schemaProperties = (form.schema as Record<string, unknown>)?.properties as Record<string, unknown> | undefined;
  const fieldCount = schemaProperties ? Object.keys(schemaProperties).length : 0;

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-semibold">{form.name}</h1>
            <Badge variant={form.status === "published" ? "default" : "secondary"}>
              {form.status}
            </Badge>
            <span className="text-muted-foreground text-sm">v{form.version}</span>
          </div>
          <p className="text-muted-foreground mt-1 text-sm">{form.description}</p>
        </div>
        <div className="flex gap-2">
          {form.status === "published" && (
            <Button asChild>
              <Link href={`/forms/${slug}/submit`}>
                <PenLineIcon className="mr-2 h-4 w-4" /> Fill Out
              </Link>
            </Button>
          )}
          {form.status === "draft" && (
            <Button onClick={handlePublish}>
              <SendIcon className="mr-2 h-4 w-4" /> Publish
            </Button>
          )}
          {form.status === "published" && (
            <Button variant="outline" onClick={handleArchive}>Archive</Button>
          )}
        </div>
      </div>
      <Separator />

      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <div className="rounded-lg border p-4">
          <h3 className="text-sm font-medium">Fields</h3>
          <p className="text-2xl font-bold">{fieldCount}</p>
        </div>
        <div className="rounded-lg border p-4">
          <h3 className="text-sm font-medium">Submissions</h3>
          <p className="text-2xl font-bold">{form.submissionCount}</p>
        </div>
        <div className="rounded-lg border p-4">
          <h3 className="text-sm font-medium">Published</h3>
          <p className="text-muted-foreground text-sm">
            {form.publishedAt ? new Date(form.publishedAt).toLocaleDateString() : "Not yet"}
          </p>
        </div>
      </div>

      <div>
        <h2 className="mb-3 text-lg font-semibold">Schema</h2>
        <pre className="bg-muted max-h-96 overflow-auto rounded-lg p-4 text-sm">
          {JSON.stringify(form.schema, null, 2)}
        </pre>
      </div>

      <div>
        <h2 className="mb-3 text-lg font-semibold">Submissions ({submissions.length})</h2>
        {subsLoading ? (
          <Loader2Icon className="text-muted-foreground h-4 w-4 animate-spin" />
        ) : submissions.length === 0 ? (
          <p className="text-muted-foreground text-sm">No submissions yet.</p>
        ) : (
          <div className="space-y-2">
            {submissions.map((sub, i) => (
              <div key={i} className="flex items-center justify-between rounded-lg border p-3">
                <pre className="text-xs">{JSON.stringify(sub.payload, null, 2)}</pre>
                <div className="flex flex-col items-end gap-1">
                  <Badge variant="outline">{sub.status}</Badge>
                  <span className="text-muted-foreground text-xs">
                    {new Date(sub.submittedAt).toLocaleString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
