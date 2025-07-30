import React, { useState, useEffect } from 'react';
import DailyStatsCard from './DailyStatsCard';
import ContractMeter from './ContractMeter';

interface DayData {
  day: number;
  daily_target: number;
  actual_pnl: number;
  suggested_contracts: number;
  trades: Array<{
    pnl: number;
    contracts: number;
    timestamp: string;
  }>;
  status: 'in_progress' | 'target_hit' | 'overdrawn';
  date: string;
}

interface Summary {
  account_id: string;
  current_day: number;
  total_pnl: number;
  remaining_drawdown: number;
  progress_percentage: number;
  completed_days: number;
  overdrawn_days: number;
  total_days: number;
  last_updated: string;
}

const CompoundingTracker: React.FC = () => {
  const [days, setDays] = useState<DayData[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDay, setSelectedDay] = useState<number | null>(null);
  const [tradePlan, setTradePlan] = useState<any>(null);
  const [perTradeTarget, setPerTradeTarget] = useState<number | null>(null);

  // Fetch all days data
  const fetchDays = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/progress/track');
      const result = await response.json();
      
      if (result.status === 'success') {
        setDays(result.data);
        // Set selected day to current day if not already set
        if (!selectedDay && result.data.length > 0) {
          const currentDay = Math.max(...result.data.map((d: DayData) => d.day));
          setSelectedDay(currentDay);
          fetchTradePlan(currentDay);
        }
      } else {
        setError('Failed to load days data');
      }
    } catch (err) {
      setError('Error connecting to server');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch summary data
  const fetchSummary = async () => {
    try {
      const response = await fetch('/api/progress/summary');
      const result = await response.json();
      
      if (result.status === 'success') {
        setSummary(result.data);
      } else {
        console.error('Failed to load summary');
      }
    } catch (err) {
      console.error('Error fetching summary:', err);
    }
  };

  // Fetch trade plan for a specific day with specified number of trades
  const fetchTradePlan = async (day: number, numTrades: number = 4) => {
    try {
      const response = await fetch(`/api/daily-plan?day=${day}&num_trades=${numTrades}`);
      const result = await response.json();
      
      if (result.status === 'success') {
        setTradePlan(result.data);
        // No need to fetch per-trade target separately as it's included in the trade plan
        setPerTradeTarget(result.data.per_trade_target);
      }
    } catch (err) {
      console.error('Error fetching trade plan:', err);
    }
  };
  
  // Fetch per-trade target for a given daily target (kept for backward compatibility)
  const fetchPerTradeTarget = async (dailyTarget: number) => {
    try {
      const response = await fetch(`/api/per-trade-targets?daily_target=${dailyTarget}&num_trades=3`);
      const result = await response.json();
      
      if (result.status === 'success') {
        setPerTradeTarget(result.data.per_trade_target);
      }
    } catch (err) {
      console.error('Error fetching per-trade target:', err);
    }
  };

  // Reset a day's data
  const resetDay = async (day: number) => {
    try {
      const response = await fetch('/api/progress/reset', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ day }),
      });
      
      const result = await response.json();
      
      if (result.status === 'success') {
        // Refresh data
        fetchDays();
        fetchSummary();
        fetchTradePlan(day);
      } else {
        setError('Failed to reset day');
      }
    } catch (err) {
      setError('Error connecting to server');
      console.error(err);
    }
  };

  // Advance to next day
  const advanceDay = async () => {
    try {
      const response = await fetch('/api/progress/advance', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      const result = await response.json();
      
      if (result.status === 'success') {
        // Refresh data and select the new day
        await fetchDays();
        await fetchSummary();
        if (result.data && result.data.day) {
          setSelectedDay(result.data.day);
          fetchTradePlan(result.data.day);
        }
      } else {
        setError('Failed to advance day');
      }
    } catch (err) {
      setError('Error connecting to server');
      console.error(err);
    }
  };

  // Load data on component mount
  useEffect(() => {
    fetchDays();
    fetchSummary();
  }, []);

  // When selected day changes, fetch trade plan
  useEffect(() => {
    if (selectedDay) {
      // Default to 4 trades as specified in the user's example
      fetchTradePlan(selectedDay, 4);
    }
  }, [selectedDay]);

  if (loading && !days.length) {
    return <div className="p-4">Loading compounding tracker data...</div>;
  }

  if (error) {
    return <div className="p-4 text-red-600">{error}</div>;
  }

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold mb-4">Compounding Tracker</h1>
      
      {/* Summary Section */}
      {summary && (
        <div className="bg-white p-4 rounded shadow mb-6">
          <h2 className="text-xl font-semibold mb-2">Progress Summary</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-gray-600">Account ID</p>
              <p className="font-semibold">{summary.account_id}</p>
            </div>
            <div>
              <p className="text-gray-600">Current Day</p>
              <p className="font-semibold">{summary.current_day}</p>
            </div>
            <div>
              <p className="text-gray-600">Total P&L</p>
              <p className={`font-semibold ${summary.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                ${summary.total_pnl.toFixed(2)}
              </p>
            </div>
            <div>
              <p className="text-gray-600">Remaining Drawdown</p>
              <p className="font-semibold">${summary.remaining_drawdown.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-gray-600">Progress</p>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div 
                  className="bg-blue-600 h-2.5 rounded-full" 
                  style={{ width: `${summary.progress_percentage}%` }}
                ></div>
              </div>
              <p className="text-sm mt-1">{summary.progress_percentage.toFixed(1)}% of $15,000 target</p>
            </div>
            <div>
              <p className="text-gray-600">Days</p>
              <p className="font-semibold">
                {summary.completed_days} completed, {summary.overdrawn_days} overdrawn
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Trade Plan Section */}
      {tradePlan && selectedDay && (
        <div className="bg-white p-4 rounded shadow mb-6">
          <h2 className="text-xl font-semibold mb-2">Day {selectedDay} Trade Plan</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-gray-600">Daily Target</p>
              <p className="font-semibold">${tradePlan.daily_target.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-gray-600">Suggested Contracts</p>
              <ContractMeter value={tradePlan.suggested_contracts} max={25} />
            </div>
            <div>
              <p className="text-gray-600">Trades</p>
              <p className="font-semibold">{tradePlan.trades_taken} taken / {tradePlan.trades_remaining} remaining</p>
            </div>
            <div>
              <p className="text-gray-600">Per-Trade Target ({tradePlan.trades_planned} trades)</p>
              <p className="font-semibold text-blue-600">${tradePlan.per_trade_target.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-gray-600">Recommended SL</p>
              <p className="font-semibold text-red-600">${tradePlan.recommended_sl.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-gray-600">Recommended TP</p>
              <p className="font-semibold text-green-600">${tradePlan.recommended_tp.toFixed(2)}</p>
            </div>
            <div>
              <p className="text-gray-600">Max Daily Loss</p>
              <p className="font-semibold text-red-600">${tradePlan.max_daily_loss.toFixed(2)}</p>
            </div>
          </div>
        </div>
      )}

      {/* Day Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">Select Day:</label>
        <div className="flex flex-wrap gap-2">
          {Array.from({ length: 20 }, (_, i) => i + 1).map(day => {
            const dayData = days.find(d => d.day === day);
            let statusClass = 'bg-gray-200'; // default for days not started
            
            if (dayData) {
              if (dayData.status === 'target_hit') statusClass = 'bg-green-200 border-green-500';
              else if (dayData.status === 'overdrawn') statusClass = 'bg-red-200 border-red-500';
              else statusClass = 'bg-yellow-200 border-yellow-500'; // in progress
            }
            
            return (
              <button
                key={day}
                className={`w-10 h-10 flex items-center justify-center rounded border ${statusClass} ${selectedDay === day ? 'ring-2 ring-blue-500' : ''}`}
                onClick={() => setSelectedDay(day)}
              >
                {day}
              </button>
            );
          })}
        </div>
      </div>

      {/* Selected Day Details */}
      {selectedDay && (
        <div className="mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold">Day {selectedDay} Details</h2>
            <div className="space-x-2">
              <button 
                onClick={() => resetDay(selectedDay)}
                className="px-3 py-1 bg-yellow-500 text-white rounded hover:bg-yellow-600"
              >
                Reset Day
              </button>
              {selectedDay === summary?.current_day && (
                <button 
                  onClick={advanceDay}
                  className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
                >
                  Advance to Next Day
                </button>
              )}
            </div>
          </div>
          
          {/* Day Stats Card */}
          {days.find(d => d.day === selectedDay) ? (
            <DailyStatsCard dayData={days.find(d => d.day === selectedDay)!} onReset={() => resetDay(selectedDay)} />
          ) : (
            <div className="bg-white p-4 rounded shadow">
              <p>Day {selectedDay} has not been started yet.</p>
              {tradePlan && (
                <div className="mt-2">
                  <p>Target: ${tradePlan.daily_target.toFixed(2)}</p>
                  <p>Suggested Contracts: {tradePlan.suggested_contracts}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default CompoundingTracker;