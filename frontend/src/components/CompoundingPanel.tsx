import React, { useState, useEffect } from 'react';
import ModeSelector from './ModeSelector';
import DailyStats from './DailyStats';

interface CompoundingPanelProps {
  className?: string;
}

const CompoundingPanel: React.FC<CompoundingPanelProps> = ({ className = '' }) => {
  const [mode, setMode] = useState<string>('safe'); // Default to safe mode
  const [summary, setSummary] = useState<any>(null);
  const [currentDay, setCurrentDay] = useState<number>(1);
  const [targetProfit, setTargetProfit] = useState<number>(0);
  const [currentProfit, setCurrentProfit] = useState<number>(0);
  const [drawdownRemaining, setDrawdownRemaining] = useState<number>(5500); // Default max drawdown
  const [loading, setLoading] = useState<boolean>(true);

  // Fast Pass Mode daily targets
  const fastPassTargets: { [key: number]: number } = {
    1: 1000,
    2: 1000,
    3: 1500,
    4: 2000,
    5: 2500,
    6: 3500,
    7: 3500
  };

  // Safe Growth Mode daily targets
  const safeGrowthTargets: { [key: number]: number } = {
    1: 50,
    2: 55,
    3: 91,
    4: 100,
    5: 110,
    6: 120,
    7: 130,
    8: 140,
    9: 150,
    10: 200,
    11: 220,
    12: 240,
    13: 260,
    14: 280,
    15: 300,
    16: 350,
    17: 400,
    18: 450,
    19: 500,
    20: 2500
  };

  // Fetch summary data
  const fetchSummary = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/progress/summary');
      const result = await response.json();
      
      if (result.status === 'success') {
        setSummary(result.data);
        setCurrentDay(result.data.current_day);
        setCurrentProfit(result.data.total_pnl);
        setDrawdownRemaining(result.data.remaining_drawdown);
        
        // Set target based on current mode and day
        updateTargetProfit(mode, result.data.current_day);
      }
    } catch (err) {
      console.error('Error fetching summary:', err);
    } finally {
      setLoading(false);
    }
  };

  // Update target profit based on mode and day
  const updateTargetProfit = (currentMode: string, day: number) => {
    if (currentMode === 'fast') {
      setTargetProfit(fastPassTargets[day] || 3500); // Default to last day if out of range
    } else {
      setTargetProfit(safeGrowthTargets[day] || 2500); // Default to last day if out of range
    }
  };

  // Handle mode change
  const handleModeChange = (newMode: string) => {
    setMode(newMode);
    updateTargetProfit(newMode, currentDay);
    
    // Send mode to backend
    updateModeOnBackend(newMode);
  };

  // Update mode on backend
  const updateModeOnBackend = async (newMode: string) => {
    try {
      const response = await fetch('/api/mode', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ mode: newMode }),
      });
      
      const result = await response.json();
      
      if (result.status === 'success') {
        console.log(`Mode updated to ${newMode}`);
        
        // Fetch updated daily plan with the new mode
        fetchSummary();
      } else {
        console.error('Failed to update mode:', result.message);
      }
    } catch (err) {
      console.error('Error updating mode:', err);
    }
  };

  // Load data on component mount
  useEffect(() => {
    fetchSummary();
    
    // Refresh data every 30 seconds
    const interval = setInterval(fetchSummary, 30000);
    return () => clearInterval(interval);
  }, []);

  // Update target when mode changes
  useEffect(() => {
    if (currentDay) {
      updateTargetProfit(mode, currentDay);
    }
  }, [mode, currentDay]);

  if (loading && !summary) {
    return <div className="p-4">Loading tracker data...</div>;
  }

  return (
    <div className={`${className}`}>
      <ModeSelector value={mode} onChange={handleModeChange} />
      <DailyStats
        currentDay={currentDay}
        target={targetProfit}
        achieved={currentProfit}
        drawdownLeft={drawdownRemaining}
        mode={mode}
      />
    </div>
  );
};

export default CompoundingPanel;