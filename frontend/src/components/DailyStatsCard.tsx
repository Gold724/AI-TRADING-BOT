import React, { useState, useEffect } from 'react';

interface Trade {
  pnl: number;
  contracts: number;
  timestamp: string;
}

interface DayData {
  day: number;
  daily_target: number;
  actual_pnl: number;
  suggested_contracts: number;
  trades: Trade[];
  status: 'in_progress' | 'target_hit' | 'overdrawn';
  date: string;
}

interface DailyStatsCardProps {
  dayData: DayData;
  onReset: () => void;
}

const DailyStatsCard: React.FC<DailyStatsCardProps> = ({ dayData, onReset }) => {
  const [isUpdating, setIsUpdating] = useState(false);
  const [pnl, setPnl] = useState(dayData.actual_pnl.toString());
  const [contracts, setContracts] = useState(dayData.suggested_contracts.toString());
  const [error, setError] = useState<string | null>(null);
  const [perTradeTargets, setPerTradeTargets] = useState<number | null>(null);
  const [numTrades, setNumTrades] = useState<number>(3);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString();
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString();
  };

  const fetchPerTradeTargets = async () => {
    try {
      const response = await fetch(`/api/per-trade-targets?daily_target=${dayData.daily_target}&num_trades=${numTrades}`);
      const result = await response.json();
      
      if (result.status === 'success') {
        setPerTradeTargets(result.data.per_trade_target);
      } else {
        console.error('Failed to load per-trade targets');
      }
    } catch (err) {
      console.error('Error fetching per-trade targets:', err);
    }
  };
  
  // Fetch per-trade targets when component mounts or numTrades changes
  useEffect(() => {
    fetchPerTradeTargets();
  }, [numTrades, dayData.daily_target]);

  const getStatusBadge = () => {
    switch (dayData.status) {
      case 'target_hit':
        return <span className="px-2 py-1 bg-green-100 text-green-800 rounded">✅ Target Hit</span>;
      case 'overdrawn':
        return <span className="px-2 py-1 bg-red-100 text-red-800 rounded">❌ Overdrawn</span>;
      default:
        return <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded">⚠️ In Progress</span>;
    }
  };

  const handleUpdate = async () => {
    try {
      setError(null);
      setIsUpdating(true);
      
      const pnlValue = parseFloat(pnl);
      const contractsValue = parseInt(contracts);
      
      if (isNaN(pnlValue) || isNaN(contractsValue)) {
        setError('Please enter valid numbers');
        return;
      }
      
      const response = await fetch('/api/progress/track', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          day: dayData.day,
          actual_pnl: pnlValue,
          contracts_used: contractsValue,
        }),
      });
      
      const result = await response.json();
      
      if (result.status !== 'success') {
        setError('Failed to update day data');
      } else {
        // Refresh the page data
        window.location.reload();
      }
    } catch (err) {
      setError('Error connecting to server');
      console.error(err);
    } finally {
      setIsUpdating(false);
    }
  };

  const progressPercentage = (dayData.actual_pnl / dayData.daily_target) * 100;
  const cappedProgressPercentage = Math.min(100, Math.max(0, progressPercentage));

  return (
    <div className="bg-white p-4 rounded shadow">
      <div className="flex justify-between items-center mb-4">
        <div>
          <h3 className="text-lg font-semibold">Day {dayData.day} - {formatDate(dayData.date)}</h3>
          {getStatusBadge()}
        </div>
        <button 
          onClick={onReset}
          className="px-3 py-1 text-sm bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
        >
          Reset
        </button>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div>
          <p className="text-gray-600">Daily Target</p>
          <p className="text-xl font-bold">${dayData.daily_target.toFixed(2)}</p>
        </div>
        <div>
          <p className="text-gray-600">Actual P&L</p>
          <p className={`text-xl font-bold ${dayData.actual_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            ${dayData.actual_pnl.toFixed(2)}
          </p>
        </div>
        <div>
          <div className="flex items-center justify-between">
            <p className="text-gray-600">Per-Trade Target</p>
            <div className="flex items-center space-x-2">
              <button 
                onClick={() => setNumTrades(Math.max(1, numTrades - 1))}
                className="px-2 py-0.5 bg-gray-200 rounded hover:bg-gray-300 text-sm"
              >
                -
              </button>
              <span className="text-sm">{numTrades} trades</span>
              <button 
                onClick={() => setNumTrades(numTrades + 1)}
                className="px-2 py-0.5 bg-gray-200 rounded hover:bg-gray-300 text-sm"
              >
                +
              </button>
            </div>
          </div>
          <p className="text-xl font-bold text-blue-600">
            ${perTradeTargets !== null ? perTradeTargets.toFixed(2) : '...'}
          </p>
        </div>
      </div>
      
      {/* Progress bar */}
      <div className="mb-4">
        <div className="flex justify-between text-sm mb-1">
          <span>Progress</span>
          <span>{progressPercentage.toFixed(1)}%</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div 
            className={`h-2.5 rounded-full ${dayData.actual_pnl >= 0 ? 'bg-green-600' : 'bg-red-600'}`} 
            style={{ width: `${cappedProgressPercentage}%` }}
          ></div>
        </div>
      </div>
      
      {/* Trades */}
      <div className="mb-4">
        <h4 className="font-semibold mb-2">Trades ({dayData.trades.length})</h4>
        {dayData.trades.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Contracts</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">P&L</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {dayData.trades.map((trade, index) => (
                  <tr key={index}>
                    <td className="px-4 py-2 whitespace-nowrap text-sm">{formatTime(trade.timestamp)}</td>
                    <td className="px-4 py-2 whitespace-nowrap text-sm">{trade.contracts}</td>
                    <td className={`px-4 py-2 whitespace-nowrap text-sm font-medium ${trade.pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      ${trade.pnl.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-500 text-sm">No trades recorded yet.</p>
        )}
      </div>
      
      {/* Update Form */}
      <div className="border-t pt-4 mt-4">
        <h4 className="font-semibold mb-2">Update Day Results</h4>
        {error && <p className="text-red-600 text-sm mb-2">{error}</p>}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">P&L Amount</label>
            <input
              type="number"
              value={pnl}
              onChange={(e) => setPnl(e.target.value)}
              className="w-full p-2 border rounded"
              placeholder="Enter P&L amount"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Contracts Used</label>
            <input
              type="number"
              value={contracts}
              onChange={(e) => setContracts(e.target.value)}
              className="w-full p-2 border rounded"
              placeholder="Enter contracts used"
            />
          </div>
        </div>
        <button
          onClick={handleUpdate}
          disabled={isUpdating}
          className="w-full py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-blue-300"
        >
          {isUpdating ? 'Updating...' : 'Update Results'}
        </button>
      </div>
    </div>
  );
};

export default DailyStatsCard;