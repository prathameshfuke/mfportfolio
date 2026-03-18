import { Suspense, lazy, useMemo, useState } from 'react'
import FundTable from './components/FundTable'
import HealthScore from './components/HealthScore'
import UploadZone from './components/UploadZone'

const ExpenseDrag = lazy(() => import('./components/ExpenseDrag'))
const OverlapHeatmap = lazy(() => import('./components/OverlapHeatmap'))
const PortfolioSnapshot = lazy(() => import('./components/PortfolioSnapshot'))
const RebalancingPlan = lazy(() => import('./components/RebalancingPlan'))
const XirrChart = lazy(() => import('./components/XirrChart'))

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const steps = ['Parsing PDF...', 'Computing XIRR...', 'Enriching fund data...', 'Building advisor output...']

export default function App() {
  const [state, setState] = useState('landing')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [stepIdx, setStepIdx] = useState(0)

  const progressLabel = useMemo(() => steps[Math.min(stepIdx, steps.length - 1)], [stepIdx])

  const animateProgress = () => {
    setStepIdx(0)
    const timers = [
      setTimeout(() => setStepIdx(1), 700),
      setTimeout(() => setStepIdx(2), 1400),
      setTimeout(() => setStepIdx(3), 2200),
    ]
    return () => timers.forEach(clearTimeout)
  }

  const handleAnalyze = async ({ file, riskProfile, apiProvider, apiKey }) => {
    setState('uploading')
    setError('')
    const clearTimers = animateProgress()

    try {
      const fd = new FormData()
      fd.append('file', file)
      fd.append('risk_profile', riskProfile)
      if (apiProvider) fd.append('user_api_provider', apiProvider)
      if (apiKey) fd.append('user_api_key', apiKey)

      setState('analyzing')
      const response = await fetch(`${API_URL}/analyze`, {
        method: 'POST',
        body: fd,
      })

      const payload = await response.json()
      if (!response.ok) {
        throw new Error(payload?.detail || 'Analysis failed')
      }

      setResult(payload)
      setState('results')
    } catch (e) {
      setError(e.message || 'Something went wrong')
      setState('error')
    } finally {
      clearTimers()
    }
  }

  return (
    <main className="mx-auto max-w-7xl p-4 pb-10 md:p-8">
      <header className="hero-shell mb-8 animate-rise">
        <div className="relative z-10">
          <div className="mb-3 flex flex-wrap gap-2">
            <span className="pill">XIRR Intelligence</span>
            <span className="pill">Overlap Forensics</span>
            <span className="pill">AI Rebalancing</span>
          </div>
          <h1 className="font-heading text-4xl text-warm md:text-5xl">MF Portfolio X-Ray</h1>
          <p className="mt-3 max-w-3xl text-sm text-warm/80 md:text-base">
            Upload your CAMS or KFintech statement to decode true performance, expose hidden drag,
            and get a practical rebalancing path.
          </p>
        </div>
      </header>

      {state === 'landing' && (
        <section className="card animate-rise">
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
            <div>
              <p className="kicker">Portfolio Intelligence</p>
              <h2 className="mt-2 font-heading text-3xl font-light text-white md:text-4xl">See what your mutual fund statement is really saying.</h2>
              <p className="mt-4 max-w-xl text-sm text-neutral-300">
                Upload your consolidated statement and get reconstruction, true XIRR, overlap diagnostics,
                benchmark comparison, and AI advisory in one pass.
              </p>
              <button className="btn-primary mt-6" onClick={() => setState('idle')}>
                Get Started
              </button>
            </div>
            <div className="rounded-2xl border border-neutral-800/80 bg-neutral-900/60 p-5">
              <p className="text-xs uppercase tracking-[0.18em] text-neutral-500">What You Get</p>
              <ul className="mt-4 space-y-3 text-sm text-neutral-300">
                <li>1. Portfolio reconstruction by fund and value</li>
                <li>2. Fund-level and portfolio-level XIRR</li>
                <li>3. Overlap heatmap and diversification diagnostics</li>
                <li>4. Expense drag and benchmark performance gap</li>
                <li>5. AI rebalancing with your own API key option</li>
              </ul>
            </div>
          </div>
        </section>
      )}

      {(state === 'idle' || state === 'error') && (
        <section className="card animate-rise">
          <UploadZone onAnalyze={handleAnalyze} disabled={state !== 'idle'} />
          {state === 'error' && (
            <div className="mt-4 rounded-xl border border-danger/40 bg-danger/10 p-3 text-sm text-danger">
              {error}
              <button
                className="ml-3 rounded-md border border-danger/60 px-2 py-1 text-xs"
                onClick={() => {
                  setError('')
                  setState('idle')
                }}
              >
                Retry
              </button>
            </div>
          )}
        </section>
      )}

      {(state === 'uploading' || state === 'analyzing') && (
        <section className="card animate-rise text-center">
          <h2 className="section-title">Analyzing Portfolio</h2>
          <p className="mt-3 text-warm/80">{progressLabel}</p>
          <div className="mx-auto mt-6 h-2 w-full max-w-xl rounded-full bg-white/10">
            <div
              className="h-2 rounded-full bg-neutral-700 transition-all duration-500"
              style={{ width: `${(stepIdx + 1) * 25}%` }}
            />
          </div>
          <div className="mx-auto mt-5 grid max-w-xl grid-cols-2 gap-2 text-left text-xs text-warm/70 md:grid-cols-4">
            {steps.map((step, idx) => (
              <div
                key={step}
                className={`rounded-md border px-2 py-1 ${
                  idx <= stepIdx ? 'border-teal/50 bg-teal/10 text-teal' : 'border-white/10 bg-white/5'
                }`}
              >
                {step}
              </div>
            ))}
          </div>
        </section>
      )}

      {state === 'results' && result && (
        <Suspense
          fallback={
            <section className="card animate-rise text-center">
              <h2 className="section-title">Rendering Dashboard</h2>
              <p className="mt-3 text-warm/80">Loading visual components...</p>
            </section>
          }
        >
          <section className="grid grid-cols-1 items-start gap-5 md:grid-cols-2 xl:grid-cols-3">
            <div className="card md:col-span-2 xl:col-span-3">
              <PortfolioSnapshot result={result} />
            </div>
            <div className="card md:col-span-1">
              <HealthScore
                score={result.health_score}
                summary={
                  result.rebalancing_plan?.summary ||
                  'Portfolio analytics completed. Enable AI advisor to receive personalized rebalancing guidance.'
                }
              />
            </div>
            <div className="card md:col-span-1 xl:col-span-2">
              <FundTable funds={result.funds || []} benchmarkXirr={result.benchmark_xirr} />
            </div>
            <div className="card md:col-span-2 xl:col-span-2">
              <OverlapHeatmap funds={result.funds || []} pairs={result.overlap_pairs || []} />
            </div>
            <div className="card">
              <ExpenseDrag
                funds={result.funds || []}
                totalDrag={result.total_ter_drag_inr || 0}
                totalDragPct={result.total_ter_drag_pct || 0}
              />
            </div>
            <div className="card md:col-span-2 xl:col-span-2">
              <XirrChart funds={result.funds || []} benchmarkXirr={result.benchmark_xirr} />
            </div>
            <div className="card md:col-span-2 xl:col-span-3">
              <RebalancingPlan plan={result.rebalancing_plan} issues={result.issues || []} />
            </div>

            {(result.issues || []).length > 0 && (
              <div className="card md:col-span-2 xl:col-span-3">
                <h3 className="section-title">Data Warnings</h3>
                <ul className="mt-3 space-y-2 text-sm text-amber">
                  {(result.issues || []).map((issue, idx) => (
                    <li key={`${issue}-${idx}`}>• {issue}</li>
                  ))}
                </ul>
              </div>
            )}
          </section>
        </Suspense>
      )}
    </main>
  )
}
