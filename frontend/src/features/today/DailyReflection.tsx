import { useEffect, useState } from "react";
import type { Reflection } from "../../shared/types";

export function DailyReflection({ value, onSave }: { value: Reflection | null; onSave: (value: Reflection | null) => Promise<void> }) {
  const [draft, setDraft] = useState<Reflection>({ accomplishments: "", blockers: "", next_steps: "" });
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => setDraft({ accomplishments: value?.accomplishments ?? "", blockers: value?.blockers ?? "", next_steps: value?.next_steps ?? "" }), [value]);
  const set = (key: keyof Reflection, text: string) => { setSaved(false); setDraft((old) => ({ ...old, [key]: text })); };
  async function save() {
    setError("");
    const result = Object.fromEntries(Object.entries(draft).map(([key, text]) => [key, text.trim() || null])) as Reflection;
    try { await onSave(Object.values(result).some(Boolean) ? result : null); setSaved(true); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Reflection could not be saved."); }
  }
  return <section className="reflection-card"><div className="section-heading"><div><span className="eyebrow">CLOSE THE LOOP</span><h2>End-of-day reflection</h2></div><span className="optional-label">Optional</span></div><p className="muted">A few lines can make tomorrow easier to start.</p>
    <div className="reflection-fields"><label>Accomplishments<textarea rows={2} value={draft.accomplishments ?? ""} onChange={(e) => set("accomplishments", e.target.value)} placeholder="What moved forward?" /></label><label>Blockers<textarea rows={2} value={draft.blockers ?? ""} onChange={(e) => set("blockers", e.target.value)} placeholder="What needs attention?" /></label><label>Next steps<textarea rows={2} value={draft.next_steps ?? ""} onChange={(e) => set("next_steps", e.target.value)} placeholder="Where will you pick up?" /></label></div>
    {error && <p role="alert" className="form-error">{error}</p>}<div className="reflection-footer"><span role="status" aria-live="polite">{saved ? "Reflection saved" : ""}</span><button className="secondary-button" onClick={() => void save()}>Save reflection</button></div>
  </section>;
}
