import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { QuickCapture } from "./QuickCapture";

describe("QuickCapture", () => {
  it("saves a one-line Work entry with Ctrl+Enter", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn().mockResolvedValue(undefined);
    render(<QuickCapture date="2026-11-10" projects={[]} onSave={onSave} />);
    await user.type(screen.getByLabelText("Work description"), "  Fixed startup  ");
    await user.keyboard("{Control>}{Enter}{/Control}");
    expect(onSave).toHaveBeenCalledWith(expect.objectContaining({ description: "Fixed startup", type: "work", date: "2026-11-10" }));
  });

  it("requires a non-whitespace description and keeps details optional", async () => {
    const user = userEvent.setup();
    const onSave = vi.fn();
    render(<QuickCapture date="2026-11-10" projects={[]} onSave={onSave} />);
    await user.click(screen.getByRole("button", { name: /Save entry/ }));
    expect(screen.getByRole("alert")).toHaveTextContent("Add a short description");
    expect(onSave).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: /Add details/ }));
    expect(screen.getByLabelText("Type")).toHaveValue("work");
  });
});
