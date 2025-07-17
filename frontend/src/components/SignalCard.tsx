import React, { useEffect, useState } from 'react'

interface Signal {
  confidence: number
  direction: string
  asset: string
}

const SignalCard: React.FC = () => {
  const [signal, setSignal] = useState<Signal | null>(null)

  useEffect(() => {
    const fetchSignal = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/signal')
        const data = await response.json()
        setSignal(data)
      } catch (error) {
        console.error('Error fetching signal:', error)
      }
    }

    fetchSignal()
    const interval = setInterval(fetchSignal, 5000)
    return () => clearInterval(interval)
  }, [])

  if (!signal) return <div>Loading signal...</div>

  return (
    <div className="bg-white p-4 rounded shadow mb-4">
      <h2 className="text-xl font-semibold mb-2">Current Signal</h2>
      <p>Asset: {signal.asset}</p>
      <p>Direction: {signal.direction}</p>
      <p>Confidence: {signal.confidence}%</p>
      {signal.confidence > 70 && (
        <div className="mt-2 p-2 bg-green-200 text-green-800 rounded">High Confidence Signal Alert!</div>
      )}
    </div>
  )
}

export default SignalCard