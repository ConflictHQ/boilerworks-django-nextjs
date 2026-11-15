import { PageHeader } from "@calliopelabs/ui";
import { Separator } from "@/ui-app/primitives/separator";
import { UserForm } from "./user-form";

export default function FormPage() {
  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <PageHeader
        title="User management"
        description="Manage user account details, role, and profile information."
      />
      <Separator />
      <UserForm />
    </div>
  );
}
