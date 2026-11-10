import { useEffect, useState, type FormEvent, type KeyboardEvent } from "react";
import type { Entry, EntryType, Project } from "../../shared/types";
import { ProjectSelect } from "./ProjectSelect";

type Props = {
  date: string;
  projects: Project[];
  initial?: Entry | null;
  onSave: (entry: Entry) => Promise<void>;
  onCancel?: () => void;
};

const blank = (date: string): Entry => ({
  id: crypto.randomUUID(), created_at: new Date().toISOString(), date, type: "work", description: "",
  project_id: null, tags: [], result: null, blocker: null, blocker_resolved_at: null,
  next_step: null, references: [], notes: null,
});

export function QuickCapture({ date, projects, initial, onSave, onCancel }: Props) {
  const [entry, setEntry] = useState<Entry>(() => initial ? { ...initial } : blank(date));
  const [details, setDetails] = useState(Boolean(initial && (initial.tags.length || initial.result || initial.blocker || initial.next_step || initial.references.length || initial.notes || initial.project_id)));
  const [tagInput, setTagInput] = useState(initial?.tags.join(", ") ?? "");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState("");
  const [error, setError] = useState("");

  useEffect(() => { setEntry(initial ? { ...initial } : blank(date)); setTagInput(initial?.tags.join(", ") ?? ""); setDetails(Boolean(initial)); setError(""); }, [date, initial]);
  const change = <K extends keyof Entry>(key: K, value: Entry[K]) => { setSaved(""); setEntry((valueBefore) => ({ ...valueBefore, [key]: value })); };

  async function submit(event?: FormEvent) {
    event?.preventDefault();
    if (!entry.description.trim()) { setError("Add a short description of work completed."); return; }
    setSaving(true); setError("");
    try {
      await onSave({ ...entry, description: entry.description.trim(), tags: entry.tags.map((tag) => tag.trim()).filter(Boolean), references: entry.references.map((ref) => ref.trim()).filter(Boolean) });
      setSaved(initial ? "Entry updated" : "Entry saved");
      if (!initial) setEntry(blank(date));
    } catch (reason) { setError(reason instanceof Error ? reason.message : "The entry could not be saved."); }
    finally { setSaving(false); }
  }

  function keyboardSave(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) { event.preventDefault(); void submit(); }
  }

  return <form className="capture-card" onSubmit={(event) => void submit(event)} aria-label={initial ? "Edit journal entry" : "Quick Capture"}>
    <div className="capture-heading"><div><span className="eyebrow">QUICK CAPTURE</span><h2>{initial ? "Edit entry" : "What did you get done?"}</h2></div><span className="capture-hint">⌘ / Ctrl + Enter</span></div>
    <label className="sr-only" htmlFor="entry-description">Work description</label>
    <textarea id="entry-description" autoFocus={!initial} rows={2} placeholder="A short note is enough — capture the outcome, not the plan…" value={entry.description} onChange={(e) => change("description", e.target.value)} onKeyDown={keyboardSave} />
    {details && <div className="capture-fields">
      <label>Type<select value={entry.type} onChange={(e) => change("type", e.target.value as EntryType)}><option value="work">Work</option><option value="note">Note</option><option value="blocker">Blocker</option></select></label>
      <ProjectSelect projects={projects} value={entry.project_id} onChange={(value) => change("project_id", value)} />
      <label>Tags<input value={tagInput} onChange={(e) => setTagInput(e.target.value)} onBlur={() => setEntry((old) => ({ ...old, tags: tagInput.split(",").map((v) => v.trim()).filter(Boolean) }))} placeholder="api, docs" /></label>
      <label>Result<input value={entry.result ?? ""} onChange={(e) => change("result", e.target.value || null)} placeholder="What changed?" /></label>
      <label>Blocker<input value={entry.blocker ?? ""} onChange={(e) => change("blocker", e.target.value || null)} placeholder="What's blocked?" /></label>
      <label>Next step<input value={entry.next_step ?? ""} onChange={(e) => change("next_step", e.target.value || null)} placeholder="Where to continue" /></label>
      <label>References<input value={entry.references.join(", ")} onChange={(e) => setEntry((old) => ({ ...old, references: e.target.value.split(",").map((v) => v.trim()).filter(Boolean) }))} placeholder="Issue, URL, or PR" /></label>
      <label className="wide">Detailed notes<textarea rows={4} value={entry.notes ?? ""} onChange={(e) => change("notes", e.target.value || null)} placeholder="Optional Markdown notes" /></label>
    </div>}
    {error && <p className="form-error" role="alert">{error}</p>}
    <div className="capture-actions"><button type="button" className="quiet-button" onClick={() => setDetails((v) => !v)}>{details ? "Hide details" : "＋ Add details"}</button><div className="button-row">{onCancel && <button type="button" className="quiet-button" onClick={onCancel}>Cancel</button>}<button className="primary-button" disabled={saving}>{saving ? "Saving…" : initial ? "Save changes" : "Save entry"}<span aria-hidden="true"> ↗</span></button></div></div>
    <p className="sr-only" role="status" aria-live="polite">{saving ? "Saving entry" : saved}</p>
  </form>;
}
