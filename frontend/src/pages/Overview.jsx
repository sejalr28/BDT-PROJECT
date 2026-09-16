import { useEffect, useState } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid,
  PieChart, Pie, Cell,
} from 'recharts'
import { statsApi, anomaliesApi } from '../services/api'

const PIE_COLORS = ['#4fd1c5', '#e8a94f', '#f0546b', '#5fb87a', '#8b949e']

export default function Overview() {
  const [overview, setOverview] = useState(null)
  const [topEvents, setTopEvents] = useState([])
  const [anomalyCount, setAnomalyCount] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false

    async function load() {
      try {
        const [ov, events, anomalies] = await Promise.all([
          statsApi.overview(),
          statsApi.topEventTypes(8),
          anomaliesApi.list({ limit: 500 }),
        ])
        if (cancelled) return
        setOverview(ov.data)
        setTopEvents(events.data)
        setAnomalyCount(anomalies.data.length)
      } catch (err) {
        if (!cancelled) setError('Could not load stats — is Elasticsearch running?')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => { cancelled = true }
  }, [])

  if (loading) return <div className="loading-state">Loading overview…</div>
  if (error) return <div className="auth-error" style={{ maxWidth: 480 }}>{error}</div>

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Overview</h1>
          <div className="page-sub">Live snapshot of the parsed log stream</div>
        </div>
      </div>

      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-label">Total log lines</div>
          <div className="stat-value accent">{overview.total_log_lines.toLocaleString()}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Predicted anomalies</div>
          <div className="stat-value critical">{anomalyCount?.toLocaleString() ?? '—'}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Event templates seen</div>
          <div className="stat-value">{topEvents.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Log levels</div>
          <div className="stat-value ok">{overview.level_breakdown.length}</div>
        </div>
      </div>

      <div className="chart-grid">
        <div className="card">
          <h3>Top event templates</h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={topEvents} layout="vertical" margin={{ left: 10 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#232938" horizontal={false} />
              <XAxis type="number" stroke="#7c8494" fontSize={11} />
              <YAxis
                type="category"
                dataKey="event_id"
                stroke="#7c8494"
                fontSize={11}
                width={40}
              />
              <Tooltip
                contentStyle={{ background: '#161b26', border: '1px solid #232938', fontSize: 12 }}
                cursor={{ fill: 'rgba(255,255,255,0.03)' }}
              />
              <Bar dataKey="count" fill="#4fd1c5" radius={[0, 2, 2, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3>Log level breakdown</h3>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={overview.level_breakdown}
                dataKey="count"
                nameKey="level"
                innerRadius={55}
                outerRadius={90}
                paddingAngle={2}
              >
                {overview.level_breakdown.map((entry, i) => (
                  <Cell key={entry.level} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ background: '#161b26', border: '1px solid #232938', fontSize: 12 }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </>
  )
}