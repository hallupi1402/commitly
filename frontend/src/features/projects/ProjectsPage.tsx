import { useEffect, useState, type FormEvent } from "react";
import { ApiError, api } from "../../shared/api";
import { getJournal, getProjects, resolveJournal, resolveProjects, saveJournal, saveProjects } from "../../shared/journalApi";
import type { JournalConflict, Project, ProjectConflict, SearchResult } from "../../shared/types";
import { EmptyState, LoadingMessage } from "../../shared/Feedback";
import { ConflictResolution } from "../capture/ConflictResolution";

export function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [etag, setEtag] = useState<string | null>(null);
  const [name, setName] = useState("");
  const [activities, setActivities] = useState<Record<string, any>>({});
  const [conflict, setConflict] = useState<ProjectConflict | null>(null);
  const [journalConflict, setJournalConflict] = useState<JournalConflict | null>(null);
  const [journalConflictProject, setJournalConflictProject] = useState<Project | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => { void getProjects().then((value) => { setProjects(value.data); setEtag(value.etag); }).catch((reason) => setError(reason.message)).finally(() => setLoading(false)); }, []);

  async function persist(next: Project[]) {
    if (!etag) throw new Error("Project registry revision is unavailable.");
    try { const response = await saveProjects(next, etag); setProjects(response.data); setEtag(response.etag); setError(""); }
    catch (reason) {
      if (reason instanceof ApiError && reason.status === 409) {
        const id = reason.payload.conflict_id as string;
        const value = await api<ProjectConflict>(`/projects/conflicts/${id}`);
        setConflict(value.data);
      }
      throw reason;
    }
  }
  async function add(event: FormEvent) {
    event.preventDefault();
    if (!name.trim()) return;
    const now = new Date().toISOString();
    try { await persist([...projects, { id: crypto.randomUUID(), name: name.trim(), created_at: now, archived_at: null }]); setName(""); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Project could not be saved."); }
  }
  async function rename(project: Project) {
    const value = window.prompt("Project name", project.name);
    if (!value?.trim()) return;
    try { await persist(projects.map((item) => item.id === project.id ? { ...item, name: value.trim() } : item)); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Project could not be renamed."); }
  }
  async function archive(project: Project) {
    if (!window.confirm(`Archive ${project.name}? Its journal history will remain.`)) return;
    try { await persist(projects.map((item) => item.id === project.id ? { ...item, archived_at: new Date().toISOString() } : item)); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Project could not be archived."); }
  }
  async function showActivity(project: Project) {
    try { const result = await api<any>(`/projects/${project.id}/activity`); setActivities((old) => ({ ...old, [project.id]: result.data })); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Project activity could not be loaded."); }
  }
  async function resolveBlocker(item: SearchResult, project: Project) {
    try {
      const journal = await getJournal(item.date);
      const entries = journal.data.entries.map((entry) => entry.id === item.entry.id ? { ...entry, blocker_resolved_at: new Date().toISOString() } : entry);
      await saveJournal({ ...journal.data, entries }, journal.etag ?? "");
      await showActivity(project);
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 409) { setJournalConflict(reason.payload as JournalConflict); setJournalConflictProject(project); }
      setError(reason instanceof Error ? reason.message : "Blocker could not be resolved.");
    }
  }
  async function resolve(value: Project[]) {
    if (!conflict) return;
    try {
      const response = await resolveProjects(conflict, value); setProjects(response.data); setEtag(response.etag); setConflict(null); setError("");
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 409) {
        const refreshed = await api<ProjectConflict>(`/projects/conflicts/${reason.payload.conflict_id}`);
        setConflict(refreshed.data);
        setError("The registry changed again. Review the newer saved version before resolving.");
      } else setError(reason instanceof Error ? reason.message : "Project conflict could not be resolved.");
    }
  }

  return <main className="page-content"><header className="page-header"><div><span className="eyebrow">YOUR PROJECT THREADS</span><h1>Projects</h1><p className="date-line">Keep work grouped without turning your journal into a task board.</p></div></header>
    <form className="new-project-card" onSubmit={(event) => void add(event)}><label htmlFor="new-project">New project</label><div className="search-row"><input id="new-project" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Commitly" /><button className="primary-button">Create project</button></div></form>
    {error && <p className="form-error" role="alert">{error}</p>}{loading && <LoadingMessage>Loading projects…</LoadingMessage>}
    {!loading && projects.length === 0 && <EmptyState title="No projects yet">Entries can stay unassigned, or create a project to collect related work.</EmptyState>}
    <div className="project-list">{projects.map((project) => <article className={`project-card ${project.archived_at ? "archived" : ""}`} key={project.id}><div className="project-card-head"><span className="project-mark">{project.name.slice(0, 1).toUpperCase()}</span><div className="project-title"><h2>{project.name}{project.archived_at && <span className="archived-label">Archived</span>}</h2><p>{project.archived_at ? `Archived ${new Date(project.archived_at).toLocaleDateString()}` : "Active project"}</p></div><div className="button-row"><button className="quiet-button" onClick={() => void showActivity(project)}>Activity</button>{!project.archived_at && <><button className="quiet-button" onClick={() => void rename(project)}>Rename</button><button className="quiet-button" onClick={() => void archive(project)}>Archive</button></>}</div></div>
      {activities[project.id] && <div className="project-activity"><div className="activity-columns"><div><h3>Latest next steps</h3>{activities[project.id].latest_next_steps.length ? activities[project.id].latest_next_steps.map((item: SearchResult) => <p key={item.entry.id}><span>{item.date}</span> {item.entry.next_step}</p>) : <p className="muted">No next steps yet.</p>}</div><div><h3>Unresolved blockers</h3>{activities[project.id].unresolved_blockers.length ? activities[project.id].unresolved_blockers.map((item: SearchResult) => <p key={item.entry.id}><span>{item.date}</span> {item.entry.blocker || item.entry.description} <button className="quiet-button" onClick={() => void resolveBlocker(item, project)}>Mark resolved</button></p>) : <p className="muted">No unresolved blockers.</p>}</div></div><h3>Project history · {activities[project.id].entries.length}</h3>{activities[project.id].entries.map((item: SearchResult) => <p key={item.entry.id} className="project-history-item"><time>{item.date}</time><span className={`type-pill ${item.entry.type}`}>{item.entry.type}</span>{item.entry.description}</p>)}</div>}
    </article>)}</div>
    {conflict && <div className="modal-scrim"><section className="conflict-card" role="dialog" aria-modal="true" aria-labelledby="project-conflict-title"><span className="eyebrow">EXTERNAL CHANGE</span><h2 id="project-conflict-title">The project registry changed outside Commitly</h2><div className="conflict-columns"><article><h3>Your edits</h3><pre>{conflict.local.map((item) => item.name).join("\n")}</pre></article><article><h3>Saved registry</h3><pre>{conflict.external.map((item) => item.name).join("\n")}</pre></article></div><p>Combine keeps both project records by stable ID and lets the saved record win if an ID conflicts.</p><div className="button-row"><button className="quiet-button" onClick={() => setConflict(null)}>Decide later</button><button className="secondary-button" onClick={() => void resolve(conflict.external)}>Keep saved</button><button className="secondary-button" onClick={() => void resolve(conflict.local)}>Keep my edits</button><button className="primary-button" onClick={() => { const ids = new Set(conflict.external.map((p) => p.id)); void resolve([...conflict.external, ...conflict.local.filter((p) => !ids.has(p.id))]); }}>Combine and save</button></div></section></div>}
    {journalConflict && <div className="modal-scrim"><ConflictResolution conflict={journalConflict} onClose={() => setJournalConflict(null)} onResolve={async (value) => { try { await resolveJournal(journalConflict.date, journalConflict, value); setJournalConflict(null); if (journalConflictProject) await showActivity(journalConflictProject); } catch (reason) { if (reason instanceof ApiError && reason.status === 409) setJournalConflict(reason.payload as JournalConflict); throw reason; } }} /></div>}
  </main>;
}
