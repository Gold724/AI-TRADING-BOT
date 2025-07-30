import React, { useState, useEffect } from 'react';

interface SymbolStatusProps {
  className?: string;
}

const SymbolStatusPanel: React.FC<SymbolStatusProps> = ({ className = '' }) => {
  const [symbol, setSymbol] = useState<string>('Loading...');
  const [mode, setMode] = useState<string>('Loading...');
  const [confirmed, setConfirmed] = useState<boolean>(false);
  const [tradingRules, setTradingRules] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSymbolStatus = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/account/symbol-status');
      const result = await response.json();
      
      if (result.status === 'success') {
        setSymbol(result.symbol);
        setMode(result.mode);
        setConfirmed(result.gold_symbol_confirmed);
        setTradingRules(result.trading_rules || '');
      } else {
        setError('Failed to load symbol status');
      }
    } catch (err) {
      setError('Error connecting to server');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSymbolStatus();
    
    // Refresh data every 5 minutes
    const interval = setInterval(fetchSymbolStatus, 300000);
    return () => clearInterval(interval);
  }, []);

  if (loading && symbol === 'Loading...') {
    return <div className="p-4">Loading symbol status...</div>;
  }

  if (error) {
    return <div className="p-4 text-red-600">{error}</div>;
  }

  return (
    <div className={`bg-white p-4 rounded shadow ${className}`}>
      <h2 className="text-xl font-semibold mb-4">Symbol Status</h2>
      <div className="grid grid-cols-1 gap-3">
        <div>
          <p className="text-gray-600">Detected Symbol</p>
          <p className="font-semibold flex items-center">
            <span className="mr-2">🪙</span>
            {symbol}
            {confirmed ? 
              <span className="ml-2 text-xs bg-green-100 text-green-800 px-2 py-1 rounded">Confirmed</span> : 
              <span className="ml-2 text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">Not Confirmed</span>
            }
          </p>
        </div>
        <div>
          <p className="text-gray-600">Trading Mode</p>
          <p className="font-semibold flex items-center">
            <span className="mr-2">🎯</span>
            {mode}
          </p>
        </div>
        {tradingRules && (
          <div>
            <p className="text-gray-600">Trading Rules</p>
            <p className="text-sm bg-blue-50 p-2 rounded border border-blue-100">
              {tradingRules}
            </p>
          </div>
        )}
        <div className="mt-2">
          <button 
            onClick={fetchSymbolStatus}
            className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
          >
            Refresh Status
          </button>
        </div>
      </div>
    </div>
  );
};

export default SymbolStatusPanel;