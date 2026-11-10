import { useEffect, useState } from "react";
import { ApiError } from "../../shared/api";
import { getJournal, getProjects, resolveJournal, saveJournal } from "../../shared/journalApi";
import type { Entry, Journal, JournalConflict, Project, SearchResult } from "../../shared/types";
import { ConflictResolution } from "../capture/ConflictResolution";
import { QuickCapture } from "../capture/QuickCapture";
import { EntryTimeline } from "../today/EntryTimeline";
import { DailyReflection } from "../today/DailyReflection";
import { JournalSearch } from "./JournalSearch";
import { EmptyState } from "../../shared/Feedback";

export function JournalPage({ projects: initialProjects }: { projects: Project[] }) {
  const [projects, setProjects] = useState(initialProjects);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searched, setSearched] = useState(false);
  const [openedDate, setOpenedDate] = useState("");
  const [journal, setJournal] = useState<Journal | null>(null);
  const [etag, setEtag] = useState<string | null>(null);
  const [editing, setEditing] = useState<Entry | null>(null);
  const [conflict, setConflict] = useState<JournalConflict | null>(null);
  const [error, setError] = useState("");

  function localDate() {
    const now = new Date();
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
  }

  useEffect(() => { void getProjects().then((value) => setProjects(value.data)).catch((reason) => setError(reason.message)); }, []);

  async function openDate(value: string) {
    setError("");
    try { const response = await getJournal(value); setOpenedDate(value); setJournal(response.data); setEtag(response.etag); setEditing(null); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Journal could not be opened."); }
  }
  async function commit(next: Journal) {
    if (!etag) throw new Error("Journal revision is unavailable.");
    try { const value = await saveJournal(next, etag); setJournal(value.data); setEtag(value.etag); setEditing(null); }
    catch (reason) { if (reason instanceof ApiError && reason.status === 409) setConflict(reason.payload as JournalConflict); throw reason; }
  }
  async function saveEntry(entry: Entry) {
    if (!journal) return;
    const entries = journal.entries.some((value) => value.id === entry.id) ? journal.entries.map((value) => value.id === entry.id ? entry : value) : [...journal.entries, entry];
    await commit({ ...journal, entries });
  }
  async function removeEntry(entry: Entry) {
    if (!journal || !window.confirm("Delete this journal entry? This cannot be undone.")) return;
    await commit({ ...journal, entries: journal.entries.filter((item) => item.id !== entry.id) });
  }
  async function saveReflection(value: Journal["reflection"]) {
    if (!journal) return;
    await commit({ ...journal, reflection: value });
  }
  return <main className="page-content"><header className="page-header"><div><span className="eyebrow">LOOK BACK, FIND THE THREAD</span><h1>Journal</h1><p className="date-line">Browse days or search across your work.</p></div></header>
    <JournalSearch projects={projects} onResults={setResults} onSearched={setSearched} />
    {searched && results.length === 0 && <EmptyState title="No matches found">Try another phrase or clear one of the filters.</EmptyState>}
    {results.length > 0 ? <section className="results-section"><div className="section-heading"><h2>Matches <span className="muted">{results.length}</span></h2></div>{results.map(({ date, entry }) => <button className="result-row" key={entry.id} onClick={() => void openDate(date)}><time>{date}</time><span className={`type-pill ${entry.type}`}>{entry.type}</span><span>{entry.description}</span><span aria-hidden="true">↗</span></button>)}</section> : null}
    <section className="browse-card"><div className="section-heading"><div><span className="eyebrow">DAILY FILES</span><h2>Open a day</h2></div></div><div className="date-picker-row"><label htmlFor="journal-date">Journal date</label><input id="journal-date" type="date" value={openedDate} onChange={(e) => void openDate(e.target.value)} /><button className="secondary-button" onClick={() => void openDate(localDate())}>Open today</button></div></section>
    {error && <p className="form-error" role="alert">{error}</p>}
    {journal && <section className="history-day"><div className="section-heading"><div><span className="eyebrow">DAILY JOURNAL</span><h2>{new Intl.DateTimeFormat(undefined, { dateStyle: "full" }).format(new Date(`${journal.date}T12:00:00`))}</h2></div></div><QuickCapture date={journal.date} projects={projects} initial={editing} onCancel={editing ? () => setEditing(null) : undefined} onSave={saveEntry} /><EntryTimeline entries={journal.entries} projects={projects} onEdit={setEditing} onDelete={(entry) => void removeEntry(entry)} /><DailyReflection value={journal.reflection} onSave={saveReflection} /></section>}
    {conflict && <div className="modal-scrim"><ConflictResolution conflict={conflict} onClose={() => setConflict(null)} onResolve={async (value) => { try { const result = await resolveJournal(openedDate, conflict, value); setJournal(result.data); setEtag(result.etag); setConflict(null); } catch (reason) { if (reason instanceof ApiError && reason.status === 409) setConflict(reason.payload as JournalConflict); throw reason; } }} /></div>}
  </main>;
}
