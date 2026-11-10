import type { ReactNode } from "react";

export function EmptyState({ title, children, icon = "✳", action }: { title: string; children: ReactNode; icon?: string; action?: ReactNode }) {
  return <div className="empty-card"><span className="empty-icon" aria-hidden="true">{icon}</span><h3>{title}</h3><p>{children}</p>{action}</div>;
}

export function ErrorNotice({ title, message, onRetry }: { title?: string; message: string; onRetry?: () => void }) {
  return <div className="notice error-notice" role="alert">{title && <strong>{title}</strong>}<span>{message}</span>{onRetry && <button onClick={onRetry}>Try again</button>}</div>;
}

export function LoadingMessage({ children }: { children: ReactNode }) {
  return <p className="loading-line" role="status">{children}</p>;
}

export function SaveStatus({ children }: { children: ReactNode }) {
  return <span className="save-status" role="status" aria-live="polite">{children}</span>;
}
