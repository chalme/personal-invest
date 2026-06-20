import type { ReactNode } from 'react';

export function Card(props: { title?: string; description?: string; children: ReactNode; className?: string }) {
  return (
    <section className={`card ${props.className ?? ''}`}>
      {(props.title || props.description) && (
        <header className="card-header">
          {props.title && <h2>{props.title}</h2>}
          {props.description && <p>{props.description}</p>}
        </header>
      )}
      {props.children}
    </section>
  );
}

export function MetricCard(props: { label: string; value: string | number; hint?: string; tone?: 'good' | 'warn' | 'bad' | 'neutral' }) {
  return (
    <div className={`metric metric-${props.tone ?? 'neutral'}`}>
      <span className="metric-label">{props.label}</span>
      <strong>{props.value}</strong>
      {props.hint && <small>{props.hint}</small>}
    </div>
  );
}

export function Badge(props: { children: ReactNode; tone?: 'good' | 'warn' | 'bad' | 'neutral' }) {
  return <span className={`badge badge-${props.tone ?? 'neutral'}`}>{props.children}</span>;
}

export function EmptyState(props: { title: string; description: string }) {
  return (
    <div className="empty-state">
      <strong>{props.title}</strong>
      <p>{props.description}</p>
    </div>
  );
}

