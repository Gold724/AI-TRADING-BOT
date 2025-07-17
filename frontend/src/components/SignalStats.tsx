import React, { useEffect, useState } from 'react'

interface SignalStatsData {
  totalSignals: number
  averageConfidence: number
  history: Array<{ timestamp: string; confidence: number; direction: string; asset: string }>
}

const SignalStats: React.FC = () => {
  const [stats, setStats] = useState<SignalStatsData | null>(null)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/signal/stats')
        const data = await response.json()
        setStats(data)
      } catch (error) {
        console.error('Error fetching signal stats:', error)
      }
    }

    fetchStats()
    const interval = setInterval(fetchStats, 10000)
    return () => clearInterval(interval)
  }, [])

  if (!stats) return <div>Loading signal stats...</div>

  return (
    <div className="bg-white p-4 rounded shadow mb-4">
      <h2 className="text-xl font-semibold mb-2">Signal Stats</h2>
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
    </div>
  )
}

export default SignalStats