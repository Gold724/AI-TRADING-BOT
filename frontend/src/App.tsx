import React, { useState, useEffect } from 'react'
import SignalCard from './components/SignalCard'
import SignalStats from './components/SignalStats'
import SignalExport from './components/SignalExport'
import BrokerAdminPanel from './components/BrokerAdminPanel'
import BulenoxTradingPanel from './components/BulenoxTradingPanel'

function App() {
  const [tradeMessage, setTradeMessage] = useState('')
  const [broker, setBroker] = useState('binance')
  const [showConfirm, setShowConfirm] = useState(false)
  const [activeTab, setActiveTab] = useState('dashboard')
  const [bulenoxStrategy, setBulenoxStrategy] = useState<'fast' | 'slow' | 'scalping'>('fast')

  // Vault strategy related state
  const [vaultStrategies, setVaultStrategies] = useState<string[]>([])
  const [selectedStrategy, setSelectedStrategy] = useState('vault-fvg-breakout')
  const [backtestStartDate, setBacktestStartDate] = useState('2023-01-01')
  const [backtestEndDate, setBacktestEndDate] = useState('2023-01-31')
  const [backtestResults, setBacktestResults] = useState<any | null>(null)

  // Authentication states
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('password123')
  const [showPassword, setShowPassword] = useState(false)
  const [authError, setAuthError] = useState('')

  // Trade parameters
  const [tradeParams, setTradeParams] = useState({
    symbol: 'BTCUSDT',
    side: 'BUY',
    quantity: 0.001,
    confidence: 0.8,
    stopLoss: '',
    takeProfit: ''
  })

  // State for tracking backend connection status
  const [backendError, setBackendError] = useState<string | null>(null)

  React.useEffect(() => {
    async function fetchStrategies() {
      try {
        setBackendError(null)
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000'
        const response = await fetch(`${apiUrl}/api/strategy`, {
          credentials: 'include',
          mode: 'cors',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          }
        })
        if (response.status === 401) {
          setIsAuthenticated(false)
          return
        }
        const data = await response.json()
        
        // Adapt the response format from /api/strategy to match what the frontend expects
        if (data.strategy) {
          const strategies = [data.strategy];
          setVaultStrategies(strategies)
          setSelectedStrategy(data.strategy)
        } else if (data.strategies) {
          // Handle both string arrays and object arrays
          const strategyNames = data.strategies.map(strategy => 
            typeof strategy === 'string' ? strategy : strategy.name || strategy.id || String(strategy)
          )
          setVaultStrategies(strategyNames)
          if (strategyNames.length > 0) {
            setSelectedStrategy(strategyNames[0])
          }
        }
      } catch (error) {
        console.error('Failed to fetch strategies', error)
        setBackendError('Unable to connect to backend server - using demo data')
        // Set some default strategies when backend is not available
        const defaultStrategies = [
          'vault-fvg-breakout',
          'vault-support-resistance',
          'vault-trend-following',
          'vault-mean-reversion'
        ];
        setVaultStrategies(defaultStrategies)
        setSelectedStrategy(defaultStrategies[0])
      }
    }
    fetchStrategies()
  }, [isAuthenticated])

  const handleLogin = async () => {
    setAuthError('')
    try {
      // For demo purposes, check if using the default credentials
      if (username === 'admin' && password === 'password123') {
        setIsAuthenticated(true)
        return
      }
      
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000'
      const response = await fetch(`${apiUrl}/api/login`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        credentials: 'include',
        mode: 'cors',
        body: JSON.stringify({ 
          username: username,
          password: password 
        })
      })
      if (response.ok) {
        setIsAuthenticated(true)
      } else {
        const data = await response.json()
        setAuthError(data.message || 'Login failed')
      }
    } catch (error) {
      console.error('Login error:', error)
      setAuthError('Login failed')
    }
  }

  const handleLogout = async () => {
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000'
      await fetch(`${apiUrl}/api/logout`, { 
      method: 'POST',
      credentials: 'include'
    })
    setIsAuthenticated(false)
    setUsername('')
    setPassword('')
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setTradeParams(prevFormData => ({
      ...prevFormData,
      [name]: value,
    }))
  }

  const handleBrokerSelectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setBroker(e.target.value)
    setTradeParams(prevFormData => ({
      ...prevFormData,
      broker: e.target.value,
    }))
  }

  const handleConfidenceChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setTradeParams(prev => ({
      ...prev,
      confidence: Number(e.target.value)
    }))
  }

  const openConfirmModal = () => setShowConfirm(true)
  const closeConfirmModal = () => setShowConfirm(false)

  const executeTrade = async () => {
    setTradeMessage('')
    closeConfirmModal()
    const payload = {
      broker,
      signal: {
        symbol: tradeParams.symbol,
        side: tradeParams.side,
        quantity: parseFloat(tradeParams.quantity as any),
        confidence: tradeParams.confidence,
        stopLoss: tradeParams.stopLoss ? parseFloat(tradeParams.stopLoss as any) : null,
        takeProfit: tradeParams.takeProfit ? parseFloat(tradeParams.takeProfit as any) : null
      }
    }
    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000'
      const response = await fetch(`${apiUrl}/api/trade`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })
      const data = await response.json()
      if (response.ok) {
        setTradeMessage('Trade executed successfully!')
        fetchTradeHistory()
      } else {
        setTradeMessage('Trade failed: ' + data.message)
      }
    } catch (error: unknown) {
      if (error instanceof Error) {
        setTradeMessage('Error triggering trade: ' + error.message)
      } else {
        setTradeMessage('An unknown error occurred')
      }
    }
  }

  interface TradeHistoryItem {
    timestamp: string
    broker: string
    symbol: string
    side: string
    quantity: number
    stopLoss?: number
    takeProfit?: number
    status: string
  }

  const [tradeHistory, setTradeHistory] = useState<TradeHistoryItem[]>([])

  const fetchTradeHistory = async () => {
    try {
      const response = await fetch(`/api/trade/history?broker=${broker}`)
      const data = await response.json()
      if (data.status === 'success') {
        setTradeHistory(data.history as TradeHistoryItem[])
      } else {
        setTradeHistory([])
      }
    } catch (error) {
      setTradeHistory([])
    }
  }

  useEffect(() => {
    fetchTradeHistory()
  }, [])

  if (!isAuthenticated) {
    return (
      <div className="container mx-auto p-4 max-w-md">
        {backendError && (
          <div className="mb-4 bg-yellow-100 text-yellow-800 p-3 rounded shadow">
            {backendError}
          </div>
        )}
        <h2 className="text-2xl font-bold mb-4">Login</h2>
        {authError && <div className="text-red-600 mb-2">{authError}</div>}
        <input
          type="text"
          placeholder="Username"
          value={username}
          onChange={e => setUsername(e.target.value)}
          className="mb-2 p-2 border rounded w-full"
        />
        <div className="relative mb-4">
          <input
            type={showPassword ? "text" : "password"}
            placeholder="Password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            className="p-2 border rounded w-full"
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute inset-y-0 right-0 pr-3 flex items-center text-sm leading-5"
          >
            {showPassword ? (
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
              </svg>
            ) : (
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            )}
          </button>
        </div>
        <button
          onClick={handleLogin}
          className="bg-blue-600 text-white px-4 py-2 rounded w-full"
        >
          Login
        </button>
        <div className="mt-2 text-sm text-gray-600">
          <p>Default credentials:</p>
          <p>Username: admin</p>
          <p>Password: password123</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      {backendError && (
        <div className="max-w-7xl mx-auto mb-4 bg-yellow-100 text-yellow-800 p-3 rounded shadow">
          {backendError}
        </div>
      )}
      <h1 className="text-3xl font-bold mb-6">AI Trading Sentinel Dashboard</h1>
      
      <button
        onClick={handleLogout}
        className="mb-4 bg-red-600 text-white px-4 py-2 rounded"
      >
        Logout
      </button>

      <div className="flex space-x-4 mb-6">
        <button
          className={`px-4 py-2 rounded ${activeTab === 'dashboard' ? 'bg-blue-600 text-white' : 'bg-gray-300'}`}
          onClick={() => setActiveTab('dashboard')}
        >
          Dashboard
        </button>
        <button
          className={`px-4 py-2 rounded ${activeTab === 'bulenox' ? 'bg-green-600 text-white' : 'bg-gray-300'}`}
          onClick={() => setActiveTab('bulenox')}
        >
          Bulenox Trading
        </button>
        <button
          className={`px-4 py-2 rounded ${activeTab === 'admin' ? 'bg-blue-600 text-white' : 'bg-gray-300'}`}
          onClick={() => setActiveTab('admin')}
        >
          Broker Admin
        </button>
      </div>

      {activeTab === 'admin' && <BrokerAdminPanel />}
      
      {activeTab === 'bulenox' && (
        <BulenoxTradingPanel 
          onTradeExecute={(tradeData) => {
            console.log('Bulenox trade executed:', tradeData);
            // Add trade to history
            const newTrade = {
              timestamp: new Date().toISOString(),
              broker: 'bulenox',
              symbol: tradeData.symbol,
              side: tradeData.side,
              quantity: tradeData.quantity,
              stopLoss: tradeData.stopLoss,
              takeProfit: tradeData.takeProfit,
              status: 'executed'
            };
            setTradeHistory(prev => [newTrade, ...prev]);
          }}
        />
      )}

      {activeTab === 'dashboard' && (
        <>
          <SignalCard />
          <SignalStats />
          <SignalExport />

          <div className="mt-6">
            <label className="block mb-2 font-semibold">Select Broker:</label>
            <select value={broker} onChange={handleBrokerSelectChange} className="mb-4 p-2 border rounded">
              <option value="binance">Binance</option>
              <option value="exness">Exness</option>
              <option value="bulenox">Bulenox</option>
            </select>

            <label className="block mb-2 font-semibold">Symbol:</label>
            <input
              type="text"
              name="symbol"
              value={tradeParams.symbol}
              onChange={handleInputChange}
              className="mb-4 p-2 border rounded w-full"
            />

            <label className="block mb-2 font-semibold">Side:</label>
            <select
              name="side"
              value={tradeParams.side}
              onChange={handleInputChange}
              className="mb-4 p-2 border rounded w-full"
            >
              <option value="BUY">BUY</option>
              <option value="SELL">SELL</option>
            </select>

            <label className="block mb-2 font-semibold">Quantity:</label>
            <input
              type="number"
              name="quantity"
              value={tradeParams.quantity.toString()}
              onChange={handleInputChange}
              className="mb-4 p-2 border rounded w-full"
              step="any"
              min="0"
            />

            <label className="block mb-2 font-semibold">Stop Loss (optional):</label>
            <input
              type="number"
              name="stopLoss"
              value={tradeParams.stopLoss}
              onChange={handleInputChange}
              className="mb-4 p-2 border rounded w-full"
              step="any"
              min="0"
            />

            <label className="block mb-2 font-semibold">Take Profit (optional):</label>
            <input
              type="number"
              name="takeProfit"
              value={tradeParams.takeProfit}
              onChange={handleInputChange}
              className="mb-4 p-2 border rounded w-full"
              step="any"
              min="0"
            />

            {/* Vault Strategy Backtest Section */}
            <div className="mt-8 p-4 border rounded bg-white">
              <h2 className="text-xl font-semibold mb-4">Vault Strategy Backtest</h2>

              <label className="block mb-2 font-semibold">Select Strategy:</label>
              <select
                value={selectedStrategy}
                onChange={e => setSelectedStrategy(e.target.value)}
                className="mb-4 p-2 border rounded w-full"
              >
                {vaultStrategies.map(strategy => (
                  <option key={strategy} value={strategy}>{strategy}</option>
                ))}
              </select>

              <label className="block mb-2 font-semibold">Backtest Start Date:</label>
              <input
                type="date"
                value={backtestStartDate}
                onChange={e => setBacktestStartDate(e.target.value)}
                className="mb-4 p-2 border rounded w-full"
              />

              <label className="block mb-2 font-semibold">Backtest End Date:</label>
              <input
                type="date"
                value={backtestEndDate}
                onChange={e => setBacktestEndDate(e.target.value)}
                className="mb-4 p-2 border rounded w-full"
              />

              <button
                onClick={async () => {
                  setBacktestResults(null)
                  try {
                    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000'
      const response = await fetch(`${apiUrl}/api/simulate`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        strategy_name: selectedStrategy,
                        start_date: backtestStartDate,
                        end_date: backtestEndDate
                      })
                    })
                    const data = await response.json()
                    if (response.ok) {
                      setBacktestResults(data)
                    } else {
                      setBacktestResults({ error: data.error || 'Simulation failed' })
                    }
                  } catch (error) {
                    setBacktestResults({ error: 'Error running simulation' })
                  }
                }}
                className="px-4 py-2 bg-blue-600 text-white rounded"
              >
                Run Simulation
              </button>

              {backtestResults && (
                <div className="mt-6">
                  {backtestResults.error ? (
                    <div className="text-red-600 font-semibold">Error: {backtestResults.error}</div>
                  ) : (
                    <>
                      <h3 className="font-semibold mb-2">Simulation Results for {backtestResults.strategy}</h3>
                      <p>Period: {backtestResults.start_date} to {backtestResults.end_date}</p>

                      <h4 className="mt-4 font-semibold">Trade Signals:</h4>
                      <ul className="list-disc list-inside max-h-40 overflow-auto border p-2 rounded bg-gray-50">
                        {backtestResults.signals.map((signal: any, idx: number) => (
                          <li key={idx}>
                            {signal.timestamp} - {signal.symbol} - {signal.side.toUpperCase()} @ {signal.price} x {signal.quantity}
                          </li>
                        ))}
                      </ul>

                      <h4 className="mt-4 font-semibold">PnL Summary:</h4>
                      <ul className="list-disc list-inside">
                        <li>Total Trades: {backtestResults.pnl_summary.total_trades}</li>
                        <li>Winning Trades: {backtestResults.pnl_summary.winning_trades}</li>
                        <li>Losing Trades: {backtestResults.pnl_summary.losing_trades}</li>
                        <li>Net Profit: {backtestResults.pnl_summary.net_profit}</li>
                      </ul>
                    </>
                  )}
                </div>
              )}
            </div>

            <button
              onClick={openConfirmModal}
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
            >
              Execute Trade
            </button>

            {tradeMessage && <p className="mt-2">{tradeMessage}</p>}
          </div>

          {showConfirm && (
            <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
              <div className="bg-white p-6 rounded shadow-lg max-w-md w-full">
                <h2 className="text-xl font-bold mb-4">Confirm Trade Execution</h2>
                <p>Are you sure you want to execute this trade?</p>
                <ul className="my-4 list-disc list-inside">
                  <li>Broker: {broker}</li>
                  <li>Symbol: {tradeParams.symbol}</li>
                  <li>Side: {tradeParams.side}</li>
                  <li>Quantity: {tradeParams.quantity}</li>
                  {tradeParams.stopLoss && <li>Stop Loss: {tradeParams.stopLoss}</li>}
                  {tradeParams.takeProfit && <li>Take Profit: {tradeParams.takeProfit}</li>}
                </ul>
                <div className="flex justify-end space-x-4">
                  <button onClick={closeConfirmModal} className="px-4 py-2 border rounded">
                    Cancel
                  </button>
                  <button onClick={executeTrade} className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700">
                    Confirm
                  </button>
                </div>
              </div>
            </div>
          )}

          <div className="mt-10">
            <h2 className="text-2xl font-bold mb-4">Trade History</h2>
            <table className="min-w-full bg-white border border-gray-300">
              <thead>
                <tr>
                  <th className="border px-4 py-2">Timestamp</th>
                  <th className="border px-4 py-2">Broker</th>
                  <th className="border px-4 py-2">Symbol</th>
                  <th className="border px-4 py-2">Side</th>
                  <th className="border px-4 py-2">Quantity</th>
                  <th className="border px-4 py-2">Stop Loss</th>
                  <th className="border px-4 py-2">Take Profit</th>
                  <th className="border px-4 py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {tradeHistory.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="text-center p-4">
                      No trades executed yet.
                    </td>
                  </tr>
                ) : (
                  tradeHistory.map((trade, index) => (
                    <tr key={index}>
                      <td className="border px-4 py-2">{trade.timestamp}</td>
                      <td className="border px-4 py-2">{trade.broker}</td>
                      <td className="border px-4 py-2">{trade.symbol}</td>
                      <td className="border px-4 py-2">{trade.side}</td>
                      <td className="border px-4 py-2">{trade.quantity}</td>
                      <td className="border px-4 py-2">{trade.stopLoss ?? '-'}</td>
                      <td className="border px-4 py-2">{trade.takeProfit ?? '-'}</td>
                      <td className="border px-4 py-2">{trade.status}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}

export default App
