import { useState } from 'react'

const profiles = ['Conservative', 'Moderate', 'Aggressive']
const providers = ['Gemini', 'Anthropic']

export default function UploadZone({ onAnalyze, disabled }) {
  const [file, setFile] = useState(null)
  const [riskProfile, setRiskProfile] = useState('Moderate')
  const [provider, setProvider] = useState('Gemini')
  const [apiKey, setApiKey] = useState('')
  const [dragging, setDragging] = useState(false)

  return (
    <div>
      <p className="kicker">Portfolio In, Insight Out</p>
      <h2 className="section-title mt-2">Upload CAMS/KFintech Consolidated Statement</h2>
      <p className="mt-2 text-sm text-warm/70">
        Supports multi-fund CAS statements. Processing stays local to your runtime session.
      </p>

      <div
        className={`mt-4 rounded-2xl border-2 border-dashed p-8 text-center transition ${
          dragging
            ? 'border-teal bg-gradient-to-br from-teal/15 to-transparent'
            : 'border-white/20 bg-gradient-to-br from-white/5 to-transparent'
        }`}
        onDragOver={(e) => {
          e.preventDefault()
          setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragging(false)
          const dropped = e.dataTransfer.files?.[0]
          if (dropped) {
            setFile(dropped)
          }
        }}
      >
        <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full border border-teal/50 bg-teal/15 text-lg text-teal">
          PDF
        </div>
        <p className="text-warm/80">Drag and drop your statement here, or browse manually.</p>
        <input
          type="file"
          accept="application/pdf"
          className="mx-auto mt-4 block text-sm file:mr-4 file:rounded-lg file:border-0 file:bg-teal file:px-3 file:py-1 file:text-xs file:font-semibold file:text-bg hover:file:brightness-110"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
        />
        {file && <p className="mt-2 text-xs text-teal">Selected: {file.name}</p>}
      </div>

      <div className="mt-5">
        <p className="text-sm text-warm/80">Risk Profile</p>
        <div className="mt-2 flex flex-wrap gap-2">
          {profiles.map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => setRiskProfile(p)}
              className={`rounded-full px-4 py-2 text-sm transition ${
                riskProfile === p
                  ? 'bg-teal text-bg'
                  : 'border border-white/20 bg-transparent text-warm/80 hover:border-teal/50'
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      <div className="mt-5 rounded-xl border border-white/15 bg-white/5 p-4">
        <p className="text-xs uppercase tracking-[0.16em] text-warm/60">Optional AI API Key</p>
        <p className="mt-2 text-xs text-warm/60">Use your own key for AI advisor output. Leave empty to use server config.</p>

        <div className="mt-3 flex flex-wrap gap-2">
          {providers.map((p) => (
            <button
              key={p}
              type="button"
              onClick={() => setProvider(p)}
              className={`rounded-full px-3 py-1 text-xs transition ${
                provider === p
                  ? 'border border-white bg-white/90 text-neutral-900'
                  : 'border border-white/20 bg-transparent text-warm/70 hover:border-white/40'
              }`}
            >
              {p}
            </button>
          ))}
        </div>

        <input
          type="password"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder="Paste API key"
          className="mt-3 w-full rounded-lg border border-white/20 bg-neutral-900/60 px-3 py-2 text-sm text-white placeholder:text-neutral-500 focus:outline-none focus:border-neutral-500"
        />
      </div>

      <div className="mt-6 flex flex-wrap gap-3">
        <button
          type="button"
          disabled={disabled || !file}
          onClick={() =>
            file &&
            onAnalyze({
              file,
              riskProfile,
              apiProvider: provider.toLowerCase(),
              apiKey: apiKey.trim(),
            })
          }
          className="btn-primary"
        >
          Analyze Portfolio
        </button>
      </div>

      <p className="mt-4 text-xs text-warm/60">Your data is processed locally and not stored.</p>
    </div>
  )
}
