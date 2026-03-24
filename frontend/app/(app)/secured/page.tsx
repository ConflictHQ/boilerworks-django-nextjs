import { Separator } from "@/components/ui/separator";
import { SecuredClientSection } from "./secured-client-section";

export default async function SecuredPage() {

  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <div>
        <h1 className="text-xl font-semibold">Secured page</h1>
        <p className="text-muted-foreground mt-1 text-sm">
          This page requires the <code className="font-mono">secured-page</code> permission. The
          server checked it before rendering — if the permission is inactive, Next.js served the 404
          page instead.
        </p>
      </div>
      <Separator />

      <div className="flex flex-col gap-2">
        <h2 className="text-sm font-semibold">Server guard</h2>
        <p className="text-muted-foreground text-sm">
          <code className="font-mono">requirePermission(PermissionSlug.SecuredPage)</code> ran in
          the RSC before this content was streamed. No client-side flicker.
        </p>
      </div>

      <Separator />

      <div className="flex flex-col gap-2">
        <h2 className="text-sm font-semibold">Client guard</h2>
        <p className="text-muted-foreground text-sm">
          The section below is wrapped with{" "}
          <code className="font-mono">withPermissionAuthenticationRequired</code>. It re-checks the
          permission on the client via Apollo.
        </p>
        <SecuredClientSection />
      </div>
    </div>
  );
}
