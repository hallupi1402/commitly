import { useCallback, useEffect, useState } from "react";
import { ApiError } from "../../shared/api";
import { getReport, getReportConflict, refreshActivity, resolveReportConflict, saveReportContext, type DailyReport, type ReportConflict } from "../../shared/reportApi";
import { ErrorNotice, LoadingMessage } from "../../shared/Feedback";

function localDate() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
}

const EMPTY_REPORT_REVISION = '"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"';

export function TodayPage() {
  const date = localDate();
  const [report, setReport] = useState<DailyReport | null>(null);
  const [conflict, setConflict] = useState<ReportConflict | null>(null);
  const [etag, setEtag] = useState<string | null>(null);
  const [context, setContext] = useState("");
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const result = await getReport(date);
      setReport(result.data); setEtag(result.etag); setContext(result.data.user_context[0]?.text ?? "");
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 404) { setReport(null); setEtag(null); }
      else setError(reason instanceof Error ? reason.message : "Could not open today's report.");
    } finally { setLoading(false); }
  }, [date]);
  useEffect(() => { void load(); }, [load]);

  async function refresh() {
    setRefreshing(true); setError("");
    try {
      const result = await refreshActivity(date);
      const stale = result.repositories.find((item) => item.fetch_status !== "success");
      setStatus(stale ? stale.error ?? "Could not check the remote; using cached refs." : "Git activity refreshed.");
      await load();
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 409 && reason.payload?.conflict_id && reason.payload?.generated_report) setConflict(reason.payload as ReportConflict);
      else setError(reason instanceof Error ? reason.message : "Git activity could not be refreshed.");
    }
    finally { setRefreshing(false); }
  }

  async function saveContext() {
    try {
      const result = await saveReportContext(date, context.trim() || null, etag ?? EMPTY_REPORT_REVISION);
      setReport(result.data); setEtag(result.etag); setContext(result.data.user_context[0]?.text ?? ""); setStatus("Context saved.");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Context could not be saved."); }
  }

  async function resolveConflict(value: DailyReport | { date: string; keep_external: true }) {
    if (!conflict) return;
    try {
      const saved = await resolveReportConflict(conflict.date, conflict.conflict_id, value, conflict.external_revision);
      setReport(saved.data); setEtag(saved.etag); setConflict(null); setStatus("Report conflict resolved.");
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 409 && reason.payload?.details?.conflict_id) {
        setConflict(await getReportConflict(conflict.date, reason.payload.details.conflict_id));
        setError("The report changed again. Review the latest versions.");
      } else setError(reason instanceof Error ? reason.message : "The report conflict could not be resolved.");
    }
  }

  return <main className="page-content">
    <header className="page-header"><div><span className="eyebrow">CAPTURE TODAY. CONTINUE TOMORROW.</span><h1>Today’s report</h1><p className="date-line">{new Intl.DateTimeFormat(undefined, { dateStyle: "full" }).format(new Date(`${date}T12:00:00`))}</p></div><button className="primary-button" onClick={() => void refresh()} disabled={refreshing}>{refreshing ? "Reading Git…" : "Refresh pushed activity"}</button></header>
    <p role="status" aria-live="polite">{status}</p>
    {error && <ErrorNotice title="Report unavailable" message={error} onRetry={() => void load()} />}
    {conflict && <ReportConflictDialog conflict={conflict} onResolve={(value) => void resolveConflict(value)} onClose={() => setConflict(null)} />}
    {!loading && <section className="browse-card"><div className="section-heading"><div><span className="eyebrow">YOUR CONTEXT</span><h2>Add a note for today</h2></div></div><label htmlFor="report-context">Optional one-line context</label><input id="report-context" value={context} onChange={(event) => setContext(event.target.value)} maxLength={500} /><button className="secondary-button" onClick={() => void saveContext()}>Save context</button></section>}
    {loading ? <LoadingMessage>Opening today’s report…</LoadingMessage> : report ? <>
      {report.analysis_status === "unavailable" && <p className="form-error" role="status">Git source activity is saved, but semantic analysis is unavailable. Configure a local llama.cpp model to generate prose.</p>}
      {report.analysis_status === "partial" && <p className="form-error" role="status">Some changed files could not be analyzed. Review their notes in the source log.</p>}
      <section className="browse-card"><span className="eyebrow">TÓM TẮT</span><ClaimText claim={report.summary} /></section>
      <section className="timeline-section"><div className="section-heading"><div><span className="eyebrow">ĐIỂM CHÍNH</span><h2>What changed</h2></div></div>{report.highlights.length ? <ul>{report.highlights.map((item) => <li key={item.id}><ClaimText claim={item} /></li>)}</ul> : <p className="muted">Detailed highlights appear when the local analyzer is available.</p>}</section>
      <section className="timeline-section"><div className="section-heading"><div><span className="eyebrow">CHI TIẾT</span><h2>Work explained</h2></div></div>{report.details.length ? report.details.map((item) => <p key={item.id}><ClaimText claim={item} /></p>) : <p className="muted">No semantic details yet.</p>}</section>
      <EvidenceLog report={report} />
    </> : <section className="browse-card"><h2>No report yet</h2><p>Choose Repositories in the sidebar, then refresh pushed commits. Commitly reads only the selected remote’s available history.</p></section>}
  </main>;
}

