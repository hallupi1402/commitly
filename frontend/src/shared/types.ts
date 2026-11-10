export type EntryType = "work" | "note" | "blocker";
export type Theme = "system" | "light" | "dark";

export interface Entry {
  id: string;
  created_at: string;
  date: string;
  type: EntryType;
  description: string;
  project_id: string | null;
  tags: string[];
  result: string | null;
  blocker: string | null;
  blocker_resolved_at: string | null;
  next_step: string | null;
  references: string[];
  notes: string | null;
}

export interface Reflection {
  accomplishments: string | null;
  blockers: string | null;
  next_steps: string | null;
}

export interface Journal {
  date: string;
  entries: Entry[];
  reflection: Reflection | null;
}

export interface Project {
  id: string;
  name: string;
  created_at: string;
  archived_at: string | null;
}

export interface SearchResult {
  date: string;
  entry: Entry;
}

export interface PriorContext {
  source_date: string;
  next_steps: Entry[];
  blockers: Entry[];
}

export interface TodayData {
  date: string;
  journal: Journal;
  previous_context: PriorContext[];
}

export interface JournalConflict {
  conflict_id: string;
  date: string;
  expected_revision: string;
  current_revision: string;
  local: Journal;
  external: Journal;
}

export interface ProjectConflict {
  conflict_id: string;
  expected_revision: string;
  current_revision: string;
  local: Project[];
  external: Project[];
}

export interface BackupStatus {
  enabled: boolean;
  configured: boolean;
  destination_label: string | null;
  private_confirmed: boolean;
  branch: string;
  last_attempt_at: string | null;
  last_success_at: string | null;
  pending_commits: number;
  last_error: string | null;
}

export interface Settings {
  workspace_path: string;
  theme: Theme;
  model_path: string | null;
  model_executable: string;
}
