import { useEffect, useMemo, useState } from 'react';
import { apiGet } from '../api/client';
import type { DataCredibilityOverview } from '../api/types';
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

function cleanMarkdownLine(line: string) {
  return line.replace(/^[-*]\s*/, '').replace(/`/g, '').trim();
}

function sectionItems(markdown: string, heading: string, limit = 4) {
  const lines = markdown.split('\n');
  const start = lines.findIndex((line) => line.includes(heading));
  if (start < 0) return [];
  const result: string[] = [];
  for (let index = start + 1; index < lines.length; index += 1) {
    const line = lines[index];
    if (line.startsWith('## ')) break;
    if (line.trim().startsWith('-')) result.push(cleanMarkdownLine(line));
    if (result.length >= limit) break;
  }
  return result;
}

function credibilityLabel(mode?: string) {
  if (mode === 'REAL') return '真实数据';
  if (mode === 'ESTIMATED') return '估算数据';
  if (mode === 'SAMPLE') return '样本数据';
  if (mode === 'MISSING') return '数据缺失';
  if (mode === 'MIXED') return '混合数据';
  return '数据未知';
}

function credibilityTone(mode?: string): 'good' | 'warn' | 'bad' | 'neutral' {
  if (mode === 'REAL') return 'good';
  if (mode === 'MISSING') return 'bad';
  if (mode === 'ESTIMATED' || mode === 'SAMPLE' || mode === 'MIXED') return 'warn';
  return 'neutral';
}

export function ReportsPage() {
  const [reports, setReports] = useState<ReportIndex[]>([]);
  const [latest, setLatest] = useState<ReportDetail | null>(null);
  const [credibility, setCredibility] = useState<DataCredibilityOverview | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    apiGet<{ data: ReportIndex[] }>('/api/reports/daily')
      .then((res) => setReports(res.data))
      .catch((err) => setError(String(err)));
    apiGet<{ data: ReportDetail }>('/api/reports/daily/latest')
      .then((res) => setLatest(res.data))
      .catch((err) => setError(String(err)));
    apiGet<{ data: DataCredibilityOverview }>('/api/data/credibility')
      .then((res) => setCredibility(res.data))
      .catch(() => undefined);
  }, []);

  const briefing = useMemo(() => {
    const markdown = latest?.markdown ?? '';
    const market = sectionItems(markdown, '市场状态', 3);
    const sectors = sectionItems(markdown, '行业强弱', 3);
    const stocks = sectionItems(markdown, '个股分析重点', 3);
    const funds = sectionItems(markdown, '基金观察', 3);
    const etfs = sectionItems(markdown, 'ETF 深度观察', 3);
    const risks = sectionItems(markdown, '风险事件', 4);
    const tomorrow = sectionItems(markdown, '明日关注', 4);
    const riskLine = risks.find((item) => !item.includes('暂无'));
    const marketSummary = market.find((item) => item.startsWith('摘要')) ?? market[0];
    return {
      main: riskLine ? `需要复核：${riskLine}` : (marketSummary ?? latest?.summary ?? '暂无日报结论'),
      review: riskLine ?? '暂无高优先级风险事件，保持观察。',
      tomorrow: tomorrow[0] ?? '明日先看市场评分、风险事件和观察池变化。',
      market,
      sectors,
      stocks,
      funds,
      etfs,
      risks,
      tomorrowItems: tomorrow,
    };
  }, [latest]);

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

      <Card title="今日投资简报" description="先看结论、复核事项和明日观察，再进入 Markdown 原文归档。">
        {latest ? (
          <>
            <div className="analysis-summary">
              <div><span>最重要变化</span><strong>{briefing.main}</strong></div>
              <div><span>是否需要复核</span><strong>{briefing.review}</strong></div>
              <div><span>明日先看</span><strong>{briefing.tomorrow}</strong></div>
              <div>
                <span>数据边界</span>
                <strong>
                  <Badge tone={credibilityTone(credibility?.summary.overall_mode)}>{credibilityLabel(credibility?.summary.overall_mode)}</Badge>
                  {' '}· 最新 {credibility?.summary.latest_data_date ?? latest.report_date}
                </strong>
              </div>
            </div>
            {credibility?.summary.warning && <div className="alert alert-warning">{credibility.summary.warning}</div>}
            <div className="grid-two">
              <div className="review-item-list">
                <strong>市场 / 行业</strong>
                {[...briefing.market, ...briefing.sectors].slice(0, 5).map((item) => <p key={item}>{item}</p>)}
                {briefing.market.length === 0 && briefing.sectors.length === 0 && <p>暂无市场和行业简报。</p>}
              </div>
              <div className="review-item-list">
                <strong>资产分区</strong>
                {[...briefing.stocks, ...briefing.funds, ...briefing.etfs].slice(0, 6).map((item) => <p key={item}>{item}</p>)}
                {briefing.stocks.length === 0 && briefing.funds.length === 0 && briefing.etfs.length === 0 && <p>暂无股票、基金或 ETF 简报。</p>}
              </div>
            </div>
          </>
        ) : (
          <EmptyState title="暂无简报" description="执行每日更新后，这里会先展示今日结论、复核事项和明日观察。" />
        )}
      </Card>

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
