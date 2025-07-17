import React, { useState } from 'react'

const SignalExport: React.FC = () => {
  const [exporting, setExporting] = useState(false)
  const [message, setMessage] = useState('')

  const handleExport = async () => {
    setExporting(true)
    setMessage('')
    try {
      const response = await fetch('http://localhost:5000/api/signal/export', { method: 'POST' })
      if (response.ok) {
        setMessage('Export successful!')
      } else {
        setMessage('Export failed.')
      }
    } catch (error) {
      setMessage('Error during export.')
    }
    setExporting(false)
  }

  return (
    <div className="bg-white p-4 rounded shadow">
      <button
        onClick={handleExport}
        disabled={exporting}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
      >
        {exporting ? 'Exporting...' : 'Export Signal & Test Webhook'}
      </button>
      {message && <p className="mt-2">{message}</p>}
    </div>
  )
}

export default SignalExport