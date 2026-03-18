import { useMemo, useState } from 'react'

const columns = [
  { key: 'fund_name', label: 'Fund Name' },
  { key: 'category', label: 'Category' },
  { key: 'current_value', label: 'Value' },
  { key: 'weight', label: 'Weight%' },
  { key: 'xirr', label: 'XIRR%' },
  { key: 'ter_pct', label: 'TER%' },
  { key: 'annual_drag_inr', label: 'Annual Drag' },
]

function cmp(a, b, key) {
  const va = a[key] ?? -Infinity
  const vb = b[key] ?? -Infinity
  if (typeof va === 'string') return va.localeCompare(vb)
  return va - vb
}

export default function FundTable({ funds, benchmarkXirr }) {
  const [sortBy, setSortBy] = useState('current_value')
  const [sortDir, setSortDir] = useState('desc')

  const total = useMemo(() => funds.reduce((s, f) => s + (f.current_value || 0), 0), [funds])

  const rows = useMemo(() => {
    const withWeight = funds.map((f) => ({
      ...f,
      weight: total > 0 ? ((f.current_value || 0) / total) * 100 : 0,
    }))
    return withWeight.sort((a, b) => {
      const base = cmp(a, b, sortBy)
      return sortDir === 'asc' ? base : -base
    })
  }, [funds, sortBy, sortDir, total])

  const invested = useMemo(() => funds.reduce((s, f) => s + (f.invested_amount || 0), 0), [funds])
  const gain = total - invested
  const gainPct = invested > 0 ? (gain / invested) * 100 : 0
  const avgTer = useMemo(
    () => (funds.length > 0 ? funds.reduce((s, f) => s + Number(f.ter_pct || 0), 0) / funds.length : 0),
    [funds],
  )

  const toggleSort = (key) => {
    if (sortBy === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
      return
    }
    setSortBy(key)
    setSortDir('desc')
  }

  return (
    <div>
      <p className="kicker">Portfolio Reconstruction</p>
      <h2 className="section-title mt-2">Fund Breakdown</h2>
      <div className="mt-3 grid grid-cols-2 gap-2 text-xs md:grid-cols-4">
        <div className="rounded-lg border border-white/10 bg-white/5 px-3 py-2">
          <p className="text-warm/60">Funds</p>
          <p className="mt-1 font-heading text-lg">{funds.length}</p>
        </div>
        <div className="rounded-lg border border-white/10 bg-white/5 px-3 py-2">
          <p className="text-warm/60">Current Value</p>
          <p className="mt-1 font-heading text-lg">INR {total.toLocaleString()}</p>
        </div>
        <div className="rounded-lg border border-white/10 bg-white/5 px-3 py-2">
          <p className="text-warm/60">Gain/Loss</p>
          <p className={`mt-1 font-heading text-lg ${gain >= 0 ? 'text-teal' : 'text-danger'}`}>
            {gain >= 0 ? '+' : ''}INR {gain.toLocaleString()}
          </p>
          <p className="text-[11px] text-warm/55">{gainPct.toFixed(2)}%</p>
        </div>
        <div className="rounded-lg border border-white/10 bg-white/5 px-3 py-2">
          <p className="text-warm/60">Avg TER</p>
          <p className="mt-1 font-heading text-lg text-amber">{avgTer.toFixed(2)}%</p>
        </div>
      </div>
      <div className="mt-4 max-h-[420px] overflow-auto rounded-xl border border-white/10">
        <table className="w-full min-w-[900px] text-sm">
          <thead>
            <tr className="sticky top-0 z-10 border-b border-white/15 bg-card text-left text-warm/70">
              {columns.map((c) => (
                <th
                  key={c.key}
                  className="cursor-pointer px-2 py-2 font-medium hover:text-teal"
                  onClick={() => toggleSort(c.key)}
                >
                  {c.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((f) => {
              const xirrPct = f.xirr == null ? null : f.xirr * 100
              const spread = benchmarkXirr == null || xirrPct == null ? null : xirrPct - benchmarkXirr * 100
              const xirrColor =
                xirrPct == null
                  ? 'text-warm/70'
                  : benchmarkXirr != null && xirrPct < benchmarkXirr * 100
                    ? 'text-danger'
                    : 'text-teal'

              return (
                <tr key={`${f.fund_name}-${f.scheme_code || 'na'}`} className="border-b border-white/10">
                  <td className="px-2 py-2">{f.fund_name}</td>
                  <td className="px-2 py-2 text-warm/80">{f.category || 'Unknown'}</td>
                  <td className="px-2 py-2">INR {Number(f.current_value || 0).toLocaleString()}</td>
                  <td className="px-2 py-2">{f.weight.toFixed(2)}%</td>
                  <td className={`px-2 py-2 font-semibold ${xirrColor}`}>
                    {xirrPct == null ? 'N/A' : `${xirrPct.toFixed(2)}%`}
                    {spread != null && (
                      <span className={`ml-2 text-xs ${spread >= 0 ? 'text-teal/80' : 'text-danger/80'}`}>
                        ({spread >= 0 ? '+' : ''}
                        {spread.toFixed(2)}%)
                      </span>
                    )}
                  </td>
                  <td className="px-2 py-2">{Number(f.ter_pct || 0).toFixed(2)}%</td>
                  <td className="px-2 py-2 text-amber">INR {Number(f.annual_drag_inr || 0).toLocaleString()}</td>
                </tr>
              )
            })}

            <tr className="bg-white/5 font-semibold">
              <td className="px-2 py-2">Benchmark Reference</td>
              <td className="px-2 py-2" colSpan={3}>
                Nifty 50 XIRR
              </td>
              <td className="px-2 py-2 text-amber">
                {benchmarkXirr == null ? 'N/A' : `${(benchmarkXirr * 100).toFixed(2)}%`}
              </td>
              <td className="px-2 py-2" colSpan={2} />
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  )
}
