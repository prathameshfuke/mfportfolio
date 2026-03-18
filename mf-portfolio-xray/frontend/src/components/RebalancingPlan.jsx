import { useState } from 'react'

const badgeClass = {
  high: 'bg-danger/20 text-danger border-danger/40',
  medium: 'bg-amber/20 text-amber border-amber/40',
  low: 'bg-teal/20 text-teal border-teal/40',
}

export default function RebalancingPlan({ plan, issues = [] }) {
  const [openCard, setOpenCard] = useState(null)
  const advisorIssues = plan?.issues || []
  const aiUnavailable = !plan

  return (
    <div>
      <p className="kicker">Advisor Layer</p>
      <h2 className="section-title mt-2">AI Rebalancing Plan</h2>
      <p className="mt-3 text-sm text-warm/80">
        {plan?.summary || 'Provide Gemini or Anthropic API key to enable AI recommendations. Analytics are still fully computed.'}
      </p>

      {aiUnavailable && (
        <div className="mt-4 rounded-lg border border-amber/40 bg-amber/10 p-3 text-sm text-amber">
          AI advisor is currently unavailable, so this panel shows fallback messaging only.
          {issues.length > 0 && <p className="mt-2 text-xs text-amber/90">Latest warning: {issues[0]}</p>}
        </div>
      )}

      <div className="mt-5 grid grid-cols-1 gap-4 xl:grid-cols-3">
        <div className="space-y-3 xl:col-span-2">
          <h3 className="font-heading text-lg">Issues</h3>
          {advisorIssues.length === 0 && (
            <div className="rounded-xl border border-white/15 bg-white/5 p-4 text-sm text-warm/70">
              No AI issues available yet.
            </div>
          )}
          {advisorIssues.map((issue, idx) => (
            <div key={`${issue.title}-${idx}`} className="rounded-xl border border-white/15 bg-white/5 p-3">
              <div className="flex items-center justify-between gap-2">
                <p className="font-semibold">{issue.title}</p>
                <span className={`rounded-full border px-2 py-0.5 text-xs ${badgeClass[issue.severity] || badgeClass.low}`}>
                  {issue.severity}
                </span>
              </div>
              <p className="mt-2 text-sm text-warm/80">{issue.explanation}</p>
              <button
                className="mt-2 rounded-md border border-teal/50 bg-teal/10 px-3 py-1 text-xs text-teal"
                onClick={() => setOpenCard(openCard === idx ? null : idx)}
              >
                {openCard === idx ? 'Hide action' : 'Show action'}
              </button>
              {openCard === idx && <p className="mt-2 text-sm text-teal">{issue.action}</p>}
            </div>
          ))}
        </div>

        <div className="space-y-4 xl:col-span-1">
          <div className="rounded-xl border border-white/15 bg-white/5 p-4">
            <h3 className="font-heading text-lg">Rebalancing Steps</h3>
            <ol className="mt-2 space-y-2 text-sm text-warm/85">
              {(plan?.rebalancing_steps || ['Enable AI advisor to generate personalized steps.']).map((step, idx) => (
                <li key={`${step}-${idx}`}>
                  {idx + 1}. {step}
                </li>
              ))}
            </ol>
          </div>

          <div className="rounded-lg border border-amber/40 bg-amber/10 p-3 text-sm text-amber">
            <p className="font-semibold">Tax Notes</p>
            <p className="mt-1">{plan?.tax_notes || 'No immediate tax impact'}</p>
          </div>
        </div>
      </div>

      <p className="mt-4 text-xs text-warm/55">
        AI-generated advice. Not SEBI-registered financial advice. Consult a financial advisor before making
        investment decisions.
      </p>
    </div>
  )
}
