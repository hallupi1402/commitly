import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { SettingsPage } from "./SettingsPage";

const mock = vi.hoisted(() => ({ getSettings: vi.fn(), updateSettings: vi.fn() }));
vi.mock("../../shared/journalApi", () => mock);

describe("SettingsPage", () => {
  it("shows the local workspace and saves analyzer configuration", async () => {
    mock.getSettings.mockResolvedValue({ workspace_path: "/home/dev/.local/share/commitly/journal", theme: "system", model_path: null, model_executable: "llama-cli" });
    mock.updateSettings.mockResolvedValue({ workspace_path: "/home/dev/.local/share/commitly/journal", theme: "system", model_path: "/models/model.gguf", model_executable: "llama-cli" });
    const user = userEvent.setup();
    render(<SettingsPage theme="system" onThemeChange={vi.fn()} />);
    expect(await screen.findByText("/home/dev/.local/share/commitly/journal")).toBeInTheDocument();
    expect(screen.getByText("Read only")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Model file path"), { target: { value: "/models/model.gguf" } });
    await user.click(screen.getByRole("button", { name: "Save analyzer settings" }));
    expect(mock.updateSettings).toHaveBeenCalledWith({ model_path: "/models/model.gguf", model_executable: "llama-cli" });
    expect(await screen.findByText("Local analyzer settings saved.")).toBeInTheDocument();
  });

  it("does not report a failed theme preference as saved", async () => {
    mock.getSettings.mockResolvedValue({ workspace_path: "/private/journal", theme: "system", model_path: null, model_executable: "llama-cli" });
    const user = userEvent.setup();
    render(<SettingsPage theme="system" onThemeChange={vi.fn().mockRejectedValue(new Error("Could not persist preference"))} />);
    await user.selectOptions(await screen.findByLabelText("Color theme"), "dark");
    expect(await screen.findByRole("alert")).toHaveTextContent("Could not persist preference");
    expect(screen.queryByText("Preference saved.")).not.toBeInTheDocument();
  });
});
