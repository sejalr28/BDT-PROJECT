import { useEffect, useState } from 'react'
import { alertsApi } from '../services/api'

export default function Alerts() {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [form, setForm] = useState({
    name: '',
    condition_field: 'level',
    condition_value: 'ERROR',
    threshold_count: 5,
    lookback_minutes: 60,
  })

  const load = () => {
    setLoading(true)
    alertsApi.list().then((res) => setAlerts(res.data)).finally(() => setLoading(false))
  }

  useEffect(load, [])

  const handleCreate = async (e) => {
    e.preventDefault()
    await alertsApi.create(form)
    setForm({ ...form, name: '' })
    load()
  }

  const handleDelete = async (id) => {
    await alertsApi.remove(id)
    load()
  }

  const handleToggle = async (id) => {
    await alertsApi.toggle(id)
    load()
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Alerts</h1>
          <div className="page-sub">Rules that watch the log stream for you</div>
        </div>
      </div>

      <div className="chart-grid" style={{ gridTemplateColumns: '1fr 1.4fr' }}>
        <div className="card">
          <h3 style={{ marginTop: 0 }}>New alert rule</h3>
          <form onSubmit={handleCreate}>
            <div className="field">
              <label>Name</label>
              <input
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                required
              />
            </div>
            <div className="field">
              <label>Watch field</label>
              <select
                value={form.condition_field}
                onChange={(e) => setForm({ ...form, condition_field: e.target.value })}
              >
                <option value="level">Log level</option>
                <option value="event_id">Event type</option>
              </select>
            </div>
            <div className="field">
              <label>Value to match</label>
              <input
                value={form.condition_value}
                onChange={(e) => setForm({ ...form, condition_value: e.target.value })}
                placeholder="e.g. ERROR or E20"
                required
              />
            </div>
            <div className="field">
              <label>Trigger threshold (count)</label>
              <input
                type="number"
                min={1}
                value={form.threshold_count}
                onChange={(e) => setForm({ ...form, threshold_count: Number(e.target.value) })}
              />
            </div>
            <div className="field">
              <label>Lookback window (minutes)</label>
              <input
                type="number"
                min={1}
                value={form.lookback_minutes}
                onChange={(e) => setForm({ ...form, lookback_minutes: Number(e.target.value) })}
              />
            </div>
            <button className="btn" type="submit">Create alert</button>
          </form>
        </div>

        <div className="card" style={{ padding: 0 }}>
          {loading ? (
            <div className="loading-state" style={{ padding: 20 }}>Loading…</div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Condition</th>
                  <th>Threshold</th>
                  <th>Status</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {alerts.map((a) => (
                  <tr key={a.id}>
                    <td>{a.name}</td>
                    <td>{a.condition_field} = {a.condition_value}</td>
                    <td>{a.threshold_count} in {a.lookback_minutes}m</td>
                    <td>
                      <span className={`badge ${a.is_active ? 'ok' : 'warn'}`}>
                        {a.is_active ? 'Active' : 'Paused'}
                      </span>
                    </td>
                    <td style={{ display: 'flex', gap: 8 }}>
                      <button className="btn secondary" onClick={() => handleToggle(a.id)}>
                        {a.is_active ? 'Pause' : 'Resume'}
                      </button>
                      <button className="btn danger" onClick={() => handleDelete(a.id)}>
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {!loading && alerts.length === 0 && (
            <div className="empty-state">No alert rules yet — create one on the left</div>
          )}
        </div>
      </div>
    </>
  )
}