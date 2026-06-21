import { FormEvent, useEffect, useMemo, useState } from 'react';
import { apiDelete, apiGet, apiPost } from '../api/client';
import { Badge, Card, EmptyState, LoadingState } from '../components/ui';

type WatchlistItem = {
  id?: number;
  symbol: string;
  name: string;
  asset_type?: string;
  market?: string;
  group_name?: string | null;
  reason?: string | null;
  priority?: number;
  status?: string;
};

type WatchlistForm = {
  symbol: string;
  name: string;
  asset_type: string;
  group_name: string;
  reason: string;
  priority: number;
};

const initialForm: WatchlistForm = {
  symbol: '',
  name: '',
  asset_type: 'STOCK',
  group_name: '',
  reason: '',
  priority: 5,
};

function watchState(row: WatchlistItem) {
  if ((row.status ?? 'ACTIVE') !== 'ACTIVE') return '关注失效';
  if (!row.reason || !row.group_name) return '数据待补齐';
  if ((row.priority ?? 0) >= 8) return '重点研究';
  if ((row.priority ?? 0) <= 2) return '低优先级';
  return '常规观察';
}

function watchTone(state: string): 'good' | 'warn' | 'bad' | 'neutral' {
  if (state === '重点研究') return 'good';
  if (state === '数据待补齐' || state === '低优先级') return 'warn';
  if (state === '关注失效') return 'bad';
  return 'neutral';
}

function nextStep(row: WatchlistItem) {
  const state = watchState(row);
  if (state === '重点研究') return '继续跟踪价格、估值和风险事件，不因样本数据提升排序。';
  if (state === '数据待补齐') return '补充关注理由、分组或执行每日更新后再判断优先级。';
  if (state === '低优先级') return '保留低频观察，若长期没有新证据可考虑移除。';
  if (state === '关注失效') return '复核是否仍有研究价值，必要时从观察池移除。';
  return '按既定理由继续观察，等待评分、行业或风险出现变化。';
}

