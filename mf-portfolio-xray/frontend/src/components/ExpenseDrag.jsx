import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'

const COLORS = ['#f5f5f5', '#d4d4d4', '#a3a3a3', '#737373', '#525252', '#404040']

export default function ExpenseDrag({ funds, totalDrag, totalDragPct }) {
  const data = (funds || []).map((f) => ({
    name: f.fund_name,
    value: Number(f.annual_drag_inr || 0),
    ter: Number(f.ter_pct || 0),
  }))

  return (
    <div>
      <p className="kicker">Cost Leak Detector</p>
      <h2 className="section-title mt-2">Expense Ratio Drag</h2>
      <div className="mt-4 h-[240px]">
        <ResponsiveContainer>
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              innerRadius={60}
              outerRadius={88}
              paddingAngle={2}
            >
              {data.map((_, idx) => (
                <Cell key={idx} fill={COLORS[idx % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value) => `INR ${Number(value).toLocaleString()}`}
              contentStyle={{
                background: '#101A33',
                border: '1px solid rgba(255,255,255,0.15)',
                color: '#F8F9FA',
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <p className="-mt-1 text-center text-sm text-amber">
        INR {Number(totalDrag || 0).toLocaleString()} lost annually to fees ({totalDragPct?.toFixed(2)}%)
      </p>
      <ul className="mt-4 space-y-2 text-sm">
        {data.map((f, idx) => (
          <li key={idx} className="flex items-center justify-between rounded-lg bg-white/5 px-3 py-2">
            <span className="max-w-[65%] truncate">{f.name}</span>
            <span className="text-right text-warm/80">
              {f.ter.toFixed(2)}% | INR {f.value.toLocaleString()}
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
