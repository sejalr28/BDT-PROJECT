import { useEffect, useState } from 'react'
import { anomaliesApi } from '../services/api'

export default function Anomalies() {
  const [anomalies, setAnomalies] = useState([])
  const [loading, setLoading] = useState(true)
  const [minProb, setMinProb] = useState(0)

  useEffect(() => {
    setLoading(true)
    anomaliesApi
      .list({ limit: 200, min_probability: minProb || undefined })
      .then((res) => setAnomalies(res.data))
      .finally(() => setLoading(false))
  }, [minProb])

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Anomalies</h1>
          <div className="page-sub">Blocks flagged by the Random Forest classifier</div>
        </div>
      </div>

      <div className="filter-bar">
        <select value={minProb} onChange={(e) => setMinProb(Number(e.target.value))}>
          <option value={0}>Any confidence</option>
          <option value={0.5}>≥ 50% confidence</option>
          <option value={0.8}>≥ 80% confidence</option>
          <option value={0.95}>≥ 95% confidence</option>
        </select>
      </div>

      {loading ? (
        <div className="loading-state">Loading…</div>
      ) : (
        <div className="card" style={{ padding: 0 }}>
          <table>
            <thead>
              <tr>
                <th>Block ID</th>
                <th>Probability</th>
                <th>Predicted</th>
                <th>Ground truth</th>
                <th>Scored at</th>
              </tr>
            </thead>
            <tbody>
              {anomalies.map((a) => (
                <tr key={a.block_id}>
                  <td>{a.block_id}</td>
                  <td>
                    <span className={`badge ${a.probability_anomaly >= 0.8 ? 'critical' : 'warn'}`}>
                      {(a.probability_anomaly * 100).toFixed(1)}%
                    </span>
                  </td>
                  <td>{a.predicted_label === 1 ? 'Anomaly' : 'Normal'}</td>
                  <td>
                    {a.true_label === null ? (
                      '—'
                    ) : (
                      <span className={`badge ${a.true_label === 1 ? 'critical' : 'ok'}`}>
                        {a.true_label === 1 ? 'Anomaly' : 'Normal'}
                      </span>
                    )}
                  </td>
                  <td>{a.scored_at ? new Date(a.scored_at).toLocaleString() : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {anomalies.length === 0 && <div className="empty-state">No anomalies at this threshold</div>}
        </div>
      )}
    </>
  )
}