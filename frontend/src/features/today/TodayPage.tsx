import { useCallback, useEffect, useState } from "react";
import { ApiError } from "../../shared/api";
import { getJournal, getProjects, getToday, resolveJournal, saveJournal } from "../../shared/journalApi";
import type { Entry, Journal, JournalConflict, Project, Reflection, TodayData } from "../../shared/types";
import { ConflictResolution } from "../capture/ConflictResolution";
import { QuickCapture } from "../capture/QuickCapture";
import { DailyReflection } from "./DailyReflection";
import { EntryTimeline } from "./EntryTimeline";
import { ErrorNotice, LoadingMessage } from "../../shared/Feedback";

function localDate() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
}

export function TodayPage() {
  const [today, setToday] = useState<TodayData | null>(null);
  const [journal, setJournal] = useState<Journal | null>(null);
  const [etag, setEtag] = useState<string | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [editing, setEditing] = useState<Entry | null>(null);
  const [conflict, setConflict] = useState<JournalConflict | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const [todayValue, journalValue, projectValue] = await Promise.all([getToday(), getJournal(localDate()), getProjects()]);
      setToday(todayValue); setJournal(journalValue.data); setEtag(journalValue.etag); setProjects(projectValue.data);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Commitly could not load today's journal."); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { void load(); }, [load]);

  async function commit(next: Journal) {
    if (!etag) throw new Error("Journal revision is unavailable. Reload before saving.");
    try {
      const result = await saveJournal(next, etag);
      setJournal(result.data); setEtag(result.etag); setToday((old) => old ? { ...old, journal: result.data } : old); setEditing(null);
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 409) setConflict(reason.payload as JournalConflict);
      throw reason;
    }
  }

  async function saveEntry(entry: Entry) {
    if (!journal) throw new Error("Journal is still loading.");
    const entries = journal.entries.some((item) => item.id === entry.id) ? journal.entries.map((item) => item.id === entry.id ? entry : item) : [...journal.entries, entry];
    await commit({ ...journal, entries });
  }

  async function removeEntry(entry: Entry) {
    if (!journal || !window.confirm("Delete this journal entry? This cannot be undone.")) return;
    await commit({ ...journal, entries: journal.entries.filter((item) => item.id !== entry.id) });
  }

  async function saveReflection(value: Reflection | null) {
    if (!journal) throw new Error("Journal is still loading.");
    await commit({ ...journal, reflection: value });
  }

  async function resolve(value: Journal) {
    if (!conflict) return;
    try {
      const result = await resolveJournal(conflict.date, conflict, value);
      setJournal(result.data); setEtag(result.etag); setToday((old) => old ? { ...old, journal: result.data } : old); setConflict(null); setEditing(null);
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 409) setConflict(reason.payload as JournalConflict);
      throw reason;
    }
  }

  const day = today ? new Date(`${today.date}T12:00:00`) : new Date();
  const formatted = new Intl.DateTimeFormat(undefined, { weekday: "long", month: "long", day: "numeric", year: "numeric" }).format(day);
  const count = journal?.entries.length ?? 0;
  return <main className="page-content">
    <header className="page-header"><div><span className="eyebrow">YOUR WORK JOURNAL</span><h1>Today</h1><p className="date-line">{formatted}</p></div><div className="day-count"><span>{String(count).padStart(2, "0")}</span><small>{count === 1 ? "entry" : "entries"}</small></div></header>
    {error && <ErrorNotice title="Couldn't load the journal." message={error} onRetry={() => void load()} />}
    {loading && <LoadingMessage>Opening your journal…</LoadingMessage>}
    {!loading && journal && <>
      <QuickCapture date={journal.date} projects={projects} initial={editing} onCancel={editing ? () => setEditing(null) : undefined} onSave={saveEntry} />
      {today?.previous_context.length ? <section className="context-section"><div className="section-heading"><div><span className="eyebrow">PICK UP THE THREAD</span><h2>From previous days</h2></div></div><div className="context-grid">{today.previous_context.map((context) => <article className="context-card" key={context.source_date}><time>{new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric" }).format(new Date(`${context.source_date}T12:00:00`))}</time>{context.next_steps.map((entry) => <p key={`next-${entry.id}`}><span className="context-mark next">↳</span>{entry.next_step}</p>)}{context.blockers.map((entry) => <p key={`block-${entry.id}`}><span className="context-mark block">!</span>{entry.blocker || entry.description}</p>)}</article>)}</div></section> : null}
      <section className="timeline-section"><div className="section-heading"><div><span className="eyebrow">THE DAY SO FAR</span><h2>Work timeline</h2></div><span className="muted">{count} captured</span></div><EntryTimeline entries={journal.entries} projects={projects} onEdit={(entry) => setEditing(entry)} onDelete={(entry) => void removeEntry(entry)} /></section>
      <DailyReflection value={journal.reflection} onSave={saveReflection} />
    </>}
    {conflict && <div className="modal-scrim"><ConflictResolution conflict={conflict} onResolve={resolve} onClose={() => setConflict(null)} /></div>}
  </main>;
}
