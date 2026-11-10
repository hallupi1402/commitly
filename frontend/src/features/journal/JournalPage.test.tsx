import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { JournalPage } from "./JournalPage";

const mock = vi.hoisted(() => ({ getReport: vi.fn(), getReportDates: vi.fn() }));
vi.mock("../../shared/reportApi", () => mock);

describe("JournalPage", () => {
  beforeEach(() => {
    mock.getReportDates.mockResolvedValue(["2026-11-09"]);
    mock.getReport.mockResolvedValue({ data: { date: "2026-11-09", summary: { id: "s", text: "Fixed the save flow", evidence_ids: ["e"], certainty: "supported" }, highlights: [], details: [], evidence: [{ id: "e", repository_id: "r", repository_name: "demo", repository_path: "/src/demo", commit_id: "a".repeat(40), authored_at: "2026-11-09T10:00:00Z", subject: "Fix save", changed_paths: ["src/save.py"], added_lines: 1, deleted_lines: 0, analysis_status: "complete", analysis_note: null }], user_context: [], analysis_status: "complete" }, etag: '"r"' });
  });
  it("opens a previous daily report and displays its source evidence", async () => {
    const user = userEvent.setup();
    render(<JournalPage />);
    await user.click(await screen.findByRole("button", { name: "2026-11-09" }));
    expect(await screen.findByText("Fixed the save flow")).toBeInTheDocument();
    expect(screen.getByText("Fix save")).toBeInTheDocument();
    expect(screen.getByText("src/save.py")).toBeInTheDocument();
  });
});
