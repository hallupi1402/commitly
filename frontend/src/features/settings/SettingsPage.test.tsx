import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { SettingsPage } from "./SettingsPage";

const mock = vi.hoisted(() => ({ getSettings: vi.fn(), getBackupStatus: vi.fn(), updateBackup: vi.fn() }));
vi.mock("../../shared/journalApi", () => mock);

describe("SettingsPage", () => {
  it("shows the read-only workspace and exact privacy assertion", async () => {
    mock.getSettings.mockResolvedValue({ workspace_path: "/home/dev/.local/share/commitly/journal", theme: "system" });
    mock.getBackupStatus.mockResolvedValue({ enabled: false, configured: false, destination_label: null, private_confirmed: false, branch: "main", last_attempt_at: null, last_success_at: null, pending_commits: 0, last_error: null });
    const user = userEvent.setup();
    render(<SettingsPage theme="system" onThemeChange={vi.fn()} />);
    expect(await screen.findByText("/home/dev/.local/share/commitly/journal")).toBeInTheDocument();
    expect(screen.getByText("Read only")).toBeInTheDocument();
    expect(screen.getByText("I confirm that this Git destination is private and appropriate for storing my personal journal.")).toBeInTheDocument();
    await user.selectOptions(screen.getByLabelText("Color theme"), "dark");
  });
});
