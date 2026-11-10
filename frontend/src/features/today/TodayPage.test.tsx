import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { TodayPage } from "./TodayPage";
import { ApiError } from "../../shared/api";

const mock = vi.hoisted(() => ({ getReport: vi.fn(), refreshActivity: vi.fn(), saveReportContext: vi.fn() }));
vi.mock("../../shared/reportApi", () => mock);

const today = new Date();
const date = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`;
const report = { date, summary: { id: "s", text: "Implemented pushed activity report", evidence_ids: ["e"], certainty: "supported" as const }, highlights: [{ id: "h", text: "Added repository evidence", evidence_ids: ["e"], certainty: "supported" as const }], details: [], evidence: [{ id: "e", repository_id: "r", repository_name: "demo", repository_path: "/src/demo", commit_id: "a".repeat(40), authored_at: `${date}T10:00:00Z`, subject: "Add report", changed_paths: ["src/report.py"], added_lines: 12, deleted_lines: 0, analysis_status: "complete", analysis_note: null }], user_context: [], analysis_status: "complete" as const };

describe("TodayPage", () => {
  beforeEach(() => {
    mock.getReport.mockResolvedValue({ data: report, etag: '"r1"' });
    mock.refreshActivity.mockResolvedValue({ from: date, to: date, repositories: [] });
    mock.saveReportContext.mockResolvedValue({ data: { ...report, user_context: [{ id: "c", created_at: "2026-11-10T00:00:00Z", text: "Checked edge cases" }] }, etag: '"r2"' });
  });
  it("shows the report sections and source log", async () => {
    render(<TodayPage />);
    expect(await screen.findByText("Implemented pushed activity report")).toBeInTheDocument();
    expect(screen.getByText("Added repository evidence")).toBeInTheDocument();
    expect(screen.getByText("Add report")).toBeInTheDocument();
    expect(screen.getByText("src/report.py")).toBeInTheDocument();
  });
  it("refreshes pushed activity and saves optional context", async () => {
    const user = userEvent.setup();
    render(<TodayPage />);
    await user.click(await screen.findByRole("button", { name: "Refresh pushed activity" }));
    expect(mock.refreshActivity).toHaveBeenCalledWith(date);
    fireEvent.change(screen.getByLabelText("Optional one-line context"), { target: { value: "Checked edge cases" } });
    await user.click(screen.getByRole("button", { name: "Save context" }));
    expect(mock.saveReportContext).toHaveBeenCalledWith(date, "Checked edge cases", '"r1"');
  });
  it("allows user context on a day without Git activity", async () => {
    mock.getReport.mockRejectedValueOnce(new ApiError(404, { message: "No report" }));
    mock.saveReportContext.mockResolvedValueOnce({ data: { ...report, summary: { ...report.summary, text: "No Git activity" }, evidence: [], highlights: [], details: [], user_context: [{ id: "c", created_at: `${date}T10:00:00Z`, text: "Pairing session" }], analysis_status: "unavailable" }, etag: '"new"' });
    const user = userEvent.setup();
    render(<TodayPage />);
    await user.type(await screen.findByLabelText("Optional one-line context"), "Pairing session");
    await user.click(screen.getByRole("button", { name: "Save context" }));
    expect(mock.saveReportContext).toHaveBeenCalledWith(date, "Pairing session", '"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"');
  });
});
