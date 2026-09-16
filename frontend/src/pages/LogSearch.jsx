import { useState } from 'react'
import { logsApi } from '../services/api'

export default function LogSearch() {
  const [query, setQuery] = useState('')
  const [level, setLevel] = useState('')
  const [eventId, setEventId] = useState('')
  const [results, setResults] = useState([])
  const [total, setTotal] = useState(null)
  const [loading, setLoading] = useState(false)

  const search = async (e) => {
    e?.preventDefault()
    setLoading(true)
    try {
      const res = await logsApi.search({
        q: query || undefined,
        level: level || undefined,
        event_id: eventId || undefined,
        page_size: 50,
      })
      setResults(res.data.results)
      setTotal(res.data.total)
    } finally {
      setLoading(false)
    }
  }

  return (
    <>
      <div className="page-header">
        <div>
          <h1 className="page-title">Log Search</h1>
          <div className="page-sub">Query parsed log lines in Elasticsearch</div>
        </div>
      </div>

      <form className="filter-bar" onSubmit={search}>
        <input
          placeholder="Search content…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          style={{ minWidth: 220 }}
        />
        <select value={level} onChange={(e) => setLevel(e.target.value)}>
          <option value="">All levels</option>
          <option value="INFO">INFO</option>
          <option value="WARN">WARN</option>
          <option value="ERROR">ERROR</option>
        </select>
        <input
          placeholder="Event ID (e.g. E20)"
          value={eventId}
          onChange={(e) => setEventId(e.target.value)}
          style={{ width: 160 }}
        />
        <button className="btn" type="submit">Search</button>
      </form>

      {loading && <div className="loading-state">Searching…</div>}

      {!loading && total !== null && (
        <div className="card" style={{ padding: 0 }}>
          <table>
            <thead>
              <tr>
                <th>Level</th>
                <th>Component</th>
                <th>Event</th>
                <th>Block ID</th>
                <th>Content</th>
              </tr>
            </thead>
            <tbody>
              {results.map((r, i) => (
                <tr key={i}>
                  <td>
                    <span className={`badge ${r.level === 'ERROR' ? 'critical' : r.level === 'WARN' ? 'warn' : 'ok'}`}>
                      {r.level}
                    </span>
                  </td>
                  <td>{r.component}</td>
                  <td>{r.event_id}</td>
                  <td>{r.block_id || '—'}</td>
                  <td style={{ maxWidth: 400, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {r.content}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {results.length === 0 && <div className="empty-state">No matching log lines</div>}
        </div>
      )}
    </>
  )
}