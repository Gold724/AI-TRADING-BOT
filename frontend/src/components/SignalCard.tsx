import React, { useEffect, useState } from 'react'

interface Signal {
  confidence: number
  direction: string
  asset: string
}

const SignalCard: React.FC = () => {
  const [signal, setSignal] = useState<Signal | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState<boolean>(true)

  useEffect(() => {
    const fetchSignal = async () => {
      setLoading(true)
      setError(null)
      try {
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000'
    const response = await fetch(`${apiUrl}/api/signal`)
        const data = await response.json()
        setSignal(data)
      } catch (error) {
        console.error('Error fetching signal:', error)
        setError('Unable to connect to backend server')
        // Set default signal data when backend is unavailable
        setSignal({
          confidence: 85,
          direction: 'BUY',
          asset: 'BTCUSDT'
        })
      } finally {
        setLoading(false)
      }
    }

    fetchSignal()
    const interval = setInterval(fetchSignal, 5000)
    return () => clearInterval(interval)
  }, [])

  if (loading && !signal) return <div>Loading signal...</div>

  return (
    <div className="bg-white p-4 rounded shadow mb-4">
      <h2 className="text-xl font-semibold mb-2">Current Signal</h2>
      {error && (
        <div className="mb-2 p-2 bg-yellow-100 text-yellow-800 rounded text-sm">
          {error} - Using demo data
        </div>
      )}
      {signal && (
        <>
          <p>Asset: {signal.asset}</p>
          <p>Direction: {signal.direction}</p>
          <p>Confidence: {signal.confidence}%</p>
          {signal.confidence > 70 && (
            <div className="mt-2 p-2 bg-green-200 text-green-800 rounded">High Confidence Signal Alert!</div>
          )}
        </>
      )}
    </div>
  )
}

export default SignalCard