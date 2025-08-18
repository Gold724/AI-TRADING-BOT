import React, { useEffect, useState } from 'react'

interface SignalStatsData {
  totalSignals: number
  averageConfidence: number
  history: Array<{ timestamp: string; confidence: number; direction: string; asset: string }>
}

const SignalStats: React.FC = () => {
  const [stats, setStats] = useState<SignalStatsData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState<boolean>(true)

  useEffect(() => {
    const fetchStats = async () => {
      setLoading(true)
      setError(null)
      try {
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000'
      const response = await fetch(`${apiUrl}/api/signal/stats`)
        const data = await response.json()
        setStats(data)
      } catch (error) {
        console.error('Error fetching signal stats:', error)
        setError('Unable to connect to backend server')
        // Set default stats when backend is unavailable
        setStats({
          totalSignals: 5,
          averageConfidence: 82.5,
          history: [
            { timestamp: new Date().toISOString(), confidence: 85, direction: 'BUY', asset: 'BTCUSDT' },
            { timestamp: new Date(Date.now() - 3600000).toISOString(), confidence: 78, direction: 'SELL', asset: 'ETHUSDT' },
            { timestamp: new Date(Date.now() - 7200000).toISOString(), confidence: 92, direction: 'BUY', asset: 'BNBUSDT' },
            { timestamp: new Date(Date.now() - 10800000).toISOString(), confidence: 75, direction: 'SELL', asset: 'ADAUSDT' },
            { timestamp: new Date(Date.now() - 14400000).toISOString(), confidence: 82, direction: 'BUY', asset: 'SOLUSDT' }
          ]
        })
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
    const interval = setInterval(fetchStats, 10000)
    return () => clearInterval(interval)
  }, [])

  if (loading && !stats) return <div>Loading signal stats...</div>

  return (
    <div className="bg-white p-4 rounded shadow mb-4">
      <h2 className="text-xl font-semibold mb-2">Signal Stats</h2>
      {error && (
        <div className="mb-2 p-2 bg-yellow-100 text-yellow-800 rounded text-sm">
          {error} - Using demo data
        </div>
      )}
      {stats && (
        <>
          <p>Total Signals: {stats.totalSignals}</p>
          <p>Average Confidence: {stats.averageConfidence.toFixed(2)}%</p>
          <h3 className="mt-4 font-semibold">Signal History</h3>
          <ul className="max-h-48 overflow-auto">
            {stats.history.map((item, index) => (
              <li key={index} className="border-b border-gray-200 py-1">
                <span>{new Date(item.timestamp).toLocaleString()} - </span>
                <span>{item.asset} </span>
                <span>{item.direction} </span>
                <span>Confidence: {item.confidence}%</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}

export default SignalStats