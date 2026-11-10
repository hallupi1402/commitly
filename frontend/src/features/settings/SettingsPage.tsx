import { useEffect, useState, type FormEvent } from "react";
import { getBackupStatus, getSettings, updateBackup } from "../../shared/journalApi";
import type { BackupStatus, Settings, Theme } from "../../shared/types";
import { ErrorNotice, SaveStatus } from "../../shared/Feedback";

const PRIVACY_ASSERTION = "I confirm that this Git destination is private and appropriate for storing my personal journal.";

export function SettingsPage({ theme, onThemeChange }: { theme: Theme; onThemeChange: (theme: Theme) => void }) {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [backup, setBackup] = useState<BackupStatus | null>(null);
  const [remote, setRemote] = useState("");
  const [branch, setBranch] = useState("main");
  const [confirmed, setConfirmed] = useState(false);
  const [enabled, setEnabled] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  useEffect(() => { void Promise.all([getSettings(), getBackupStatus()]).then(([value, status]) => {
    setSettings(value); setBackup(status); setRemote(""); setBranch(status.branch ?? "main"); setEnabled(status.enabled); setConfirmed(status.private_confirmed);
  }).catch((reason) => setError(reason.message)); }, []);

  async function saveBackup(event: FormEvent) {
    event.preventDefault(); setMessage(""); setError("");
    try {
      const status = await updateBackup({ enabled, remote_url: remote.trim() || null, branch: branch.trim() || "main", private_confirmed: confirmed });
      setBackup(status); setRemote(""); setMessage("Backup settings saved.");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Backup settings could not be saved."); }
  }
  async function changeTheme(value: Theme) {
    onThemeChange(value);
    setMessage("Preference saved.");
  }

  return <main className="page-content"><header className="page-header"><div><span className="eyebrow">LOCAL BY DESIGN</span><h1>Settings</h1><p className="date-line">Your journal stays on this device unless you configure a backup.</p></div></header>
    {error && <ErrorNotice message={error} />}{message && <SaveStatus>{message}</SaveStatus>}
    <section className="settings-card"><div className="section-heading"><div><span className="eyebrow">WORKSPACE</span><h2>Journal location</h2></div><span className="read-only-pill">Read only</span></div><p className="muted">Personal journal files are stored outside the application repository.</p><code className="path-display">{settings?.workspace_path ?? "Loading…"}</code></section>
    <section className="settings-card"><div className="section-heading"><div><span className="eyebrow">APPEARANCE</span><h2>Theme</h2></div></div><label className="setting-row">Color theme<select value={theme} onChange={(e) => void changeTheme(e.target.value as Theme)}><option value="system">Use system setting</option><option value="light">Light</option><option value="dark">Dark</option></select></label></section>
    <section className="settings-card"><div className="section-heading"><div><span className="eyebrow">OPTIONAL SAFETY COPY</span><h2>Git backup</h2></div><span className={`status-pill ${backup?.enabled ? "online" : "offline"}`}>{backup?.enabled ? "Enabled" : "Not enabled"}</span></div><p className="muted">Commitly creates a daily local commit and pushes only to the destination you choose. Credentials come from your Git credential helper.</p>
      <div className="backup-status-grid"><div><small>Destination</small><strong>{backup?.destination_label ?? "Not configured"}</strong></div><div><small>Last successful push</small><strong>{backup?.last_success_at ? new Date(backup.last_success_at).toLocaleString() : "Never"}</strong></div><div><small>Local commits to push</small><strong>{backup?.pending_commits ?? 0}</strong></div></div>
      {backup?.last_error && <div className="notice error-notice" role="alert"><strong>Last backup failed</strong><span>{backup.last_error}</span></div>}
      <form className="backup-form" onSubmit={(event) => void saveBackup(event)}><label>Git destination URL<input value={remote} onChange={(e) => { setRemote(e.target.value); setConfirmed(false); }} placeholder={backup?.destination_label ?? "git@host:private/journal.git"} autoComplete="off" /></label><p className="field-hint">Enter a URL to select or change the destination. Leave blank to retain a configured destination. Use your system Git credential helper for authentication.</p><label>Branch<input value={branch} onChange={(e) => setBranch(e.target.value)} /></label><label className="check-row"><input type="checkbox" checked={confirmed} onChange={(e) => setConfirmed(e.target.checked)} /><span>{PRIVACY_ASSERTION}<small>Commitly cannot verify whether a remote is private.</small></span></label><label className="check-row"><input type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} /><span>Enable daily backup and push</span></label><button className="primary-button" disabled={enabled && (!confirmed || (!remote.trim() && !backup?.configured))}>Save backup settings</button></form>
    </section>
  </main>;
}