export function WatchlistPage() {
  const [rows, setRows] = useState<WatchlistItem[]>([]);
  const [form, setForm] = useState<WatchlistForm>(initialForm);
  const [keyword, setKeyword] = useState('');
  const [assetFilter, setAssetFilter] = useState('ALL');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  async function load() {
    setLoading(true);
    setError('');
    try {
      const res = await apiGet<{ data: WatchlistItem[] }>('/api/watchlist');
      setRows(res.data);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const filteredRows = useMemo(() => {
    const value = keyword.trim().toLowerCase();
    return rows.filter((row) => {
      const matchesAsset = assetFilter === 'ALL' || (row.asset_type ?? 'STOCK') === assetFilter;
      const haystack = `${row.symbol} ${row.name} ${row.asset_type ?? ''} ${row.group_name ?? ''} ${row.reason ?? ''}`.toLowerCase();
      const matchesKeyword = !value || haystack.includes(value);
      return matchesAsset && matchesKeyword;
    });
  }, [assetFilter, keyword, rows]);
  const highPriorityRows = rows.filter((row) => watchState(row) === '重点研究');
  const dataMissingRows = rows.filter((row) => watchState(row) === '数据待补齐');
  const staleRows = rows.filter((row) => watchState(row) === '关注失效' || watchState(row) === '低优先级');
  const assetCounts = rows.reduce<Record<string, number>>((acc, row) => {
    const key = row.asset_type ?? 'STOCK';
    acc[key] = (acc[key] ?? 0) + 1;
    return acc;
  }, {});

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!form.symbol.trim()) {
      setError('标的代码不能为空');
      return;
    }
    setSaving(true);
    setError('');
    try {
      await apiPost('/api/watchlist', {
        symbol: form.symbol.trim().toUpperCase(),
        name: form.name.trim() || form.symbol.trim().toUpperCase(),
        asset_type: form.asset_type,
        market: 'A_SHARE',
        group_name: form.group_name.trim() || null,
        reason: form.reason.trim() || null,
        priority: Number(form.priority || 0),
      });
      setForm(initialForm);
      await load();
    } catch (err) {
      setError(String(err));
    } finally {
      setSaving(false);
    }
  }

  async function remove(symbol: string) {
    const ok = window.confirm(`确认从观察池移除 ${symbol}？`);
    if (!ok) return;
    setError('');
    try {
      await apiDelete(`/api/watchlist/${encodeURIComponent(symbol)}`);
      await load();
    } catch (err) {
      setError(String(err));
    }
  }

  return (
    <div className="page-stack">
      <div className="page-title-row">
        <div>
          <h2>观察池</h2>
          <p>维护关注股票、ETF、基金、分组、备注和优先级。这里只做研究观察，不代表买入指令。</p>
        </div>
        <Badge tone="neutral">{rows.length} 个关注</Badge>
      </div>

      <Card className="conclusion-card" title="观察池研究状态" description="先看研究状态分层，再决定是否继续跟踪、补数据或清理。">
        <div className="analysis-summary">
          <div><span>正在研究</span><strong>{highPriorityRows.length} 个重点标的</strong></div>
          <div><span>数据待补齐</span><strong>{dataMissingRows.length} 个标的</strong></div>
          <div><span>可能失效</span><strong>{staleRows.length} 个低优先级或非 ACTIVE 标的</strong></div>
          <div><span>资产分布</span><strong>{Object.entries(assetCounts).map(([key, value]) => `${key}:${value}`).join(' / ') || '暂无'}</strong></div>
        </div>
        <div className="grid-two">
          <div className="review-item-list">
            <strong>值得继续观察</strong>
            {highPriorityRows.slice(0, 5).map((row) => <p key={row.symbol}>{row.name}：{row.reason ?? '暂无理由'} · {nextStep(row)}</p>)}
            {highPriorityRows.length === 0 && <p>暂无高优先级研究标的；可以先补充理由和分组，再提升优先级。</p>}
          </div>
          <div className="review-item-list">
            <strong>待补齐 / 待清理</strong>
            {[...dataMissingRows, ...staleRows].slice(0, 5).map((row) => <p key={row.symbol}>{row.name}：{watchState(row)} · {nextStep(row)}</p>)}
            {dataMissingRows.length === 0 && staleRows.length === 0 && <p>观察池字段完整，暂无明显待清理标的。</p>}
          </div>
        </div>
      </Card>

      <Card title="新增 / 更新观察标的" description="相同代码会覆盖已有资产类型、备注和优先级。">
        <form className="form-grid" onSubmit={submit}>
          <label>
            标的代码
            <input value={form.symbol} onChange={(event) => setForm({ ...form, symbol: event.target.value })} placeholder="600519.SH / 510300.SH / 000001.OF" />
          </label>
          <label>
            名称
            <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="贵州茅台 / 沪深300ETF / 基金名称" />
          </label>
          <label>
            资产类型
            <select value={form.asset_type} onChange={(event) => setForm({ ...form, asset_type: event.target.value })}>
              <option value="STOCK">股票</option>
              <option value="ETF">ETF / LOF</option>
              <option value="FUND">场外基金</option>
            </select>
          </label>
          <label>
            分组 / 行业 / 类型
            <input value={form.group_name} onChange={(event) => setForm({ ...form, group_name: event.target.value })} placeholder="消费 / 宽基 / 主动基金" />
          </label>
          <label>
            优先级
            <input type="number" min={0} max={10} value={form.priority} onChange={(event) => setForm({ ...form, priority: Number(event.target.value) })} />
          </label>
          <label className="form-wide">
            关注理由
            <input value={form.reason} onChange={(event) => setForm({ ...form, reason: event.target.value })} placeholder="例如：高质量公司、宽基 Beta、基金经理观察" />
          </label>
          <div className="form-actions form-wide">
            <button className="primary-button" type="submit" disabled={saving}>{saving ? '保存中...' : '保存观察标的'}</button>
            {error && <span className="form-error">{error}</span>}
          </div>
        </form>
      </Card>

      <Card>
        <div className="toolbar-row">
          <input className="search-input" value={keyword} onChange={(event) => setKeyword(event.target.value)} placeholder="搜索代码、名称、类型、分组或理由" />
          <select className="search-select" value={assetFilter} onChange={(event) => setAssetFilter(event.target.value)}>
            <option value="ALL">全部资产</option>
            <option value="STOCK">股票</option>
            <option value="ETF">ETF / LOF</option>
            <option value="FUND">场外基金</option>
          </select>
          <button className="ghost-button" onClick={load} type="button">刷新</button>
        </div>
        {loading ? (
          <LoadingState title="正在加载观察池" description="读取观察标的、资产类型、分组和备注。" rows={3} />
        ) : filteredRows.length === 0 ? (
          <EmptyState title="暂无观察标的" description="添加股票、ETF 或基金后，这里会展示资产类型、分组、优先级和关注理由。" />
        ) : (
          <table className="data-table">
            <thead><tr><th>标的</th><th>类型</th><th>分组</th><th>优先级</th><th>关注理由</th><th>研究状态</th><th>下一步观察</th><th>操作</th></tr></thead>
            <tbody>
              {filteredRows.map((row) => (
                <tr key={row.symbol}>
                  <td><strong>{row.name}</strong><br /><small>{row.symbol}</small></td>
                  <td><Badge tone="neutral">{row.asset_type ?? 'STOCK'}</Badge></td>
                  <td>{row.group_name ?? '-'}</td>
                  <td>{row.priority ?? 0}</td>
                  <td>{row.reason ?? '-'}</td>
                  <td><Badge tone={watchTone(watchState(row))}>{watchState(row)}</Badge></td>
                  <td><small>{nextStep(row)}</small></td>
                  <td><button className="danger-button" onClick={() => remove(row.symbol)} type="button">移除</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
