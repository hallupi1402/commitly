import { useEffect, useState } from "react";
import { getSettings, updateSettings } from "../shared/journalApi";
import type { Theme } from "../shared/types";
import { JournalPage } from "../features/journal/JournalPage";
import { RepositoriesPage } from "../features/repositories/RepositoriesPage";
import { SettingsPage } from "../features/settings/SettingsPage";
import { TodayPage } from "../features/today/TodayPage";

type Section = "today" | "journal" | "repositories" | "settings";
const nav: { id: Section; label: string; icon: string }[] = [
  { id: "today", label: "Today", icon: "◷" }, { id: "journal", label: "Reports", icon: "▤" },
  { id: "repositories", label: "Repositories", icon: "◈" }, { id: "settings", label: "Settings", icon: "⚙" },
];

export function App() {
  const [section, setSection] = useState<Section>("today");
  const [theme, setTheme] = useState<Theme>("system");
  const [error, setError] = useState("");
  useEffect(() => {
    void getSettings().then((settings) => setTheme(settings.theme)).catch((reason) => setError(reason.message));
  }, []);
  useEffect(() => {
    const dark = theme === "dark" || (theme === "system" && window.matchMedia?.("(prefers-color-scheme: dark)").matches);
    document.documentElement.dataset.theme = dark ? "dark" : "light";
  }, [theme]);
  async function changeTheme(value: Theme) {
    const previous = theme;
    setTheme(value);
    try { await updateSettings({ theme: value }); }
    catch (reason) {
      setTheme(previous);
      setError(reason instanceof Error ? reason.message : "Theme could not be saved.");
      throw reason;
    }
  }
  return <div className="app-shell"><aside className="sidebar"><a href="#today" className="brand" onClick={(e) => { e.preventDefault(); setSection("today"); }}><span className="brand-mark">c.</span><span>commitly<small>WORK JOURNAL</small></span></a><div className="sidebar-label">YOUR SPACE</div><nav aria-label="Main navigation">{nav.map((item) => <button key={item.id} className={`nav-item ${section === item.id ? "active" : ""}`} aria-current={section === item.id ? "page" : undefined} onClick={() => setSection(item.id)}><span aria-hidden="true">{item.icon}</span>{item.label}{item.id === "today" && <span className="nav-dot" />}</button>)}</nav><div className="sidebar-footer"><span className="local-indicator" />Stored on this device<p>Markdown · Offline ready</p></div></aside>
    <div className="main-column"><header className="topbar"><div className="breadcrumb">My workspace <span>/</span> {nav.find((item) => item.id === section)?.label}</div><div className="offline-badge"><span />LOCAL JOURNAL</div></header>{error && <p className="global-error" role="alert">{error}</p>}{section === "today" && <TodayPage />}{section === "journal" && <JournalPage />}{section === "repositories" && <RepositoriesPage />}{section === "settings" && <SettingsPage theme={theme} onThemeChange={changeTheme} />}</div>
  </div>;
}
