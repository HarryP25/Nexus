import solarWindsLogo from '../assets/integrations/solarwinds.png'
import catoLogo from '../assets/integrations/cato.png'
import site24x7Logo from '../assets/integrations/site24x7.png'
import microsoftSqlServerLogo from '../assets/integrations/microsoft-sql-server.png'
import mysqlLogo from '../assets/integrations/mysql.svg'
import postgresqlLogo from '../assets/integrations/postgresql.svg'
import prometheusLogo from '../assets/integrations/prometheus.svg'
import grafanaLogo from '../assets/integrations/grafana.svg'
import cloudWatchLogo from '../assets/integrations/cloudwatch.svg'
const providerLogos = {
  'Cato': catoLogo,
  'Site24x7': site24x7Logo,
  'SolarWinds SWIS API': solarWindsLogo,
  'Solarwinds': solarWindsLogo,
  'Microsoft SQL Server': microsoftSqlServerLogo,
  'MySQL': mysqlLogo,
  'PostgreSQL': postgresqlLogo,
  'Prometheus': prometheusLogo,
  'Grafana': grafanaLogo,
  'AWS CloudWatch': cloudWatchLogo,
}

export const getProviderLogo = (providerName) => providerLogos[providerName] || providerLogos[providerName?.split(' ')[0]]
