import { api, jsonBody } from "./api";
import type { BackupStatus, Journal, JournalConflict, Project, ProjectConflict, SearchResult, Settings, TodayData } from "./types";

export async function getToday() {
  return (await api<TodayData>("/today")).data;
}

export function getJournal(date: string) {
  return api<Journal>(`/journals/${date}`);
}

export function saveJournal(journal: Journal, etag: string) {
  return api<Journal>(`/journals/${journal.date}`, { method: "PUT", headers: { "If-Match": etag }, body: jsonBody(journal) });
}

export function getJournalConflict(date: string, id: string) {
  return api<JournalConflict>(`/journals/${date}/conflicts/${id}`).then((r) => r.data);
}

export function resolveJournal(date: string, conflict: JournalConflict, journal: Journal) {
  return api<Journal>(`/journals/${date}/conflicts/${conflict.conflict_id}/resolve`, {
    method: "POST", headers: { "If-Match": conflict.current_revision }, body: jsonBody(journal),
  });
}

export function getProjects() {
  return api<Project[]>("/projects");
}

export function saveProjects(projects: Project[], etag: string) {
  return api<Project[]>("/projects", { method: "PUT", headers: { "If-Match": etag }, body: jsonBody(projects) });
}

export function resolveProjects(conflict: ProjectConflict, projects: Project[]) {
  return api<Project[]>(`/projects/conflicts/${conflict.conflict_id}/resolve`, {
    method: "POST", headers: { "If-Match": conflict.current_revision }, body: jsonBody(projects),
  });
}

export function searchEntries(params: URLSearchParams) {
  return api<SearchResult[]>(`/entries/search?${params}`).then((r) => r.data);
}

export function getSettings() {
  return api<Settings>("/settings").then((r) => r.data);
}

export function updateSettings(value: Partial<Settings>) {
  return api<Settings>("/settings", { method: "PATCH", body: jsonBody(value) }).then((r) => r.data);
}

export function getBackupStatus() {
  return api<BackupStatus>("/backup/status").then((r) => r.data);
}

export function updateBackup(value: { enabled: boolean; remote_url: string | null; branch: string; private_confirmed: boolean }) {
  return api<BackupStatus>("/backup/configuration", { method: "PUT", body: jsonBody(value) }).then((r) => r.data);
}
