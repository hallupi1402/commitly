import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { TodayPage } from "./TodayPage";
import { EntryTimeline } from "./EntryTimeline";

const mock = vi.hoisted(() => ({ getToday: vi.fn(), getJournal: vi.fn(), getProjects: vi.fn(), saveJournal: vi.fn(), resolveJournal: vi.fn() }));
vi.mock("../../shared/journalApi", () => mock);

describe("TodayPage", () => {
  beforeEach(() => {
    mock.getToday.mockResolvedValue({ date: "2026-11-10", journal: { date: "2026-11-10", entries: [], reflection: null }, previous_context: [{ source_date: "2026-11-09", next_steps: [], blockers: [] }] });
    mock.getJournal.mockResolvedValue({ data: { date: "2026-11-10", entries: [], reflection: null }, etag: '"rev"' });
    mock.getProjects.mockResolvedValue({ data: [], etag: '"projects"' });
  });
  it("shows the current journal, prior context, and an optional reflection", async () => {
    render(<TodayPage />);
    expect(await screen.findByText("Work timeline")).toBeInTheDocument();
    expect(screen.getByText("From previous days")).toBeInTheDocument();
    expect(screen.getByText("End-of-day reflection")).toBeInTheDocument();
    expect(screen.getByText("No entries yet")).toBeInTheDocument();
  });

  it("renders user Markdown without interpreting raw HTML", () => {
    render(<EntryTimeline entries={[{ id: "1", created_at: "2026-11-10T02:00:00Z", date: "2026-11-10", type: "work", description: '<img src=x onerror="alert(1)">', project_id: null, tags: [], result: null, blocker: null, blocker_resolved_at: null, next_step: null, references: [], notes: null }]} onEdit={vi.fn()} onDelete={vi.fn()} />);
    expect(document.querySelector("img")).toBeNull();
  });
});
