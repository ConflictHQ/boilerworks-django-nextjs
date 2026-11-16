import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { expect, waitFor, within } from "storybook/test";

import { SupersetDashboard } from "./SupersetDashboard";

const meta = {
  title: "App/Analytics/SupersetDashboard",
  component: SupersetDashboard,
  args: {
    title: "Revenue overview",
    embeddedId: "00000000-0000-4000-8000-000000000000",
    supersetDomain: "https://superset.example.com",
    height: 320,
    // Never settles, so the story holds the loading state.
    fetchGuestToken: () => new Promise<string>(() => {}),
  },
} satisfies Meta<typeof SupersetDashboard>;
export default meta;
type Story = StoryObj<typeof meta>;

/** Waiting for the backend's guest token and the iframe handshake. */
export const Loading: Story = {
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await waitFor(() =>
      expect(canvas.getByRole("status")).toHaveTextContent("Loading Revenue overview")
    );
  },
};

/** The backend could not issue a guest token (Superset down or misconfigured). */
export const GuestTokenError: Story = {
  args: {
    fetchGuestToken: () => Promise.reject(new Error("Analytics are unavailable right now.")),
  },
  play: async ({ canvasElement }) => {
    const canvas = within(canvasElement);
    await expect(await canvas.findByText("Could not load Revenue overview")).toBeInTheDocument();
    await expect(canvas.getByRole("button", { name: "Try again" })).toBeInTheDocument();
  },
};

/** No embedded dashboard id or Superset domain yet. */
export const NotConfigured: Story = {
  args: { embeddedId: null, supersetDomain: null },
  play: async ({ canvasElement }) => {
    await expect(
      await within(canvasElement).findByText("Analytics are not configured")
    ).toBeInTheDocument();
  },
};
