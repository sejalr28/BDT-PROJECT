import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'
import Login from './pages/Login'
import Overview from './pages/Overview'
import LogSearch from './pages/LogSearch'
import Anomalies from './pages/Anomalies'
import Alerts from './pages/Alerts'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Overview />} />
            <Route path="search" element={<LogSearch />} />
            <Route path="anomalies" element={<Anomalies />} />
            <Route path="alerts" element={<Alerts />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}