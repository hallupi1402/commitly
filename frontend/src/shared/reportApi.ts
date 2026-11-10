import { api, jsonBody } from "./api";

export interface Claim { id: string; text: string; evidence_ids: string[]; certainty: "supported" | "uncertain" }
export interface Evidence { id: string; repository_id: string; repository_name: string; repository_path: string; commit_id: string; authored_at: string; subject: string; changed_paths: string[]; added_lines: number | null; deleted_lines: number | null; analysis_status: string; analysis_note: string | null }
export interface DailyReport { date: string; summary: Claim; highlights: Claim[]; details: Claim[]; evidence: Evidence[]; user_context: { id: string; created_at: string; text: string }[]; analysis_status: "complete" | "partial" | "unavailable" }
export interface Repository { id: string; path: string; display_name: string; remote_name: string; author_email: string; last_fetch_at: string | null; last_fetch_status: "success" | "failed" | "never"; last_error: string | null }
export interface RefreshResponse { from: string; to: string; repositories: { repository_id: string; fetch_status: "success" | "failed" | "cached"; last_verified_at: string | null; analysis_status: string; report_dates: string[]; error: string | null }[] }
export interface ReportConflict { conflict_id: string; date: string; external_markdown: string; external_report: DailyReport; generated_report: DailyReport; external_revision: string }

export const getReport = (date: string) => api<DailyReport>(`/reports/${date}`);
export const getReportDates = () => api<string[]>("/reports").then((result) => result.data);
export const refreshActivity = (date: string) => api<RefreshResponse>("/activity/refresh", { method: "POST", body: jsonBody({ from: date, to: date }) }).then((result) => result.data);
export const getRepositories = () => api<Repository[]>("/repositories").then((result) => result.data);
export const addRepository = (path: string, remote_name?: string) => api<Repository>("/repositories", { method: "POST", body: jsonBody({ path, remote_name: remote_name || null }) }).then((result) => result.data);
export const removeRepository = (id: string) => api<null>(`/repositories/${id}`, { method: "DELETE" });
export const saveReportContext = (date: string, text: string | null, etag: string) => api<DailyReport>(`/reports/${date}/context`, { method: "PUT", headers: { "If-Match": etag }, body: jsonBody({ text }) });
export const getReportConflict = (date: string, id: string) => api<ReportConflict>(`/reports/${date}/conflicts/${id}`).then((result) => result.data);
export const resolveReportConflict = (date: string, id: string, value: DailyReport | { date: string; keep_external: true }, etag: string) => api<DailyReport>(`/reports/${date}/conflicts/${id}/resolve`, { method: "POST", headers: { "If-Match": etag }, body: jsonBody(value) });
