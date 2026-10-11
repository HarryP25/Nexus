import NexusLogo from './Brand.jsx'

function LandingView({ mode, showAuth, message, messageType, showSignupSuccess, createdUsername, onOpenAuth, onCloseAuth, onDismissMessage, onSignInNow, onEnterDashboard }) {
  return (
    <div className="landing-shell">
      <div className="bg-grid" />

      <header className="landing-header">
        <NexusLogo />
      </header>

      <main className="landing-grid">
        <section className={`hero-copy ${showAuth ? 'blurred' : ''}`}>
          <p className="eyebrow">AI Powered Wissen Platform</p>
          <h1>Welcome to Wissen Nexus </h1>
          <p className="hero-subtext">
            Unified observability and digital experience for modern IT.
          </p>

          <div className="hero-actions">
            <button className="primary-btn large-btn" onClick={() => onOpenAuth('signup')}>Get Started</button>
            <button className="ghost-btn large-btn" onClick={() => onOpenAuth('signin')}>Sign In</button>
          </div>

        </section>

        {showAuth && (
          <div className="auth-popup-backdrop" onClick={onCloseAuth}>
            <section className="auth-panel" onClick={(event) => event.stopPropagation()}>
              <div className="auth-card">
                <button type="button" className="close-btn" onClick={onCloseAuth} aria-label="Close authentication panel">
                  ×
                </button>

                <div className="form-header">
                  <h2>{mode === 'signin' ? 'Sign in to Nexus' : 'Create your Nexus account'}</h2>
                </div>

                {message && (
                  <div className={`auth-message ${messageType}`} role="alert">
                    <span>{message}</span>
                    <button type="button" onClick={onDismissMessage} aria-label="Dismiss message">×</button>
                  </div>
                )}

                <form onSubmit={onEnterDashboard} className="auth-form">
                  <label>
                    <span>Username</span>
                    <input name="username" type="text" placeholder="" required />
                  </label>

                  <label>
                    <span>Password</span>
                    <input
                      name="password"
                      type="password"
                      placeholder=""
                      minLength={mode === 'signup' ? 12 : undefined}
                      maxLength={256}
                      required
                    />
                  </label>

                  <div className="remember-row">
                    <label className="checkbox">
                      <input type="checkbox" defaultChecked />
                      <span>Remember me</span>
                    </label>
                    <a href="#" className="text-link">Forgot password?</a>
                  </div>

                  <button type="submit" className="primary-btn full-width">
                    {mode === 'signin' ? 'Continue' : 'Create account'}
                  </button>
                </form>

                {showSignupSuccess && (
                  <div className="signup-success-popup" role="dialog" aria-modal="true" aria-labelledby="signup-success-title">
                    <div className="success-icon" aria-hidden="true">✓</div>
                    <h3 id="signup-success-title">Account created!</h3>
                    <p>
                      Your Nexus account for <strong>{createdUsername}</strong> is ready. Please sign in with the username and password you just created.
                    </p>
                    <button type="button" className="primary-btn full-width" onClick={onSignInNow}>
                      Sign in now
                    </button>
                  </div>
                )}
              </div>
            </section>
          </div>
        )}
      </main>
    </div>
  )
}

export default LandingView
