function ConnectionCatalog({ filteredDatasourceCards, connectionSearch, setConnectionSearch, openDatasourceConfiguration }) {
  return (
<section className="connection-feature-card">
            <div className="connection-feature-head">
              <div>
                <h2>Add new connection</h2>
                <p>Browse and create new connections</p>
              </div>
            </div>

            <div className="connection-search-row">
              <div className="connection-search-box">
                <span className="search-icon">⌕</span>
                <input
                  type="text"
                  value={connectionSearch}
                  onChange={(event) => setConnectionSearch(event.target.value)}
                  placeholder="Search connections"
                  aria-label="Search connections"
                />

                {connectionSearch && (
                  <div className="connection-suggestions">
                    {filteredDatasourceCards.length ? (
                      filteredDatasourceCards.map((card) => (
                        <button
                          type="button"
                          key={card.name}
                          className="connection-suggestion"
                          onClick={() => openDatasourceConfiguration(card)}
                        >
                          <img src={card.logoUrl} alt="" />
                          <span>{card.name}</span>
                        </button>
                      ))
                    ) : (
                      <p>No matching connections found.</p>
                    )}
                  </div>
                )}
              </div>
            </div>

            <div className="connection-filter-row">
              <button type="button" className="filter-pill active">Data source</button>
            </div>

            <div className="connections-data-section">
              <div className="connection-section-title">
                <span>Data source</span>
              </div>

              <div className="connection-card-grid">
                {filteredDatasourceCards.map((card) => (
                  <button
                    type="button"
                    key={card.name}
                    className="connection-card"
                    onClick={() => openDatasourceConfiguration(card)}
                  >
                    <div className="connection-card-left">
                      <div className="connection-logo">
                        <img src={card.logoUrl} alt={`${card.name} logo`} />
                      </div>
                      <span>{card.name}</span>
                    </div>
                    <div className="connection-check">✓</div>
                  </button>
                ))}
                {!filteredDatasourceCards.length && (
                  <p className="connection-empty-results">Try a different connection name.</p>
                )}
              </div>
            </div>
          </section>
  )
}

export default ConnectionCatalog
