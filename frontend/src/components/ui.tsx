import type { ReactNode } from 'react';

export type Tone = 'good' | 'warn' | 'bad' | 'neutral';

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

export function MetricCard(props: { label: string; value: string | number; hint?: string; tone?: Tone }) {
  return (
    <div className={`metric metric-${props.tone ?? 'neutral'}`}>
      <span className="metric-label">{props.label}</span>
      <strong>{props.value}</strong>
      {props.hint && <small>{props.hint}</small>}
    </div>
  );
}

export function Badge(props: { children: ReactNode; tone?: Tone; title?: string }) {
  return <span className={`badge badge-${props.tone ?? 'neutral'}`} title={props.title}>{props.children}</span>;
}

export function DataModeBadge(props: { mode?: string | null; compact?: boolean }) {
  const mode = String(props.mode ?? '').toUpperCase();
  const labels: Record<string, string> = {
    REAL: '真实数据',
    ESTIMATED: '估算数据',
    SAMPLE: '样本数据',
    MISSING: '数据缺失',
    MIXED: '混合数据',
  };
  const tone: Tone = mode === 'REAL'
    ? 'good'
    : mode === 'MISSING'
      ? 'bad'
      : mode === 'ESTIMATED' || mode === 'SAMPLE' || mode === 'MIXED'
        ? 'warn'
        : 'neutral';
  return <Badge tone={tone}>{props.compact ? (labels[mode] ?? '未知') : (labels[mode] ?? '数据未知')}</Badge>;
}

export function FreshnessBadge(props: { status?: string | null }) {
  const status = String(props.status ?? '').toUpperCase();
  const labels: Record<string, string> = {
    FRESH: '数据新鲜',
    STALE: '数据过期',
    MISSING: '新鲜度缺失',
    NOT_APPLICABLE: '非日频数据',
  };
  const tone: Tone = status === 'FRESH'
    ? 'good'
    : status === 'STALE'
      ? 'warn'
      : status === 'MISSING'
        ? 'bad'
        : 'neutral';
  return <Badge tone={tone}>{labels[status] ?? '新鲜度未知'}</Badge>;
}

export function EmptyState(props: { title: string; description: string }) {
  return (
    <div className="empty-state">
      <strong>{props.title}</strong>
      <p>{props.description}</p>
    </div>
  );
}

export function LoadingState(props: { title?: string; description?: string; rows?: number }) {
  const rows = props.rows ?? 4;
  return (
    <div className="loading-state" aria-busy="true" aria-live="polite">
      <div className="loading-copy">
        <strong>{props.title ?? '正在加载数据'}</strong>
        <p>{props.description ?? '正在读取本地数据库与分析结果。'}</p>
      </div>
      <div className="loading-bars">
        {Array.from({ length: rows }).map((_, index) => (
          <span key={index} style={{ width: `${92 - index * 11}%` }} />
        ))}
      </div>
    </div>
  );
}

export function ErrorState(props: { title?: string; description: string; onRetry?: () => void }) {
  return (
    <div className="error-state">
      <strong>{props.title ?? '加载失败'}</strong>
      <p>{props.description}</p>
      {props.onRetry && <button className="ghost-button" onClick={props.onRetry} type="button">重试</button>}
    </div>
  );
}
