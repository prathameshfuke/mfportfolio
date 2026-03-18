import { useMemo } from 'react'

export default function HealthScore({ score, summary }) {
  const normalized = Math.max(0, Math.min(100, score || 0))
  const radius = 70
  const circumference = 2 * Math.PI * radius
  const offset = circumference * (1 - normalized / 100)

  const color = useMemo(() => {
    if (normalized < 40) return 'rgba(255,255,255,0.45)'
    if (normalized < 70) return 'rgba(255,255,255,0.70)'
    return 'rgba(255,255,255,0.92)'
  }, [normalized])

  const band = useMemo(() => {
    if (normalized < 40) return 'At Risk'
    if (normalized < 70) return 'Needs Attention'
    return 'Healthy'
  }, [normalized])

  return (
    <div>
      <p className="kicker">Portfolio Health</p>
      <h2 className="section-title mt-2">Health Score</h2>
      <div className="relative mt-5 flex items-center justify-center">
        <svg width="190" height="190" viewBox="0 0 190 190" className="-rotate-90">
          <circle cx="95" cy="95" r={radius} stroke="rgba(255,255,255,0.12)" strokeWidth="14" fill="none" />
          <circle
            cx="95"
            cy="95"
            r={radius}
            stroke={color}
            strokeWidth="14"
            fill="none"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            style={{ transition: 'stroke-dashoffset 1s ease' }}
          />
        </svg>
        <div className="absolute text-center">
          <div className="font-heading text-4xl" style={{ color }}>
            {normalized}
          </div>
          <div className="text-xs text-warm/70">/ 100</div>
        </div>
      </div>
      <p className="mt-3 text-center text-xs uppercase tracking-[0.14em] text-warm/70">{band}</p>
      <p className="mt-4 text-sm text-warm/80">{summary}</p>
    </div>
  )
}
