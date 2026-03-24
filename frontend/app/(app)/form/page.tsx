import { Separator } from "@/components/ui/separator";
import { UserForm } from "./user-form";

export default function FormPage() {
  return (
    <div className="flex flex-1 flex-col gap-6 p-6">
      <div>
        <h1 className="text-xl font-semibold">User management</h1>
        <p className="text-muted-foreground mt-1 text-sm">
          Manage user account details, role, and profile information.
        </p>
      </div>
      <Separator />
      <UserForm />
    </div>
  );
}
