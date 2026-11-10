import ReactMarkdown from "react-markdown";
import type { Entry, Project } from "../../shared/types";
import { EmptyState } from "../../shared/Feedback";

function time(value: string) {
  return new Intl.DateTimeFormat(undefined, { hour: "numeric", minute: "2-digit" }).format(new Date(value));
}

export function EntryTimeline({ entries, projects = [], onEdit, onDelete }: { entries: Entry[]; projects?: Project[]; onEdit: (entry: Entry) => void; onDelete: (entry: Entry) => void }) {
  if (!entries.length) return <EmptyState title="No entries yet">Capture a small win or useful detail. One line is plenty.</EmptyState>;
  return <ol className="timeline">{entries.map((entry) => <li className="timeline-item" key={entry.id}>
    <time dateTime={entry.created_at}>{time(entry.created_at)}</time><span className={`timeline-dot ${entry.type}`} aria-hidden="true" />
    <article className="entry-card"><div className="entry-topline"><span className={`type-pill ${entry.type}`}>{entry.type}</span>{entry.tags.map((tag) => <span className="tag-pill" key={tag}>{tag}</span>)}<div className="entry-actions"><button className="icon-button" aria-label={`Edit ${entry.description}`} onClick={() => onEdit(entry)}>Edit</button><button className="icon-button danger" aria-label={`Delete ${entry.description}`} onClick={() => onDelete(entry)}>Delete</button></div></div>
      <div className="markdown-body"><ReactMarkdown>{entry.description}</ReactMarkdown></div>
      {entry.result && <p className="entry-detail"><strong>Result</strong> {entry.result}</p>}{entry.blocker && <p className="entry-detail blocker-line"><strong>Blocker</strong> {entry.blocker}{entry.blocker_resolved_at && <span> · Resolved</span>}</p>}{entry.next_step && <p className="entry-detail"><strong>Next</strong> {entry.next_step}</p>}{entry.project_id && <p className="entry-project">{projects.find((project) => project.id === entry.project_id)?.name ?? "Archived project"}{projects.find((project) => project.id === entry.project_id)?.archived_at ? " · Archived" : ""}</p>}
      {entry.notes && <details className="entry-notes"><summary>Technical notes</summary><div className="markdown-body"><ReactMarkdown>{entry.notes}</ReactMarkdown></div></details>}
    </article>
  </li>)}</ol>;
}
