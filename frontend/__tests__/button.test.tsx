import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { Button } from "@/components/ui/button";

describe("Button", () => {
  it("renders its children", () => {
    render(<Button type="button">Click me</Button>);
    expect(screen.getByRole("button", { name: "Click me" })).toBeTruthy();
  });

  it("respects the disabled prop", () => {
    render(
      <Button type="button" disabled>
        Nope
      </Button>
    );
    expect((screen.getByRole("button", { name: "Nope" }) as HTMLButtonElement).disabled).toBe(true);
  });
});
