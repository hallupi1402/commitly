import { useEffect, useState, type FormEvent } from "react";
import { getSettings, updateSettings } from "../../shared/journalApi";
import type { Settings, Theme } from "../../shared/types";
import { ErrorNotice, SaveStatus } from "../../shared/Feedback";

export function SettingsPage({ theme, onThemeChange }: { theme: Theme; onThemeChange: (theme: Theme) => void }) {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [modelPath, setModelPath] = useState("");
  const [executable, setExecutable] = useState("llama-cli");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  useEffect(() => { void getSettings().then((value) => { setSettings(value); setModelPath(value.model_path ?? ""); setExecutable(value.model_executable || "llama-cli"); }).catch((reason) => setError(reason.message)); }, []);
  async function saveAnalyzer(event: FormEvent) {
    event.preventDefault(); setError(""); setMessage("");
    try { const value = await updateSettings({ model_path: modelPath.trim() || null, model_executable: executable.trim() }); setSettings(value); setMessage("Local analyzer settings saved."); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Analyzer settings could not be saved."); }
  }
  async function changeTheme(value: Theme) {
    try { await onThemeChange(value); setMessage("Preference saved."); setError(""); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Preference could not be saved."); }
  }
  return <main className="page-content"><header className="page-header"><div><span className="eyebrow">LOCAL BY DESIGN</span><h1>Settings</h1><p className="date-line">Report data and analysis stay on this device.</p></div></header>
    {error && <ErrorNotice message={error} />}{message && <SaveStatus>{message}</SaveStatus>}
    <section className="settings-card"><div className="section-heading"><div><span className="eyebrow">WORKSPACE</span><h2>Report location</h2></div><span className="read-only-pill">Read only</span></div><p className="muted">Markdown reports are stored outside the application repository.</p><code className="path-display">{settings?.workspace_path ?? "Loading…"}</code></section>
    <section className="settings-card"><div className="section-heading"><div><span className="eyebrow">APPEARANCE</span><h2>Theme</h2></div></div><label className="setting-row">Color theme<select value={theme} onChange={(event) => void changeTheme(event.target.value as Theme)}><option value="system">Use system setting</option><option value="light">Light</option><option value="dark">Dark</option></select></label></section>
    <section className="settings-card"><div className="section-heading"><div><span className="eyebrow">SEMANTIC REPORTS</span><h2>Local analyzer</h2></div></div><p className="muted">Use a local llama.cpp CLI and a model file. Commitly does not send repository content to a hosted service.</p><form className="backup-form" onSubmit={(event) => void saveAnalyzer(event)}><label>Model file path<input value={modelPath} onChange={(event) => setModelPath(event.target.value)} placeholder="/path/to/model.gguf" /></label><label>CLI executable<input value={executable} onChange={(event) => setExecutable(event.target.value)} /></label><button className="primary-button" type="submit">Save analyzer settings</button></form></section>
  </main>;
}
