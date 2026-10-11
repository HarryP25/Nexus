const API_BASE_URL = ''
let initialSessionRequest

const apiFetch = (url, options = {}, csrfToken = '') => {
  const headers = new Headers(options.headers || {})
  const method = (options.method || 'GET').toUpperCase()
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method) && csrfToken) {
    headers.set('X-CSRF-Token', csrfToken)
  }

  return fetch(url, { ...options, headers, credentials: 'include' })
}

const readApiResponse = async (response) => {
  const contentType = response.headers.get('content-type') || ''
  if (contentType.includes('application/json')) {
    return response.json()
  }
  const message = await response.text()
  return {
    message: contentType.includes('text/html')
      ? 'The backend endpoint was not found. Restart the Python backend and try again.'
      : message,
  }
}

const getApiSession = () => {
  if (!initialSessionRequest) {
    initialSessionRequest = apiFetch(`${API_BASE_URL}/api/session`)
      .then(async (response) => ({ response, data: await readApiResponse(response) }))
      .catch((error) => {
        initialSessionRequest = null
        throw error
      })
  }
  return initialSessionRequest
}

export { API_BASE_URL, apiFetch, getApiSession, readApiResponse }
