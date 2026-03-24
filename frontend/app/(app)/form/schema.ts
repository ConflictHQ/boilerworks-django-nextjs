import { z } from "zod";

export const userFormSchema = z.object({
  username: z.string().min(3, "Username must be at least 3 characters"),
  email: z.string().email("Invalid email address"),
  displayName: z.string().min(1, "Display name is required"),
  role: z.enum(["admin", "member", "viewer"], {
    message: "Please select a role",
  }),
  bio: z.string().max(300, "Bio must be 300 characters or less").optional(),
});

export type UserFormValues = z.infer<typeof userFormSchema>;
