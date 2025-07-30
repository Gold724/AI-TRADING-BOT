import React from 'react';

interface DailyStatsProps {
  currentDay: number;
  target: number;
  achieved: number;
  drawdownLeft: number;
  mode: string;
}

const DailyStats: React.FC<DailyStatsProps> = ({
  currentDay,
  target,
  achieved,
  drawdownLeft,
  mode
}) => {
  // Calculate progress percentage
  const progressPercentage = Math.min(100, (achieved / target) * 100);
  
  // Determine status
  let status = '⏳ In Progress';
  let statusClass = 'text-yellow-600';
  
  if (achieved >= target) {
    status = '✅ Target Hit';
    statusClass = 'text-green-600';
  } else if (achieved < 0 && Math.abs(achieved) > target * 0.5) {
    status = '⚠️ At Risk';
    statusClass = 'text-red-600';
  } else if (progressPercentage > 75) {
    status = '✅ On Track';
    statusClass = 'text-green-600';
  }

  return (
    <div className="bg-white p-4 rounded shadow">
      <h2 className="text-xl font-semibold mb-2">Sentinel Tracker</h2>
      <div className="border-b pb-2 mb-2">
        <div className="flex justify-between items-center">
          <span className="text-gray-600">Mode:</span>
          <span className="font-semibold">
            {mode === 'fast' ? '🔥 Fast Pass' : '🌱 Safe Growth'}
          </span>
        </div>
      </div>
      <div className="space-y-2">
        <div className="flex justify-between items-center">
          <span className="text-gray-600">Day:</span>
          <span className="font-semibold">
            {currentDay}/{mode === 'fast' ? 7 : 20}
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-600">Target:</span>
          <span className="font-semibold text-blue-600">${target.toFixed(2)}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-600">Achieved:</span>
          <span className={`font-semibold ${achieved >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            ${achieved.toFixed(2)}
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-600">Drawdown Left:</span>
          <span className="font-semibold">${drawdownLeft.toFixed(2)}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-gray-600">Status:</span>
          <span className={`font-semibold ${statusClass}`}>{status}</span>
        </div>
      </div>
      
      {/* Progress bar */}
      <div className="mt-3">
        <div className="w-full bg-gray-200 rounded-full h-2.5">
          <div 
            className={`h-2.5 rounded-full ${achieved >= 0 ? 'bg-blue-600' : 'bg-red-600'}`} 
            style={{ width: `${Math.max(0, progressPercentage)}%` }}
          ></div>
        </div>
        <p className="text-xs text-right mt-1">{progressPercentage.toFixed(1)}%</p>
      </div>
    </div>
  );
};

export default DailyStats;