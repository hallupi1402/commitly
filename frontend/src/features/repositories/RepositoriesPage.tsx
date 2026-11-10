import { useEffect, useState } from "react";
import { addRepository, getRepositories, removeRepository, type Repository } from "../../shared/reportApi";
import { ErrorNotice, LoadingMessage } from "../../shared/Feedback";

export function RepositoriesPage() {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [path, setPath] = useState("");
  const [remote, setRemote] = useState("origin");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  async function load() {
    setLoading(true);
    try { setRepositories(await getRepositories()); setError(""); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Selected repositories could not be loaded."); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, []);
  async function add(event: React.FormEvent) {
    event.preventDefault();
    try { await addRepository(path, remote || undefined); setPath(""); await load(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Repository could not be selected."); }
  }
  async function remove(repository: Repository) {
    try { await removeRepository(repository.id); await load(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Repository could not be removed."); }
  }
  return <main className="page-content"><header className="page-header"><div><span className="eyebrow">LOCAL SOURCES ONLY</span><h1>Repositories</h1><p className="date-line">Commitly reads only repositories you select.</p></div></header>
    {error && <ErrorNotice title="Repository action failed" message={error} onRetry={() => void load()} />}
    <form className="browse-card" onSubmit={(event) => void add(event)}><label htmlFor="repo-path">Repository folder path</label><input id="repo-path" required value={path} onChange={(event) => setPath(event.target.value)} placeholder="/home/you/src/project" /><label htmlFor="repo-remote">Remote name</label><input id="repo-remote" value={remote} onChange={(event) => setRemote(event.target.value)} /><button className="primary-button" type="submit">Select repository</button></form>
    {loading ? <LoadingMessage>Loading selected repositories…</LoadingMessage> : repositories.length === 0 ? <p className="muted">No repositories selected.</p> : repositories.map((repository) => <article className="browse-card" key={repository.id}><div className="section-heading"><div><h2>{repository.display_name}</h2><p>{repository.path}</p></div><button className="secondary-button" onClick={() => void remove(repository)}>Remove</button></div><p>Remote: <code>{repository.remote_name}</code> · Author: <code>{repository.author_email}</code></p><p className="muted">Last refresh: {repository.last_fetch_at ? new Date(repository.last_fetch_at).toLocaleString() : "Never"} · {repository.last_error ?? repository.last_fetch_status}</p></article>)}
  </main>;
}
