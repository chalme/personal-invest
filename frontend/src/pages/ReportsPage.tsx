import { useEffect, useState } from 'react';
import { apiGet } from '../api/client';
import { Badge, Card, EmptyState } from '../components/ui';

type ReportIndex = {
  id: number;
  report_date: string;
  title: string;
  summary?: string;
  markdown_path?: string;
};

type ReportDetail = ReportIndex & {
  markdown: string;
  html: string;
};

export function ReportsPage() {
  const [reports, setReports] = useState<ReportIndex[]>([]);
  const [latest, setLatest] = useState<ReportDetail | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    apiGet<{ data: ReportIndex[] }>('/api/reports/daily')
      .then((res) => setReports(res.data))
      .catch((err) => setError(String(err)));
    apiGet<{ data: ReportDetail }>('/api/reports/daily/latest')
      .then((res) => setLatest(res.data))
      .catch((err) => setError(String(err)));
  }, []);

  return (
    <div className="page-stack">
      <div className="page-title-row">
        <div>
          <h2>投资日报</h2>
          <p>归档每日市场状态、行业强弱、个股变化、风险事件和明日关注。</p>
        </div>
        {latest && <Badge tone="good">最新：{latest.report_date}</Badge>}
      </div>

      {error && <Card><div className="error-box">{error}</div></Card>}

      <div className="grid-two reports-layout">
        <Card title="日报列表" description="按交易日倒序排列。">
          {reports.length === 0 ? (
            <EmptyState title="暂无日报" description="执行 make daily 后会在这里出现每日投资报告。" />
          ) : (
            <div className="report-list">
              {reports.map((item) => (
                <button
                  key={item.id}
                  className={latest?.report_date === item.report_date ? 'report-item active' : 'report-item'}
                  onClick={() => apiGet<{ data: ReportDetail }>(`/api/reports/daily/${item.report_date}`).then((res) => setLatest(res.data))}
                >
                  <strong>{item.title}</strong>
                  <span>{item.summary || '市场、行业、个股、风险和信号摘要'}</span>
                </button>
              ))}
            </div>
          )}
        </Card>

        <Card title={latest?.title ?? '最新日报'} description="Markdown 生成的可追溯报告。">
          {latest?.html ? (
            <article className="report-content" dangerouslySetInnerHTML={{ __html: latest.html }} />
          ) : (
            <EmptyState title="暂无内容" description="日报存在后会展示完整 Markdown 渲染内容。" />
          )}
        </Card>
      </div>
    </div>
  );
}
