import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

const truncate = (name) => (name.length > 30 ? `${name.slice(0, 30)}...` : name)

export default function XirrChart({ funds, benchmarkXirr }) {
  const data = (funds || []).map((f) => ({
    name: truncate(f.fund_name || 'Unknown Fund'),
    xirr: f.xirr == null ? 0 : Number((f.xirr * 100).toFixed(2)),
    available: f.xirr != null,
  }))
  const chartHeight = Math.max(240, Math.min(460, data.length * 58 + 90))

  return (
    <div>
      <p className="kicker">Performance Lens</p>
      <h2 className="section-title mt-2">Fund-wise XIRR</h2>
      <div className="mt-4 w-full" style={{ height: chartHeight }}>
        <ResponsiveContainer>
          <BarChart data={data} layout="vertical" margin={{ top: 10, right: 30, left: 20, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
            <XAxis type="number" tick={{ fill: '#F8F9FA' }} unit="%" />
            <YAxis type="category" dataKey="name" width={220} tick={{ fill: '#F8F9FA', fontSize: 12 }} />
            <Tooltip
              contentStyle={{
                background: '#101A33',
                border: '1px solid rgba(255,255,255,0.15)',
                color: '#F8F9FA',
              }}
            />
            {benchmarkXirr != null && (
              <ReferenceLine
                x={benchmarkXirr * 100}
                stroke="#F59E0B"
                strokeDasharray="6 4"
                label={{ value: 'Benchmark', fill: '#F59E0B', position: 'top' }}
              />
            )}
            <Bar dataKey="xirr" fill="#00D4AA" radius={[0, 8, 8, 0]}>
              <LabelList
                dataKey="xirr"
                position="right"
                formatter={(v, row) => (row?.available ? `${v}%` : 'N/A')}
                fill="#F8F9FA"
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
