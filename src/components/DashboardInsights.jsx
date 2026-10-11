import { useState } from 'react'

const chartColors = ['#48d597', '#9b86ff', '#67b4ff', '#ff985c']
const plot = { left: 52, right: 588, top: 18, bottom: 132 }

const formatValue = (value) => {
  if (Math.abs(value) >= 1000) return value.toLocaleString(undefined, { maximumFractionDigits: 1 })
  return Number(value.toFixed(2)).toString()
}

function TelemetryChart({ series, color }) {
  const [hoverState, setHoverState] = useState(null)
  const values = series.points.flatMap((point) => [point.minimum, point.maximum, point.average])
  const rawMin = Math.min(...values)
  const rawMax = Math.max(...values)
  const padding = Math.max((rawMax - rawMin) * 0.15, Math.abs(rawMax) * 0.05, 1)
  const minValue = Math.max(0, rawMin - padding)
  const maxValue = series.unit === '%' ? Math.min(100, rawMax + padding) : rawMax + padding
  const range = maxValue - minValue || 1
  const xFor = (index) => series.points.length === 1
    ? (plot.left + plot.right) / 2
    : plot.left + (index / (series.points.length - 1)) * (plot.right - plot.left)
  const yFor = (value) => plot.bottom - ((value - minValue) / range) * (plot.bottom - plot.top)
  const linePath = series.points.map((point, index) => `${index === 0 ? 'M' : 'L'} ${xFor(index)} ${yFor(point.average)}`).join(' ')
  const handlePointerMove = (event) => {
    const bounds = event.currentTarget.getBoundingClientRect()
    if (!bounds.width || series.points.length === 0) return
    const pointerX = event.clientX - bounds.left
    const svgX = (pointerX / bounds.width) * 600
    const plotX = Math.max(plot.left, Math.min(plot.right, svgX))
    let nearestIndex = 0
    for (let index = 1; index < series.points.length; index += 1) {
      if (Math.abs(xFor(index) - plotX) < Math.abs(xFor(nearestIndex) - plotX)) nearestIndex = index
    }
    setHoverState({ index: nearestIndex, x: pointerX, width: bounds.width })
  }
  const hoverIndex = hoverState?.index ?? null
  const hoveredPoint = hoverIndex === null ? null : series.points[hoverIndex]
  const hoveredX = hoverIndex === null ? 0 : xFor(hoverIndex)
  const tooltipMargin = hoverState ? Math.min(110, hoverState.width / 2) : 0
  const tooltipLeft = hoverState
    ? Math.max(tooltipMargin, Math.min(hoverState.x, hoverState.width - tooltipMargin))
    : 0
  const tooltipDate = hoveredPoint
    ? new Date(hoveredPoint.timestamp.replace(' ', 'T')).toLocaleDateString(undefined, {
      year: 'numeric', month: 'long', day: 'numeric', timeZone: 'UTC',
    })
    : ''
  const rangeArea = series.points.length > 1
    ? [
      ...series.points.map((point, index) => `${xFor(index)},${yFor(point.maximum)}`),
      ...series.points.slice().reverse().map((point, reverseIndex) => {
        const index = series.points.length - 1 - reverseIndex
        return `${xFor(index)},${yFor(point.minimum)}`
      }),
    ].join(' ')
    : ''
  const ticks = [0, 1, 2, 3].map((index) => maxValue - (range * index) / 3)

  return (
    <>
      <div
        className="insight-chart-wrap"
        onPointerMove={handlePointerMove}
        onPointerLeave={() => setHoverState(null)}
      >
        <svg
          className="insight-line-chart"
          viewBox="0 0 600 150"
          role="img"
          aria-label={`${series.name} line chart across ${series.points.length} time bucket${series.points.length === 1 ? '' : 's'}`}
        >
        {ticks.map((value, index) => {
          const y = plot.top + (index / 3) * (plot.bottom - plot.top)
          return (
            <g key={index}>
              <line className="insight-grid-line" x1={plot.left} x2={plot.right} y1={y} y2={y} />
              <text className="insight-y-label" x={plot.left - 9} y={y + 4} textAnchor="end">{formatValue(value)}</text>
            </g>
          )
        })}
        {rangeArea && <polygon points={rangeArea} fill={color} fillOpacity="0.13" />}
        {series.points.map((point, index) => (
          <line
            key={`range-${point.timestamp}`}
            x1={xFor(index)}
            x2={xFor(index)}
            y1={yFor(point.maximum)}
            y2={yFor(point.minimum)}
            stroke={color}
            strokeOpacity="0.55"
            strokeWidth="2"
          />
        ))}
        {series.points.length > 1 && (
          <path d={linePath} fill="none" stroke={color} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
        )}
        {hoveredPoint && (
          <line className="insight-hover-guide" x1={hoveredX} x2={hoveredX} y1={plot.top} y2={plot.bottom} />
        )}
        {series.points.map((point, index) => (
          <circle key={point.timestamp} cx={xFor(index)} cy={yFor(point.average)} r={hoverIndex === index ? 6 : 4.5} fill={color} stroke="#171520" strokeWidth="2">
            <title>{`${point.timestamp}: average ${formatValue(point.average)} ${series.unit}; range ${formatValue(point.minimum)}–${formatValue(point.maximum)} (${point.count} samples)`}</title>
          </circle>
        ))}
        </svg>
        {hoveredPoint && (
          <div
            className="insight-hover-tooltip"
            style={{ left: `${tooltipLeft}px` }}
            role="status"
          >
            <strong>{tooltipDate}</strong>
            <span>Average: {formatValue(hoveredPoint.average)} {series.unit}</span>
            <span>Range: {formatValue(hoveredPoint.minimum)}–{formatValue(hoveredPoint.maximum)} {series.unit}</span>
          </div>
        )}
      </div>
      <div className={`insight-chart-labels${series.points.length === 1 ? ' insight-chart-labels-single' : ''}`}>
        {series.points.length === 1 ? (
          <span>{series.points[0].timestamp.slice(0, 10)} · one time bucket</span>
        ) : (
          <>
            <span>{series.points[0].timestamp.slice(0, 10)}</span>
            <span>{series.points[series.points.length - 1].timestamp.slice(0, 10)}</span>
          </>
        )}
      </div>
    </>
  )
}

function DashboardInsights({ data, loading, error }) {
  return (
    <section className="insights-section">
      <div className="insights-header">
        <div>
          <p className="overview-eyebrow">Live server analysis</p>
          <h2>Telemetry · {data?.range.label || 'Loading range'}</h2>
          <span>
            {loading
              ? 'Refreshing from the server…'
              : `${data?.summary.measurementCount || 0} measurements · ${data?.summary.servicesMonitored || 0} services · updated ${data?.generatedAt || '—'}`}
          </span>
        </div>
      </div>

      {error && <p className="dashboard-data-message error" role="alert">{error}</p>}

      {data?.series.length ? (
        <div className="insights-grid">
          {data.series.map((series, index) => (
            <article className="insight-card" key={`${series.name}-${series.unit}`}>
              <div className="insight-card-head">
                <h3>{series.name}</h3>
                <span className="insight-badge">{series.unit}</span>
              </div>
              <TelemetryChart series={series} color={chartColors[index % chartColors.length]} />
            </article>
          ))}
        </div>
      ) : (
        !loading && <p className="dashboard-data-message">No telemetry was recorded for this date range.</p>
      )}
    </section>
  )
}

export default DashboardInsights
