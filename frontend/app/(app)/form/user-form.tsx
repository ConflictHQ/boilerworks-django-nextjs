"use client";

import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { userFormSchema, type UserFormValues } from "./schema";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Field, FieldLabel, FieldDescription, FieldError, FieldGroup } from "@/components/ui/field";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";

const SectionHeader = ({ title, description }: { title: string; description: string }) => (
  <div className="col-span-full md:col-span-1">
    <h2 className="text-sm font-medium">{title}</h2>
    <p className="text-muted-foreground mt-0.5 text-sm">{description}</p>
  </div>
);

export const UserForm = () => {
  const {
    register,
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<UserFormValues>({
    resolver: zodResolver(userFormSchema),
    defaultValues: {
      username: "",
      email: "",
      displayName: "",
      role: "member",
      bio: "",
    },
  });

  const onSubmit = async (_: UserFormValues) => {
    try {
      await new Promise((r) => setTimeout(r, 800));
      reset();
      toast.success("Profile saved", { description: "Your changes have been saved." });
    } catch {
      toast.error("Something went wrong", { description: "Please try again." });
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-8">
      {/* Identity section */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <SectionHeader
          title="Identity"
          description="Basic account information visible across the application."
        />
        <div className="col-span-full md:col-span-2">
          <FieldGroup>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <Field data-invalid={!!errors.username}>f
                <FieldLabel htmlFor="username">Username</FieldLabel>
                <Input
                  id="username"
                  placeholder="johndoe"
                  aria-invalid={!!errors.username}
                  {...register("username")}
                />
                <FieldError errors={[errors.username]} />
              </Field>

              <Field data-invalid={!!errors.displayName}>
                <FieldLabel htmlFor="displayName">Display name</FieldLabel>
                <Input
                  id="displayName"
                  placeholder="John Doe"
                  aria-invalid={!!errors.displayName}
                  {...register("displayName")}
                />
                <FieldError errors={[errors.displayName]} />
              </Field>
            </div>

            <Field data-invalid={!!errors.email}>
              <FieldLabel htmlFor="email">Email</FieldLabel>
              <Input
                id="email"
                type="email"
                placeholder="john@example.com"
                aria-invalid={!!errors.email}
                {...register("email")}
              />
              <FieldError errors={[errors.email]} />
            </Field>
          </FieldGroup>
        </div>
      </div>

      <Separator />

      {/* Access section */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <SectionHeader
          title="Access"
          description="Controls what this user can view and do in the application."
        />
        <div className="col-span-full md:col-span-2">
          <FieldGroup>
            <Field data-invalid={!!errors.role}>
              <FieldLabel htmlFor="role">Role</FieldLabel>
              <FieldDescription>
                Admins have full access. Members can edit. Viewers are read-only.
              </FieldDescription>
              <Controller
                name="role"
                control={control}
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger id="role" aria-invalid={!!errors.role} className="w-48">
                      <SelectValue placeholder="Select a role" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="admin">Admin</SelectItem>
                      <SelectItem value="member">Member</SelectItem>
                      <SelectItem value="viewer">Viewer</SelectItem>
                    </SelectContent>
                  </Select>
                )}
              />
              <FieldError errors={[errors.role]} />
            </Field>
          </FieldGroup>
        </div>
      </div>

      <Separator />

      {/* Profile section */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <SectionHeader
          title="Profile"
          description="Additional public information shown on the user's profile."
        />
        <div className="col-span-full md:col-span-2">
          <FieldGroup>
            <Field data-invalid={!!errors.bio}>
              <FieldLabel htmlFor="bio">Bio</FieldLabel>
              <FieldDescription>Max 300 characters.</FieldDescription>
              <Textarea
                id="bio"
                placeholder="Tell us a little about this user…"
                rows={4}
                aria-invalid={!!errors.bio}
                {...register("bio")}
              />
              <FieldError errors={[errors.bio]} />
            </Field>
          </FieldGroup>
        </div>
      </div>

      <Separator />

      {/* Actions */}
      <div className="flex items-center justify-end">
        <div className="flex items-center gap-3">
          <Button type="button" variant="outline" onClick={() => reset()}>
            Reset
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Saving…" : "Save changes"}
          </Button>
        </div>
      </div>
    </form>
  );
};
