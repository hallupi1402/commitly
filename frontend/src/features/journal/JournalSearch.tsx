import { useState, type FormEvent } from "react";
import type { Project, SearchResult } from "../../shared/types";
import { searchEntries } from "../../shared/journalApi";

export function JournalSearch({ projects, onResults, onSearched }: { projects: Project[]; onResults: (results: SearchResult[]) => void; onSearched: (searched: boolean) => void }) {
  const [query, setQuery] = useState("");
  const [project, setProject] = useState("");
  const [type, setType] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");
  const [error, setError] = useState("");
  const [searching, setSearching] = useState(false);
  async function search(event: FormEvent) {
    event.preventDefault(); setSearching(true); setError(""); onSearched(true);
    const params = new URLSearchParams();
    if (query.trim()) params.set("q", query.trim());
    if (project) params.set("project_id", project);
    if (type) params.set("type", type);
    if (from) params.set("from", from);
    if (to) params.set("to", to);
    try { onResults(await searchEntries(params)); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Search failed."); }
    finally { setSearching(false); }
  }
  return <form className="filter-card" onSubmit={(event) => void search(event)}>
    <div className="search-row"><label className="search-box"><span aria-hidden="true">⌕</span><input aria-label="Search journal entries" value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search your journal…" /></label><button className="primary-button" disabled={searching}>{searching ? "Searching…" : "Search"}</button></div>
    <div className="filter-row"><label>Project<select value={project} onChange={(e) => setProject(e.target.value)}><option value="">All projects</option>{projects.map((item) => <option key={item.id} value={item.id}>{item.name}{item.archived_at ? " (archived)" : ""}</option>)}</select></label><label>Type<select value={type} onChange={(e) => setType(e.target.value)}><option value="">All types</option><option value="work">Work</option><option value="note">Note</option><option value="blocker">Blocker</option></select></label><label>From<input type="date" value={from} onChange={(e) => setFrom(e.target.value)} /></label><label>To<input type="date" value={to} onChange={(e) => setTo(e.target.value)} /></label><button className="quiet-button" type="button" onClick={() => { setQuery(""); setProject(""); setType(""); setFrom(""); setTo(""); onResults([]); onSearched(false); }}>Clear</button></div>
    {error && <p className="form-error" role="alert">{error}</p>}
  </form>;
}