export function EvidenceLog({ report }: { report: DailyReport }) {
  return <section className="timeline-section"><div className="section-heading"><div><span className="eyebrow">LOG NGUỒN</span><h2>Git evidence</h2></div></div>{report.evidence.map((item) => <article id={`evidence-${item.id}`} className="browse-card" key={item.id}><strong>{item.repository_name}</strong><p>{item.subject}</p><code>{item.commit_id}</code><p className="muted">{item.repository_path} · {new Date(item.authored_at).toLocaleString()}</p><ul>{item.changed_paths.map((path) => <li key={path}><code>{path}</code></li>)}</ul></article>)}</section>;
}

export function ClaimText({ claim }: { claim: { text: string; evidence_ids: string[]; certainty?: string } }) {
  return <>{claim.certainty === "uncertain" ? "Có thể: " : ""}{claim.text} {claim.evidence_ids.map((id) => <a className="evidence-link" key={id} href={`#evidence-${id}`} aria-label={`View source evidence ${id}`}>Source</a>)}</>;
}

function ReportConflictDialog({ conflict, onResolve, onClose }: { conflict: ReportConflict; onResolve: (report: DailyReport | { date: string; keep_external: true }) => void; onClose: () => void }) {
  return <div className="modal-scrim"><section className="conflict-card" role="dialog" aria-modal="true" aria-labelledby="report-conflict-title"><span className="eyebrow">EXTERNAL EDIT DETECTED</span><h2 id="report-conflict-title">Choose the report to keep</h2><p>Commitly preserved both report versions. Pick one to save; the other remains available until resolution succeeds.</p><div className="conflict-columns"><article><h3>Edited file</h3><pre>{conflict.external_markdown.split("<!-- commitly:report-data v1")[0]}</pre><button className="secondary-button" onClick={() => onResolve({ date: conflict.date, keep_external: true })}>Keep edited file</button></article><article><h3>Generated report</h3><ReportPreview report={conflict.generated_report} /><button className="primary-button" onClick={() => onResolve(conflict.generated_report)}>Keep generated report</button></article></div><button className="secondary-button" onClick={onClose}>Review later</button></section></div>;
}

function ReportPreview({ report }: { report: DailyReport }) {
  return <pre><strong>Tóm tắt</strong>{"\n"}{report.summary.text}{"\n\n"}<strong>Điểm chính</strong>{"\n"}{report.highlights.map((item) => `• ${item.text}`).join("\n") || "—"}{"\n\n"}<strong>Chi tiết</strong>{"\n"}{report.details.map((item) => `• ${item.text}`).join("\n") || "—"}{"\n\n"}<strong>Log nguồn</strong>{"\n"}{report.evidence.map((item) => `${item.repository_name}: ${item.subject}`).join("\n") || "—"}</pre>;
}
