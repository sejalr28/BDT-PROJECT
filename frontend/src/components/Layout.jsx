import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

const NAV_ITEMS = [
  { to: '/', label: 'Overview', end: true },
  { to: '/search', label: 'Log Search' },
  { to: '/anomalies', label: 'Anomalies' },
  { to: '/alerts', label: 'Alerts' },
]

export default function Layout() {
  const { logout } = useAuth()

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand-mark">
            <span className="sidebar-brand-dot" />
            LogWatch
          </div>
          <span className="sidebar-brand-sub">HDFS incident console</span>
        </div>

        <nav>
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => 'nav-item' + (isActive ? ' active' : '')}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <button className="logout-btn" onClick={logout}>
            Sign out
          </button>
        </div>
      </aside>

      <main className="main">
        <Outlet />
      </main>
    </div>
  )
}