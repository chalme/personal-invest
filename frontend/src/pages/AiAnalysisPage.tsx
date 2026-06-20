import { useEffect, useState } from 'react';
import { apiGet } from '../api/client';
import { Badge, Card, EmptyState, LoadingState } from '../components/ui';

type AiSection = {
  title: string;
  content: string;
};

type AiResult = {
  analysis_type: string;
  target: string;
  data_version?: string | null;
  generated_at: string;
  sections: AiSection[];
};

type Mode = 'market' | 'portfolio' | 'stock' | 'fund';

const modeOptions: { key: Mode; label: string; description: string }[] = [
  { key: 'market', label: '市场解释', description: '解释市场状态、强弱方向和仓位含义。' },
  { key: 'portfolio', label: '持仓解释', description: '解释组合风险、集中度和复盘重点。' },
  { key: 'stock', label: '个股解释', description: '解释个股评分、风险点和观察边界。' },
  { key: 'fund', label: '基金解释', description: '解释基金收益、回撤、波动和观察边界。' },
];

export function AiAnalysisPage() {
  const [mode, setMode] = useState<Mode>('market');
  const [symbol, setSymbol] = useState('600519.SH');
  const [fundSymbol, setFundSymbol] = useState('000001.OF');
  const [result, setResult] = useState<AiResult | null>(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function runAnalysis(nextMode = mode) {
    try {
      setLoading(true);
      setError('');
      const path = nextMode === 'stock' ? `/api/ai/stock?symbol=${encodeURIComponent(symbol)}` : nextMode === 'fund' ? `/api/ai/fund?symbol=${encodeURIComponent(fundSymbol)}` : `/api/ai/${nextMode}`;
      const res = await apiGet<{ data: AiResult }>(path);
      setResult(res.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    runAnalysis('market');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="page-stack">
      <div className="page-title-row">
        <div>
          <h2>AI 分析</h2>
          <p>基于系统数据做结构化解释，不调用外部模型也可运行，不直接给交易指令。</p>
        </div>
        {result && <Badge tone="neutral">数据版本：{result.data_version ?? '-'}</Badge>}
      </div>

      <Card title="分析类型" description="选择需要解释的对象。">
        <div className="ai-controls">
          <div className="ai-mode-grid">
            {modeOptions.map((item) => (
              <button
                key={item.key}
                className={mode === item.key ? 'ai-mode-card active' : 'ai-mode-card'}
                onClick={() => {
                  setMode(item.key);
                  if (item.key !== 'stock' && item.key !== 'fund') runAnalysis(item.key);
                }}
              >
                <strong>{item.label}</strong>
                <span>{item.description}</span>
              </button>
            ))}
          </div>
          {mode === 'stock' && (
            <div className="stock-query-row">
              <input value={symbol} onChange={(event) => setSymbol(event.target.value)} placeholder="输入股票代码，如 600519.SH" />
              <button className="primary-button" onClick={() => runAnalysis('stock')}>分析个股</button>
            </div>
          )}
          {mode === 'fund' && (
            <div className="stock-query-row">
              <input value={fundSymbol} onChange={(event) => setFundSymbol(event.target.value)} placeholder="输入基金代码，如 000001.OF" />
              <button className="primary-button" onClick={() => runAnalysis('fund')}>分析基金</button>
            </div>
          )}
        </div>
      </Card>

      {error && <Card><div className="error-box">{error}</div></Card>}
      {loading && <LoadingState title="正在生成结构化解释" description="基于系统数据整理市场、持仓、个股或基金分析。" rows={3} />}

      {!loading && result ? (
        <Card title={`${result.target} · ${result.analysis_type}`} description={`生成时间：${result.generated_at}`}>
          <div className="ai-section-grid">
            {result.sections.map((section) => (
              <div className="ai-section" key={section.title}>
                <span>{section.title}</span>
                <p>{section.content}</p>
              </div>
            ))}
          </div>
        </Card>
      ) : !loading && (
        <EmptyState title="暂无分析" description="选择市场、持仓、个股或基金后生成解释。" />
      )}
    </div>
  );
}
