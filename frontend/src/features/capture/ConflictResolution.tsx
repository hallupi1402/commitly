import { useState } from "react";
import type { Journal, JournalConflict } from "../../shared/types";

export function ConflictResolution({ conflict, onResolve, onClose }: { conflict: JournalConflict; onResolve: (value: Journal) => Promise<void>; onClose: () => void }) {
  const [choice, setChoice] = useState<"local" | "external" | "combine">("combine");
  const [error, setError] = useState("");
  async function save() {
    const localById = new Map(conflict.local.entries.map((entry) => [entry.id, entry]));
    const externalIds = new Set(conflict.external.entries.map((entry) => entry.id));
    const combined: Journal = {
      date: conflict.date,
      entries: [
        ...conflict.external.entries.map((entry) => { const local = localById.get(entry.id); return local ? { ...entry, ...local } : entry; }),
        ...conflict.local.entries.filter((entry) => !externalIds.has(entry.id)),
      ],
      reflection: conflict.local.reflection ?? conflict.external.reflection,
    };
    try { await onResolve(choice === "local" ? conflict.local : choice === "external" ? conflict.external : combined); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Resolution was not saved. Both versions remain available."); }
  }
  return <section className="conflict-card" role="alertdialog" aria-labelledby="conflict-title" aria-modal="true">
    <div><span className="eyebrow">EXTERNAL CHANGE</span><h2 id="conflict-title">This journal changed outside Commitly</h2><p>Nothing has been overwritten. Compare both versions and explicitly save a resolution.</p></div>
    <div className="conflict-columns"><article><h3>Your draft · {conflict.local.entries.length} entries</h3><pre>{JSON.stringify(conflict.local, null, 2)}</pre></article><article><h3>Saved file · {conflict.external.entries.length} entries</h3><pre>{JSON.stringify(conflict.external, null, 2)}</pre></article></div>
    <fieldset><legend>Resolution</legend>{(["combine", "local", "external"] as const).map((value) => <label className="radio-choice" key={value}><input type="radio" name="resolution" value={value} checked={choice === value} onChange={() => setChoice(value)} />{value === "combine" ? "Combine entries (your fields win when an ID appears in both)" : value === "local" ? "Keep my draft" : "Keep the saved version"}</label>)}</fieldset>
    {error && <p role="alert" className="form-error">{error}</p>}
    <div className="button-row"><button className="quiet-button" onClick={onClose}>Decide later</button><button className="primary-button" onClick={() => void save()}>Save resolution</button></div>
  </section>;
}
