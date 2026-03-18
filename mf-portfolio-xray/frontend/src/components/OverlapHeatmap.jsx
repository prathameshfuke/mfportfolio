const getColor = (pct) => {
  if (pct > 50) return 'bg-neutral-500 text-neutral-950'
  if (pct >= 20) return 'bg-neutral-700 text-white'
  return 'bg-neutral-800 text-neutral-200'
}

export default function OverlapHeatmap({ funds, pairs }) {
  const fundNames = (funds || []).map((f) => f.fund_name)
  const keyFor = (a, b) => [a, b].sort().join('||')
  const pairMap = new Map((pairs || []).map((p) => [keyFor(p.fund_a, p.fund_b), Number(p.overlap_pct || 0)]))

  if ((funds || []).length <= 1) {
    return (
      <div>
        <p className="kicker">Diversification Lens</p>
        <h2 className="section-title mt-2">Fund Overlap Heatmap</h2>
        <p className="mt-4 text-sm text-warm/70">Add more funds to see overlap analysis.</p>
      </div>
    )
  }

  if (!pairs || pairs.length === 0) {
    return (
      <div>
        <p className="kicker">Diversification Lens</p>
        <h2 className="section-title mt-2">Fund Overlap Heatmap</h2>
        <p className="mt-4 text-sm text-neutral-300">Holdings data unavailable for overlap analysis.</p>
      </div>
    )
  }

  return (
    <div>
      <p className="kicker">Diversification Lens</p>
      <h2 className="section-title mt-2">Fund Overlap Heatmap</h2>
      <div className="mt-4 overflow-auto rounded-xl border border-white/10 p-2">
        <div
          className="grid min-w-[680px] gap-2"
          style={{ gridTemplateColumns: `180px repeat(${fundNames.length}, minmax(120px, 1fr))` }}
        >
          <div className="px-2 py-2 text-xs uppercase tracking-[0.14em] text-warm/60">Fund</div>
          {fundNames.map((name) => (
            <div key={`head-${name}`} className="truncate px-2 py-2 text-xs text-warm/70" title={name}>
              {name}
            </div>
          ))}

          {fundNames.map((rowFund) => (
            <div
              key={`row-wrap-${rowFund}`}
              className="contents"
            >
              <div key={`row-${rowFund}`} className="truncate px-2 py-2 text-xs text-warm/70" title={rowFund}>
                {rowFund}
              </div>
              {fundNames.map((colFund) => {
                if (rowFund === colFund) {
                  return (
                    <div
                      key={`${rowFund}-${colFund}`}
                      className="rounded-lg border border-white/10 bg-white/5 px-2 py-3 text-center text-xs text-warm/60"
                    >
                      --
                    </div>
                  )
                }

                const pct = pairMap.get(keyFor(rowFund, colFund)) ?? 0
                return (
                  <div
                    key={`${rowFund}-${colFund}`}
                    title={`${pct.toFixed(2)}% overlap`}
                    className={`rounded-lg border border-white/10 px-2 py-3 text-center text-sm font-semibold ${getColor(pct)}`}
                  >
                    {pct.toFixed(1)}%
                  </div>
                )
              })}
            </div>
          ))}
        </div>
      </div>
      <p className="mt-3 text-xs text-neutral-500">Legend: darker means lower overlap, lighter means higher overlap.</p>
    </div>
  )
}
