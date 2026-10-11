import { useCallback, useEffect, useState } from 'react'
import LandingView from './components/LandingView.jsx'
import DashboardView from './components/DashboardView.jsx'
import { API_BASE_URL, apiFetch, getApiSession, readApiResponse } from './lib/appHelpers.js'

function App() {
  const [view, setView] = useState('landing')
  const [currentUser, setCurrentUser] = useState(null)
  const [csrfToken, setCsrfToken] = useState('')
  const [sessionLoading, setSessionLoading] = useState(true)
  const [mode, setMode] = useState('signin')
  const [showAuth, setShowAuth] = useState(false)
  const [message, setMessage] = useState('')
  const [messageType, setMessageType] = useState('error')
  const [showSignupSuccess, setShowSignupSuccess] = useState(false)
  const [createdUsername, setCreatedUsername] = useState('')

  useEffect(() => {
    let isCurrent = true

    const restoreSession = async () => {
      try {
        const { response, data } = await getApiSession()
        if (!response.ok) throw new Error(data.message || 'Unable to restore your session.')
        if (!isCurrent) return

        setCsrfToken(data.csrfToken || '')
        setCurrentUser(data.user || null)
        setView(data.authenticated ? 'dashboard' : 'landing')
      } catch {
        if (isCurrent) {
          setCurrentUser(null)
          setView('landing')
          setMessage('Unable to connect to the Nexus API. Please start the backend and try again.')
        }
      } finally {
        if (isCurrent) setSessionLoading(false)
      }
    }

    restoreSession()
    return () => { isCurrent = false }
  }, [])

  const openAuth = (nextMode) => {
    setMode(nextMode)
    setShowAuth(true)
    setView('landing')
    setMessage('')
    setMessageType('error')
    setShowSignupSuccess(false)
  }

  const closeAuth = () => {
    setShowAuth(false)
    setMessage('')
    setMessageType('error')
    setShowSignupSuccess(false)
  }

  const handleLogout = async () => {
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/logout`, {
        method: 'POST',
      }, csrfToken)
      const data = await readApiResponse(response)
      if (!response.ok) {
        if (response.status === 401 || response.status === 403) {
          await handleSessionExpired()
          return false
        }
        throw new Error(data.message || 'Unable to sign out.')
      }

      setCsrfToken(data.csrfToken || '')
      setCurrentUser(null)
      setView('landing')
      setShowAuth(false)
      setMessage('')
      setMessageType('error')
      setShowSignupSuccess(false)
      return true
    } catch {
      return false
    }
  }

  const handleSessionExpired = useCallback(async () => {
    try {
      const response = await apiFetch(`${API_BASE_URL}/api/session`)
      const data = await readApiResponse(response)
      if (!response.ok) return
      setCsrfToken(data.csrfToken || '')
      setCurrentUser(data.user || null)
      setView(data.authenticated ? 'dashboard' : 'landing')
      if (!data.authenticated) {
        setMessage('Your session expired. Please sign in again.')
        setMessageType('error')
      }
    } catch {
      setMessage('Unable to refresh your session. Please check your connection and try again.')
      setMessageType('error')
    }
  }, [])

  const handleAuthSubmit = async (event) => {
    event.preventDefault()
    const form = event.currentTarget
    const username = form.elements.username.value.trim()
    const password = form.elements.password.value.trim()

    if (!username || !password) {
      setMessage('Please enter both a username and password.')
      setMessageType('error')
      return
    }

    const endpoint = mode === 'signup' ? '/api/signup' : '/api/login'
    try {
      const response = await apiFetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      }, csrfToken)
      const data = await readApiResponse(response)

      if (!response.ok) {
        setMessage(data.message || (mode === 'signup' ? 'Unable to create account right now.' : 'Unable to sign in right now.'))
        setMessageType('error')
        return
      }

      if (mode === 'signup') {
        setMode('signin')
        setCreatedUsername(data.username || username)
        setShowSignupSuccess(true)
        form.reset()
        return
      }

      setCsrfToken(data.csrfToken || '')
      setCurrentUser({ uniqueID: data.uniqueID, username: data.username })
      setMessage('')
      setMessageType('error')
      setShowAuth(false)
      setView('dashboard')
    } catch {
      setMessage('Unable to connect to the Nexus API. Please start the backend and try again.')
      setMessageType('error')
    }
  }

  const signInWithNewAccount = () => {
    setShowSignupSuccess(false)
    setCreatedUsername('')
    setMode('signin')
    setMessage('')
    setMessageType('error')
  }

  if (sessionLoading) return null

  return view === 'dashboard' ? (
    <DashboardView
      currentUser={currentUser}
      csrfToken={csrfToken}
      onLogout={handleLogout}
      onSessionExpired={handleSessionExpired}
    />
  ) : (
    <LandingView
      mode={mode}
      showAuth={showAuth}
      message={message}
      messageType={messageType}
      showSignupSuccess={showSignupSuccess}
      createdUsername={createdUsername}
      onOpenAuth={openAuth}
      onCloseAuth={closeAuth}
      onDismissMessage={() => setMessage('')}
      onSignInNow={signInWithNewAccount}
      onEnterDashboard={handleAuthSubmit}
    />
  )
}

export default App
