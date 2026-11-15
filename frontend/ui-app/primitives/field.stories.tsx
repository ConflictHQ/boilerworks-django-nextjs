import { Input } from "@calliopelabs/ui";
import type { Meta, StoryObj } from "@storybook/nextjs-vite";

import {
  Field,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
  FieldLegend,
  FieldSet,
} from "./field";

/** A form field: label, control, help and error, wired for screen readers. */
const meta = { title: "App/Primitives/Field", component: Field } satisfies Meta<typeof Field>;
export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <FieldSet className="max-w-sm">
      <FieldLegend>Profile</FieldLegend>
      <FieldGroup>
        <Field>
          <FieldLabel htmlFor="name">Name</FieldLabel>
          <Input id="name" placeholder="Ada Lovelace" />
          <FieldDescription>As it appears to your team.</FieldDescription>
        </Field>
        <Field data-invalid>
          <FieldLabel htmlFor="email">Email</FieldLabel>
          <Input id="email" aria-invalid defaultValue="ada@" />
          <FieldError>Enter a complete email address.</FieldError>
        </Field>
      </FieldGroup>
    </FieldSet>
  ),
};
