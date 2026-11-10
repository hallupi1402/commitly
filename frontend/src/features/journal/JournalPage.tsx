import { useEffect, useState } from "react";
import { getReport, getReportDates, type DailyReport } from "../../shared/reportApi";
import { ErrorNotice, LoadingMessage } from "../../shared/Feedback";
import { ClaimText, EvidenceLog } from "../today/TodayPage";

export function JournalPage() {
  const [dates, setDates] = useState<string[]>([]);
  const [report, setReport] = useState<DailyReport | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  async function load() {
    setLoading(true);
    try { setDates(await getReportDates()); setError(""); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Report history could not be loaded."); }
    finally { setLoading(false); }
  }
  useEffect(() => { void load(); }, []);
  async function open(day: string) {
    try { setReport((await getReport(day)).data); setError(""); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Report could not be opened."); }
  }
  return <main className="page-content"><header className="page-header"><div><span className="eyebrow">PAST WORK, READY TO RESUME</span><h1>Report history</h1><p className="date-line">Browse saved daily reports and their Git evidence.</p></div></header>
    {error && <ErrorNotice title="History unavailable" message={error} onRetry={() => void load()} />}
    {loading ? <LoadingMessage>Loading report dates…</LoadingMessage> : dates.length ? <section className="browse-card"><label htmlFor="report-date">Open a report</label><select id="report-date" defaultValue="" onChange={(event) => event.target.value && void open(event.target.value)}><option value="" disabled>Select date</option>{dates.map((day) => <option key={day} value={day}>{day}</option>)}</select><div className="date-picker-row">{dates.map((day) => <button className="secondary-button" key={day} onClick={() => void open(day)}>{day}</button>)}</div></section> : <section className="browse-card"><h2>No saved reports</h2><p>Refresh a selected repository to create your first report. Go to Today in the sidebar to refresh activity.</p></section>}
    {report && <><section className="browse-card"><span className="eyebrow">TÓM TẮT</span><h2>{report.date}</h2><p><ClaimText claim={report.summary} /></p></section><section className="timeline-section"><h2>Điểm chính</h2>{report.highlights.map((item) => <p key={item.id}><ClaimText claim={item} /></p>)}<h2>Chi tiết</h2>{report.details.map((item) => <p key={item.id}><ClaimText claim={item} /></p>)}</section><EvidenceLog report={report} /></>}
  </main>;
}
