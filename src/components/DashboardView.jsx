import { useCallback, useEffect, useState } from 'react'
import NexusLogo from './Brand.jsx'
import ConnectionCatalog from './ConnectionCatalog.jsx'
import DatasourceConfigurationForm from './DatasourceConfigurationForm.jsx'
import DashboardInsights from './DashboardInsights.jsx'
import { API_BASE_URL, apiFetch, readApiResponse } from '../lib/appHelpers.js'
import { getProviderLogo } from '../lib/providerLogos.js'
import solarWindsLogo from '../assets/integrations/solarwinds.png'
import catoLogo from '../assets/integrations/cato.png'
import site24x7Logo from '../assets/integrations/site24x7.png'
import microsoftSqlServerLogo from '../assets/integrations/microsoft-sql-server.png'
import mysqlLogo from '../assets/integrations/mysql.svg'
import postgresqlLogo from '../assets/integrations/postgresql.svg'
import prometheusLogo from '../assets/integrations/prometheus.svg'
import grafanaLogo from '../assets/integrations/grafana.svg'
import cloudWatchLogo from '../assets/integrations/cloudwatch.svg'
import '../App.css'

function DashboardView({ currentUser, csrfToken, onLogout, onSessionExpired }) {
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [connectionsOpen, setConnectionsOpen] = useState(false)
  const [showConnectionForm, setShowConnectionForm] = useState(false)
  const [showDatasources, setShowDatasources] = useState(false)
  const [analysisData, setAnalysisData] = useState(null)
  const [analysisLoadingId, setAnalysisLoadingId] = useState(null)
  const [selectedDatasource, setSelectedDatasource] = useState(null)
  const [connectionStatus, setConnectionStatus] = useState(null)
  const [connectionSearch, setConnectionSearch] = useState('')
  const [profileOpen, setProfileOpen] = useState(false)
  const [accountOpen, setAccountOpen] = useState(false)
  const [logoutLoading, setLogoutLoading] = useState(false)
  const [profileMessage, setProfileMessage] = useState('')
  const [showDateRangePicker, setShowDateRangePicker] = useState(false)
  const [dateRange, setDateRange] = useState(null)
  const [dateRangeDraft, setDateRangeDraft] = useState({ start: '', end: '' })
  const [dateRangeError, setDateRangeError] = useState('')
  const [overviewData, setOverviewData] = useState(null)
  const [overviewLoading, setOverviewLoading] = useState(true)
  const [overviewError, setOverviewError] = useState('')
  const [savedDatasources, setSavedDatasources] = useState([])

  const username = currentUser.username || 'Nexus'
  const userInitial = username.charAt(0).toUpperCase()

  const requestApi = useCallback(async (...args) => {
    const response = await apiFetch(...args)
    if (response.status === 401 || response.status === 403) {
      onSessionExpired()
    }
    return response
  }, [onSessionExpired])

  const datasourceCards = [
    {
      name: 'SolarWinds SWIS API',
      logoUrl: solarWindsLogo,
      authType: 'basic',
      description: 'Connect to the SolarWinds Information Service (SWIS) API.',
      endpointLabel: 'Server URL',
      endpointPlaceholder: 'https://solarwinds.example.com',
      endpointHint: 'Enter only the scheme and host. Nexus uses the SWIS API on port 17774 automatically.',
    },
    {
      name: 'Cato',
      logoUrl: catoLogo,
      authType: 'cato',
      description: 'Connect to your Cato SASE account with your API URL, API key, account ID, and site IDs.',
      endpointLabel: 'API URL',
      endpointPlaceholder: 'https://api.catonetworks.com/api/v1/graphql2',
      endpointHint: 'Use the Cato API endpoint for your account and a read-only API key where possible.',
    },
    {
      name: 'Site24x7',
      logoUrl: site24x7Logo,
      authType: 'site24x7',
      description: 'Use the prefilled demo values for testing, or enter your Site24x7 OAuth access token.',
      endpointLabel: 'API URL',
      endpointPlaceholder: 'https://www.site24x7.com/api',
      endpointHint: 'Demo analysis reads seeded measurements from the Nexus database; no external Site24x7 request is made.',
    },
    {
      name: 'Microsoft SQL Server',
      logoUrl: microsoftSqlServerLogo,
      authType: 'basic',
      description: 'Connect to a Microsoft SQL Server database.',
      endpointLabel: 'Server',
      endpointPlaceholder: 'sql.example.com',
      endpointHint: 'Provide the SQL Server host name or IP address. Use a dedicated read-only account.',
    },
    {
      name: 'MySQL',
      logoUrl: mysqlLogo,
      authType: 'basic',
      description: 'Connect to a MySQL database with a dedicated read-only account.',
      endpointLabel: 'Server',
      endpointPlaceholder: 'mysql.example.com',
      endpointHint: 'Provide the MySQL host name or IP address.',
    },
    {
      name: 'PostgreSQL',
      logoUrl: postgresqlLogo,
      authType: 'basic',
      description: 'Connect to a PostgreSQL database with a dedicated read-only account.',
      endpointLabel: 'Server',
      endpointPlaceholder: 'postgres.example.com',
      endpointHint: 'Provide the PostgreSQL host name or IP address.',
    },
    {
      name: 'Prometheus',
      logoUrl: prometheusLogo,
      authType: 'basic',
      description: 'Connect to a Prometheus server to query metrics.',
      endpointLabel: 'Server URL',
      endpointPlaceholder: 'http://prometheus.example.com:9090',
      endpointHint: 'Enter the base URL for your Prometheus server.',
    },
    {
      name: 'Grafana',
      logoUrl: grafanaLogo,
      authType: 'basic',
      description: 'Connect to a Grafana instance and import dashboard metadata.',
      endpointLabel: 'Grafana URL',
      endpointPlaceholder: 'https://grafana.example.com',
      endpointHint: 'Enter the base URL of your Grafana instance.',
    },
    {
      name: 'AWS CloudWatch',
      logoUrl: cloudWatchLogo,
      authType: 'basic',
      description: 'Connect to AWS CloudWatch to bring cloud metrics into Nexus.',
      endpointLabel: 'AWS endpoint',
      endpointPlaceholder: 'https://monitoring.ap-south-1.amazonaws.com',
      endpointHint: 'Use the CloudWatch endpoint for your AWS region.',
    },
  ]

  const openDatasourceConfiguration = (datasource) => {
    setSelectedDatasource(datasource)
    setConnectionStatus(null)
  }

  useEffect(() => {
    if (!currentUser.uniqueID) return

    let isCurrent = true
    const loadSavedDatasources = async () => {
      try {
        const response = await requestApi(`${API_BASE_URL}/api/datasources`)
        const data = await readApiResponse(response)
        if (!response.ok || !isCurrent) return
        setSavedDatasources(data.datasources || [])
      } catch {
        // Keep the local copy visible if the backend is temporarily unavailable.
      }
    }

    loadSavedDatasources()
    return () => { isCurrent = false }
  }, [currentUser.uniqueID, requestApi])

  useEffect(() => {
    if (!currentUser.uniqueID) return

    let isCurrent = true
    const query = new URLSearchParams()
    if (dateRange?.start && dateRange?.end) {
      query.set('start', dateRange.start)
      query.set('end', dateRange.end)
    }
    const queryString = query.toString()
    const url = `${API_BASE_URL}/api/dashboard/overview${queryString ? `?${queryString}` : ''}`

    const loadOverview = async () => {
      try {
        const response = await requestApi(url)
        const data = await readApiResponse(response)
        if (!response.ok) throw new Error(data.message || 'Unable to load dashboard telemetry.')
        if (isCurrent) setOverviewData(data)
      } catch (error) {
        if (isCurrent) setOverviewError(error.message || 'Unable to load dashboard telemetry from the server.')
      } finally {
        if (isCurrent) setOverviewLoading(false)
      }
    }

    loadOverview()
    return () => { isCurrent = false }
  }, [currentUser.uniqueID, dateRange?.start, dateRange?.end, requestApi])

  useEffect(() => {
    if (!connectionStatus) return
    const timer = setTimeout(() => {
      setConnectionStatus(null)
    }, 2000)
    return () => clearTimeout(timer)
  }, [connectionStatus])

  const editSavedDatasource = (datasource) => {
    const sourceTemplate = datasourceCards.find((card) => card.name === datasource.type) || datasourceCards.find((card) => card.name === datasource.name)
    setSelectedDatasource({
      ...(sourceTemplate || datasource),
      savedId: datasource.id,
      savedFromDatabase: datasource.databaseId === true,
      savedName: datasource.name,
      savedEndpoint: datasource.endpoint,
      savedSettings: datasource.settings || {},
      savedConfiguredAt: datasource.configuredAt,
    })
    setConnectionStatus(null)
    setShowDatasources(false)
    setShowConnectionForm(true)
  }

  const deleteSavedDatasource = async (datasource) => {
    const { id: datasourceId } = datasource
    if (!currentUser.uniqueID) return

    try {
      const response = await requestApi(`${API_BASE_URL}/api/datasources/${datasourceId}`, {
        method: 'DELETE',
      }, csrfToken)
      const data = await readApiResponse(response)
      if (!response.ok) {
        setConnectionStatus({ type: 'error', text: data.message || 'Unable to delete this data source.' })
        return
      }
      setSavedDatasources((sources) => {
        const nextSources = sources.filter((source) => source.id !== datasourceId)
        return nextSources
      })
    } catch {
      setConnectionStatus({ type: 'error', text: 'Database API is not running. The data source was not deleted.' })
    }
  }

  const analyseDatasource = async (datasource) => {
    if (!currentUser.uniqueID || analysisLoadingId) return
    setAnalysisLoadingId(datasource.id)
    setConnectionStatus(null)
    try {
      const response = await requestApi(`${API_BASE_URL}/api/datasources/${datasource.id}/analysis`)
      const data = await readApiResponse(response)
      if (!response.ok) {
        setConnectionStatus({ type: 'error', text: data.message || 'Unable to analyse this data source.' })
        return
      }
      setAnalysisData(data)
      setShowDatasources(false)
      setShowConnectionForm(false)
      setSelectedDatasource(null)
      setConnectionStatus(null)
    } catch {
      setConnectionStatus({ type: 'error', text: 'Database API is not running. Unable to load analysis.' })
    } finally {
      setAnalysisLoadingId(null)
    }
  }

  const filteredDatasourceCards = datasourceCards.filter((datasource) => (
    datasource.name.toLowerCase().includes(connectionSearch.trim().toLowerCase())
  ))

  const returnToConnections = () => {
    setSelectedDatasource(null)
    setConnectionStatus(null)
  }

  const saveAndTestConnection = async (event) => {
    event.preventDefault()
    const values = new FormData(event.currentTarget)
    const requiredFields = selectedDatasource.authType === 'cato'
      ? ['endpoint', 'apiKey', 'accountId', 'siteIds']
      : selectedDatasource.authType === 'site24x7'
        ? ['accessToken']
        : ['username', 'password']

    if (requiredFields.some((field) => !values.get(field)?.trim())) {
      setConnectionStatus({ type: 'error', text: 'Complete all required connection details before testing.' })
      return
    }

    const datasource = {
      id: selectedDatasource.savedId || `${selectedDatasource.name}-${Date.now()}`,
      name: values.get('name').trim(),
      type: selectedDatasource.name,
      endpoint: values.get('endpoint').trim(),
      logoUrl: selectedDatasource.logoUrl,
      settings: {
        isDefault: values.get('isDefault') === 'on',
        port: values.get('port') || '',
        database: values.get('database') || '',
        accountId: values.get('accountId') || '',
        siteIds: values.get('siteIds') || '',
        skipTlsValidation: values.get('skipTlsValidation') === 'on',
      },
      configuredAt: new Date().toLocaleString(),
      demoData: {
        hosts: 3,
        metrics: 12,
        status: 'Demo data imported',
      },
    }

    const cato = selectedDatasource.authType === 'cato'
      ? {
          CATO_API_URL: datasource.endpoint,
          CATO_API_KEY: values.get('apiKey')?.trim() || '',
          CATO_ACCOUNT_ID: values.get('accountId')?.trim() || '',
          CATO_SITE_IDS: values.get('siteIds')?.trim() || '',
        }
      : null

    const payload = {
      name: datasource.name,
      provider: datasource.type,
      endpoint: datasource.endpoint,
      logoUrl: datasource.logoUrl,
      settings: datasource.settings,
      secrets: {
        username: values.get('username') || '',
        password: values.get('password') || '',
        apiKey: cato ? '' : values.get('apiKey') || '',
        accessToken: values.get('accessToken') || '',
      },
      ...(cato ? { cato } : {}),
    }

    try {
      const isDatabaseEdit = Boolean(selectedDatasource.savedId && selectedDatasource.savedFromDatabase)
      const response = await requestApi(
        isDatabaseEdit
          ? `${API_BASE_URL}/api/datasources/${selectedDatasource.savedId}`
          : `${API_BASE_URL}/api/datasources`,
        {
          method: isDatabaseEdit ? 'PUT' : 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        },
        csrfToken,
      )
      const data = await readApiResponse(response)
      if (!response.ok) {
        setConnectionStatus({ type: 'error', text: data.message || 'Unable to save this data source.' })
        return
      }

      const savedDatasource = data.datasource
      setSavedDatasources((sources) => {
        const nextSources = selectedDatasource.savedId
          ? sources.map((source) => (source.id === selectedDatasource.savedId ? savedDatasource : source))
          : [...sources, savedDatasource]
        return nextSources
      })
      setConnectionStatus({
        type: 'success',
        text: savedDatasource.type === 'Cato'
          ? 'Cato connection saved to dbo.NexusDataSources.'
          : 'Configuration saved.',
      })
    } catch {
      setConnectionStatus({ type: 'error', text: 'Database API is not running. The data source was not saved.' })
      return
    }
    setSelectedDatasource(null)
    setShowConnectionForm(false)
    setShowDatasources(true)
  }

  return (
    <div
      className={`dashboard-body ${sidebarOpen ? 'sidebar-open' : 'sidebar-closed'}`}
      onClick={() => setProfileOpen(false)}
    >
      <aside className="sidebar">
        <div className="sidebar-top">
          <NexusLogo />
        </div>

        <nav className="sidebar-menu">
          <button
            type="button"
            className={`menu-item ${!showConnectionForm && !showDatasources ? 'active' : ''}`}
            onClick={() => {
              setAnalysisData(null)
              setShowConnectionForm(false)
              setShowDatasources(false)
              setConnectionsOpen(false)
              setSelectedDatasource(null)
              setConnectionStatus(null)
            }}
          >
            Home
          </button>

          <div className="connection-group">
            <button
              type="button"
              className={`menu-item connection-toggle ${connectionsOpen ? 'open' : ''}`}
              onClick={() => setConnectionsOpen((open) => !open)}
            >
              <span>Connections</span>
              <span className="dropdown-caret">{connectionsOpen ? '▾' : '▸'}</span>
            </button>

            {connectionsOpen && (
              <div className="connection-submenu">
                <button
                  type="button"
                  className="submenu-item"
                  onClick={() => {
                    setAnalysisData(null)
                    setShowConnectionForm(true)
                    setShowDatasources(false)
                    setConnectionsOpen(false)
                    setSelectedDatasource(null)
                    setConnectionStatus(null)
                    setConnectionSearch('')
                  }}
                >
                  Add New Connection
                </button>
              </div>
            )}
          </div>

          <button
            type="button"
            className={`menu-item ${showDatasources ? 'active' : ''}`}
            onClick={() => {
              setAnalysisData(null)
              setShowDatasources(true)
              setShowConnectionForm(false)
              setSelectedDatasource(null)
              setConnectionStatus(null)
              setConnectionsOpen(false)
            }}
          >
            Datasource
          </button>
        </nav>
      </aside>

      <main className="main-area">
        <header className="top-toolbar">
          <div className="top-toolbar-left">
            <button
              className="nav-toggle"
              onClick={() => {
                setSidebarOpen((open) => !open)
                setConnectionsOpen(false)
              }}
            >
              ☰
            </button>
            <div className="breadcrumbs">Hello, {username}</div>
          </div>
          <div className="toolbar-controls">
            <input className="search-box" type="text" placeholder="Search..." />

            <div className="profile-menu-wrap" onClick={(event) => event.stopPropagation()}>
              <button
                type="button"
                className="profile-chip"
                onClick={() => setProfileOpen((open) => !open)}
              >
                <span className="profile-avatar">{userInitial}</span>
              </button>

              {profileOpen && (
                <div className="profile-dropdown">
                  <button type="button" className="profile-dropdown-item" onClick={() => {
                    setProfileOpen(false)
                    setAccountOpen(true)
                  }}>
                    <span className="profile-action-icon">👤</span>
                    <span>Account</span>
                  </button>
                  <button
                    type="button"
                    className="profile-dropdown-item"
                    disabled={logoutLoading}
                    onClick={async () => {
                      setProfileMessage('')
                      setLogoutLoading(true)
                      const succeeded = await onLogout()
                      setLogoutLoading(false)
                      if (succeeded) setProfileOpen(false)
                      else setProfileMessage('Sign out failed. Check the API connection and try again.')
                    }}
                  >
                    <span className="profile-action-icon">⎋</span>
                    <span>{logoutLoading ? 'Signing out…' : 'Logout'}</span>
                  </button>
                  {profileMessage && <p className="profile-menu-message" role="alert">{profileMessage}</p>}
                </div>
              )}
            </div>
          </div>
        </header>

        {showConnectionForm && !selectedDatasource && (
          <ConnectionCatalog
            filteredDatasourceCards={filteredDatasourceCards}
            connectionSearch={connectionSearch}
            setConnectionSearch={setConnectionSearch}
            openDatasourceConfiguration={openDatasourceConfiguration}
          />
        )}

        {showConnectionForm && selectedDatasource && (
          <DatasourceConfigurationForm
            selectedDatasource={selectedDatasource}
            connectionStatus={connectionStatus}
            returnToConnections={returnToConnections}
            saveAndTestConnection={saveAndTestConnection}
          />
        )}

        {showDatasources && (
          <section className="datasource-list-card">
            <div className="datasource-list-header">
              <div>
                <p>CONNECTIONS</p>
                <h2>Data sources</h2>
                <span>Manage the data sources available to your Nexus dashboards.</span>
              </div>
              <button
                type="button"
                className="overview-action"
                onClick={() => {
                  setShowDatasources(false)
                  setShowConnectionForm(true)
                }}
              >
                <span>+</span> Add data source
              </button>
            </div>

            {connectionStatus && (
              <div className={`connection-status ${connectionStatus.type}`} role="status">
                {connectionStatus.text}
              </div>
            )}

            {savedDatasources.length ? (
              <div className="saved-datasource-grid">
                {savedDatasources.map((datasource) => (
                  <article key={datasource.id} className="saved-datasource-card">
                    <div className="saved-datasource-logo">
                      <img src={getProviderLogo(datasource.type)} alt={`${datasource.type} logo`} />
                    </div>
                    <div className="saved-datasource-details">
                      <h3>{datasource.name}</h3>
                      <span>{datasource.type}</span>
                      <small>{datasource.endpoint}</small>
                    </div>
                    <div className="saved-datasource-status">
                      <div className="saved-datasource-status-row">
                        <span>Configured</span>
                        <button
                          type="button"
                          className="datasource-edit-btn"
                          onClick={() => editSavedDatasource(datasource)}
                          aria-label={`Edit ${datasource.name}`}
                          title="Edit data source"
                        >
                          <span aria-hidden="true">✎</span> Edit
                        </button>
                      </div>
                      <small>{datasource.configuredAt}</small>
                      <button
                        type="button"
                        className="datasource-delete-btn"
                        onClick={() => deleteSavedDatasource(datasource)}
                        aria-label={`Delete ${datasource.name}`}
                        title="Delete data source"
                      >
                        <span aria-hidden="true">×</span> Delete
                      </button>
                      {datasource.type?.toLowerCase() === 'site24x7' && (
                        <button
                          type="button"
                          className="datasource-analyse-btn"
                          onClick={() => analyseDatasource(datasource)}
                          disabled={analysisLoadingId !== null}
                        >
                          {analysisLoadingId === datasource.id ? 'Loading…' : 'Analyse data'}
                        </button>
                      )}
                    </div>
                    <div className="saved-datasource-demo">
                      <span>{datasource.demoData?.status || 'Demo data imported'}</span>
                      <small>{datasource.demoData?.hosts || 3} hosts · {datasource.demoData?.metrics || 12} metrics</small>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <div className="datasource-empty-state">
                <div>+</div>
                <h3>No data sources yet</h3>
                <p>Add a connection, enter its authentication details, and save it here.</p>
              </div>
            )}
          </section>
        )}

        {analysisData && !showConnectionForm && !showDatasources && (
          <section className="monitor-shell analysis-dashboard">
            <div className="overview-header">
              <div>
                <p className="overview-eyebrow">Site24x7 · Database analysis</p>
                <h1>{analysisData.datasource.name}</h1>
                <p>Sample monitoring measurements loaded from the Nexus database.</p>
              </div>
              <div className="overview-actions">
                <button type="button" className="overview-action" onClick={() => setAnalysisData(null)}>
                  Back to overview
                </button>
              </div>
            </div>

            {(() => {
              const averageFor = (metricName) => {
                const values = analysisData.metrics.filter((metric) => metric.name === metricName)
                if (!values.length) return '—'
                return (values.reduce((sum, metric) => sum + metric.value, 0) / values.length).toFixed(1)
              }
              const warningCount = analysisData.metrics.filter((metric) => metric.status === 'Warning').length
              return (
                <>
                  <div className="overview-stats analysis-stats">
                    <article className="overview-stat">
                      <span className="stat-label">Average CPU</span>
                      <strong>{averageFor('CPU utilization')}%</strong>
                      <span className="stat-caption">Across monitored hosts</span>
                    </article>
                    <article className="overview-stat">
                      <span className="stat-label">Average memory</span>
                      <strong>{averageFor('Memory usage')}%</strong>
                      <span className="stat-caption">Across monitored hosts</span>
                    </article>
                    <article className="overview-stat">
                      <span className="stat-label">Availability</span>
                      <strong>{averageFor('Availability')}%</strong>
                      <span className="stat-caption">Mean availability</span>
                    </article>
                    <article className="overview-stat">
                      <span className="stat-label">Warnings</span>
                      <strong className={warningCount ? 'analysis-warning' : 'status-ok'}>{warningCount}</strong>
                      <span className="stat-caption">Metric readings to review</span>
                    </article>
                  </div>

                  <section className="analysis-table-section">
                    <div className="analysis-table-heading">
                      <div>
                        <p className="overview-eyebrow">Measurements</p>
                        <h2>Host telemetry</h2>
                      </div>
                      <span>{analysisData.metrics.length} readings · {new Set(analysisData.metrics.map((metric) => metric.host)).size} hosts</span>
                    </div>
                    <div className="analysis-table-wrap">
                      <table className="analysis-table">
                        <thead>
                          <tr><th>Host</th><th>Metric</th><th>Value</th><th>Status</th><th>Recorded</th></tr>
                        </thead>
                        <tbody>
                          {analysisData.metrics.map((metric) => (
                            <tr key={`${metric.host}-${metric.name}`}>
                              <td>{metric.host}</td>
                              <td>{metric.name}</td>
                              <td>{metric.value}{metric.unit === '%' ? '%' : ` ${metric.unit}`}</td>
                              <td><span className={`analysis-status ${metric.status.toLowerCase()}`}>{metric.status}</span></td>
                              <td>{metric.recordedAt}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </section>
                </>
              )
            })()}
          </section>
        )}

        {!analysisData && !showConnectionForm && !showDatasources && (
          <section className="monitor-shell empty-state">
            <div className="overview-header">
              <div>
                <p className="overview-eyebrow">Observability workspace</p>
                <h1>Your systems, clearly in view.</h1>
                <p>Connect a data source to start bringing your infrastructure into focus.</p>
              </div>
              <div className="overview-actions">
                <button
                  type="button"
                  className="overview-action date-range-btn"
                  onClick={() => {
                    setDateRangeDraft(dateRange || { start: '', end: '' })
                    setDateRangeError('')
                    setShowDateRangePicker((open) => !open)
                  }}
                >
                  <span>📅</span>
                  {dateRange ? `${dateRange.start} → ${dateRange.end}` : 'Last 24 hours'}
                </button>
              </div>
            </div>

            {showDateRangePicker && (
              <div className="date-range-popup" onClick={(event) => event.stopPropagation()}>
                <div className="date-range-popup-head">
                  <h3>Select date range</h3>
                  <button
                    type="button"
                    className="date-range-close"
                    onClick={() => setShowDateRangePicker(false)}
                    aria-label="Close date range picker"
                  >
                    ×
                  </button>
                </div>
                <div className="date-range-fields">
                  <label>
                    <span>From</span>
                    <input
                      type="date"
                      value={dateRangeDraft.start}
                      onChange={(event) => setDateRangeDraft((range) => ({ ...range, start: event.target.value }))}
                    />
                  </label>
                  <label>
                    <span>To</span>
                    <input
                      type="date"
                      value={dateRangeDraft.end}
                      onChange={(event) => setDateRangeDraft((range) => ({ ...range, end: event.target.value }))}
                    />
                  </label>
                </div>
                {dateRangeError && <p className="dashboard-data-message error" role="alert">{dateRangeError}</p>}
                <div className="date-range-actions">
                  <button
                    type="button"
                    className="date-range-clear"
                    onClick={() => {
                      setDateRange(null)
                      setDateRangeDraft({ start: '', end: '' })
                      setDateRangeError('')
                      setOverviewLoading(true)
                      setOverviewError('')
                      setShowDateRangePicker(false)
                    }}
                  >
                    Clear
                  </button>
                  <button
                    type="button"
                    className="date-range-apply"
                    onClick={() => {
                      if (!dateRangeDraft.start || !dateRangeDraft.end) {
                        setDateRangeError('Choose both a start date and an end date.')
                        return
                      }
                      if (dateRangeDraft.start > dateRangeDraft.end) {
                        setDateRangeError('Start date must be on or before the end date.')
                        return
                      }
                      setDateRange(dateRangeDraft)
                      setDateRangeError('')
                      setOverviewLoading(true)
                      setOverviewError('')
                      setShowDateRangePicker(false)
                    }}
                  >
                    Apply
                  </button>
                </div>
              </div>
            )}

            <div className="overview-stats">
              <article className="overview-stat">
                <span className="stat-label">Data sources</span>
                <strong>{overviewData?.summary.dataSources ?? (overviewLoading ? '…' : 0)}</strong>
                <span className="stat-caption">{overviewData?.summary.dataSources ? 'Ready to use' : 'Connect your first source'}</span>
              </article>
              <article className="overview-stat">
                <span className="stat-label">Services monitored</span>
                <strong>{overviewData?.summary.servicesMonitored ?? (overviewLoading ? '…' : 0)}</strong>
                <span className="stat-caption">Unique hosts with telemetry in range</span>
              </article>
              <article className="overview-stat">
                <span className="stat-label">Active alerts</span>
                <strong className={overviewData?.summary.activeAlerts ? 'analysis-warning' : 'status-ok'}>
                  {overviewData?.summary.activeAlerts ?? (overviewLoading ? '…' : 0)}
                </strong>
                <span className="stat-caption">Warning or critical measurements in range</span>
              </article>
            </div>

            <DashboardInsights data={overviewData} loading={overviewLoading} error={overviewError} />

            <div className="getting-started-card">
              <div className="getting-started-icon">N</div>
              <div>
                <span>GET STARTED</span>
                <h2>Bring your signals together</h2>
                <p>Connect InfluxDB, Elasticsearch, Alertmanager, Azure Monitor, and more.</p>
              </div>
              <button type="button" onClick={() => setShowConnectionForm(true)}>Browse connections →</button>
            </div>
          </section>
        )}
      </main>
      {accountOpen && (
        <div className="account-dialog-backdrop" onClick={() => setAccountOpen(false)}>
          <section
            className="account-dialog"
            role="dialog"
            aria-modal="true"
            aria-labelledby="account-dialog-title"
            onClick={(event) => event.stopPropagation()}
          >
            <button type="button" className="account-dialog-close" aria-label="Close account details" onClick={() => setAccountOpen(false)}>×</button>
            <span className="account-dialog-icon">{userInitial}</span>
            <h2 id="account-dialog-title">Account</h2>
            <p className="account-dialog-caption">Signed in to Nexus</p>
            <dl>
              <div><dt>Username</dt><dd>{username}</dd></div>
              <div><dt>User ID</dt><dd>{currentUser.uniqueID || 'Unavailable'}</dd></div>
            </dl>
          </section>
        </div>
      )}
    </div>
  )
}

export default DashboardView
