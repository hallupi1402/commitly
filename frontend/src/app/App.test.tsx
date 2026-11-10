import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { App } from "./App";

const mock = vi.hoisted(() => ({ getSettings: vi.fn(), getProjects: vi.fn(), updateSettings: vi.fn(), getToday: vi.fn(), getJournal: vi.fn(), saveJournal: vi.fn(), resolveJournal: vi.fn(), getBackupStatus: vi.fn(), updateBackup: vi.fn() }));
vi.mock("../shared/journalApi", () => mock);

describe("application shell", () => {
  it("provides named navigation controls and applies the saved dark theme", async () => {
    mock.getSettings.mockResolvedValue({ workspace_path: "/tmp/journal", theme: "dark" });
    mock.getProjects.mockResolvedValue({ data: [], etag: '"projects"' });
    mock.getBackupStatus.mockResolvedValue({ enabled: false, configured: false, destination_label: null, private_confirmed: false, branch: "main", last_attempt_at: null, last_success_at: null, pending_commits: 0, last_error: null });
    mock.getToday.mockResolvedValue({ date: "2026-11-10", journal: { date: "2026-11-10", entries: [], reflection: null }, previous_context: [] });
    mock.getJournal.mockResolvedValue({ data: { date: "2026-11-10", entries: [], reflection: null }, etag: '"journal"' });
    const user = userEvent.setup();
    render(<App />);
    expect(await screen.findByRole("navigation", { name: "Main navigation" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Today/ })).toHaveAttribute("aria-current", "page");
    await user.click(screen.getByRole("button", { name: /Settings/ }));
    expect(await screen.findByRole("heading", { name: "Settings" })).toBeInTheDocument();
    expect(document.documentElement.dataset.theme).toBe("dark");
  });
});
