const formatInr = (value) => `INR ${Number(value || 0).toLocaleString()}`

function MetricCard({ title, value, tone = 'teal', subtext }) {
  const toneClass = {
    teal: 'border-neutral-700 bg-neutral-900/50 text-white',
    amber: 'border-neutral-700 bg-neutral-900/50 text-white',
    red: 'border-neutral-700 bg-neutral-900/50 text-white',
    warm: 'border-white/20 bg-white/5 text-warm',
  }

  return (
    <div className={`rounded-xl border p-3 ${toneClass[tone] || toneClass.warm}`}>
      <p className="text-[11px] uppercase tracking-[0.16em] text-warm/70">{title}</p>
      <p className="mt-2 font-heading text-2xl leading-none">{value}</p>
      {subtext && <p className="mt-2 text-xs text-warm/70">{subtext}</p>}
    </div>
  )
}

export default function PortfolioSnapshot({ result }) {
  const totalInvested = Number(result?.total_invested || 0)
  const currentValue = Number(result?.current_value || 0)
  const gain = currentValue - totalInvested
  const gainPct = totalInvested > 0 ? (gain / totalInvested) * 100 : 0
  const overallXirrPct = result?.overall_xirr == null ? null : result.overall_xirr * 100
  const benchmarkPct = result?.benchmark_xirr == null ? null : result.benchmark_xirr * 100
  const alpha = overallXirrPct != null && benchmarkPct != null ? overallXirrPct - benchmarkPct : null

  return (
    <div>
      <p className="kicker">Portfolio Snapshot</p>
      <h2 className="section-title mt-2">At-a-glance Metrics</h2>
      <div className="mt-4 grid grid-cols-2 gap-3 xl:grid-cols-5">
        <MetricCard title="Invested" value={formatInr(totalInvested)} tone="warm" />
        <MetricCard title="Current Value" value={formatInr(currentValue)} tone="teal" />
        <MetricCard
          title="Unrealized Gain"
          value={`${formatInr(gain)}`}
          tone={gain >= 0 ? 'teal' : 'red'}
          subtext={`${gainPct.toFixed(2)}% vs invested`}
        />
        <MetricCard
          title="Portfolio XIRR"
          value={overallXirrPct == null ? 'N/A' : `${overallXirrPct.toFixed(2)}%`}
          tone="warm"
        />
        <MetricCard
          title="Alpha vs Nifty"
          value={alpha == null ? 'N/A' : `${alpha >= 0 ? '+' : ''}${alpha.toFixed(2)}%`}
          tone={alpha == null ? 'warm' : alpha >= 0 ? 'teal' : 'amber'}
          subtext={benchmarkPct == null ? 'Benchmark unavailable' : `Nifty XIRR ${benchmarkPct.toFixed(2)}%`}
        />
      </div>
    </div>
  )
}
