import { createContext, useContext, useState } from 'react'
import { authApi } from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('token'))

  const login = async (username, password) => {
    const res = await authApi.login(username, password)
    localStorage.setItem('token', res.data.access_token)
    setToken(res.data.access_token)
  }

  const register = async (username, password) => {
    await authApi.register(username, password)
    await login(username, password)
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
  }

  return (
    <AuthContext.Provider value={{ token, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}