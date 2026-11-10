import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { JournalPage } from "./JournalPage";

const mock = vi.hoisted(() => ({ getJournal: vi.fn(), getProjects: vi.fn(), resolveJournal: vi.fn(), saveJournal: vi.fn(), searchEntries: vi.fn() }));
vi.mock("../../shared/journalApi", () => mock);

describe("JournalPage", () => {
  beforeEach(() => {
    mock.getProjects.mockResolvedValue({ data: [], etag: '"p"' });
    mock.getJournal.mockResolvedValue({ data: { date: "2026-11-09", entries: [], reflection: null }, etag: '"j"' });
    mock.searchEntries.mockResolvedValue([]);
    mock.saveJournal.mockImplementation(async (value) => ({ data: value, etag: '"j2"' }));
  });
  it("opens a prior date and gives an explicit no-match state", async () => {
    const user = userEvent.setup();
    render(<JournalPage projects={[]} />);
    fireEvent.change(screen.getByLabelText("Journal date"), { target: { value: "2026-11-09" } });
    expect(await screen.findByText(/November 9, 2026/)).toBeInTheDocument();
    await user.type(screen.getByLabelText("Search journal entries"), "missing");
    await user.click(screen.getByRole("button", { name: "Search" }));
    expect(await screen.findByText("No matches found")).toBeInTheDocument();
  });

  it("edits and saves an optional reflection on a prior day", async () => {
    const user = userEvent.setup();
    render(<JournalPage projects={[]} />);
    fireEvent.change(screen.getByLabelText("Journal date"), { target: { value: "2026-11-09" } });
    await user.type(await screen.findByLabelText("Accomplishments"), "Closed the issue");
    await user.click(screen.getByRole("button", { name: "Save reflection" }));
    expect(mock.saveJournal).toHaveBeenCalledWith(expect.objectContaining({ reflection: { accomplishments: "Closed the issue", blockers: null, next_steps: null } }), '"j"');
  });
});
