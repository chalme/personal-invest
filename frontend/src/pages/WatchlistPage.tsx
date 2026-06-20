import { FormEvent, useEffect, useMemo, useState } from 'react';
import { apiDelete, apiGet, apiPost } from '../api/client';
import { Badge, Card, EmptyState, LoadingState } from '../components/ui';

type WatchlistItem = {
  id?: number;
  symbol: string;
  name: string;
  market?: string;
  group_name?: string | null;
  reason?: string | null;
  priority?: number;
  status?: string;
};

type WatchlistForm = {
  symbol: string;
  name: string;
  group_name: string;
  reason: string;
  priority: number;
};

const initialForm: WatchlistForm = {
  symbol: '',
  name: '',
  group_name: '',
  reason: '',
  priority: 5,
};

export function WatchlistPage() {
  const [rows, setRows] = useState<WatchlistItem[]>([]);
  const [form, setForm] = useState<WatchlistForm>(initialForm);
  const [keyword, setKeyword] = useState('');
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
    if (!value) return rows;
    return rows.filter((row) => `${row.symbol} ${row.name} ${row.group_name ?? ''} ${row.reason ?? ''}`.toLowerCase().includes(value));
  }, [keyword, rows]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!form.symbol.trim()) {
      setError('股票代码不能为空');
      return;
    }
    setSaving(true);
    setError('');
    try {
      await apiPost('/api/watchlist', {
        symbol: form.symbol.trim().toUpperCase(),
        name: form.name.trim() || form.symbol.trim().toUpperCase(),
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
    const ok = window.confirm(`确认从自选股移除 ${symbol}？`);
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
          <h2>自选股</h2>
          <p>维护关注股票、分组、备注和优先级。这里只做观察池，不代表买入指令。</p>
        </div>
        <Badge tone="neutral">{rows.length} 个关注</Badge>
      </div>

      <Card title="新增 / 更新自选股" description="相同股票代码会覆盖已有备注和优先级。">
        <form className="form-grid" onSubmit={submit}>
          <label>
            股票代码
            <input value={form.symbol} onChange={(event) => setForm({ ...form, symbol: event.target.value })} placeholder="600519.SH" />
          </label>
          <label>
            名称
            <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} placeholder="贵州茅台" />
          </label>
          <label>
            分组 / 行业
            <input value={form.group_name} onChange={(event) => setForm({ ...form, group_name: event.target.value })} placeholder="消费" />
          </label>
          <label>
            优先级
            <input type="number" min={0} max={10} value={form.priority} onChange={(event) => setForm({ ...form, priority: Number(event.target.value) })} />
          </label>
          <label className="form-wide">
            关注理由
            <input value={form.reason} onChange={(event) => setForm({ ...form, reason: event.target.value })} placeholder="例如：高质量公司，等待估值回落" />
          </label>
          <div className="form-actions form-wide">
            <button className="primary-button" type="submit" disabled={saving}>{saving ? '保存中...' : '保存自选股'}</button>
            {error && <span className="form-error">{error}</span>}
          </div>
        </form>
      </Card>

      <Card>
        <div className="toolbar-row">
          <input className="search-input" value={keyword} onChange={(event) => setKeyword(event.target.value)} placeholder="搜索代码、名称、行业或理由" />
          <button className="ghost-button" onClick={load} type="button">刷新</button>
        </div>
        {loading ? (
          <LoadingState title="正在加载自选股" description="读取关注列表、分组和备注。" rows={3} />
        ) : filteredRows.length === 0 ? (
          <EmptyState title="暂无自选股" description="添加关注股票后，这里会展示分组、优先级和关注理由。" />
        ) : (
          <table className="data-table">
            <thead><tr><th>股票</th><th>分组</th><th>优先级</th><th>关注理由</th><th>状态</th><th>操作</th></tr></thead>
            <tbody>
              {filteredRows.map((row) => (
                <tr key={row.symbol}>
                  <td><strong>{row.name}</strong><br /><small>{row.symbol}</small></td>
                  <td>{row.group_name ?? '-'}</td>
                  <td>{row.priority ?? 0}</td>
                  <td>{row.reason ?? '-'}</td>
                  <td><Badge>{row.status ?? 'ACTIVE'}</Badge></td>
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
