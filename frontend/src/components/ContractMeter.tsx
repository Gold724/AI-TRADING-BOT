import React from 'react';

interface ContractMeterProps {
  value: number;
  max: number;
}

const ContractMeter: React.FC<ContractMeterProps> = ({ value, max }) => {
  // Calculate percentage for the meter
  const percentage = (value / max) * 100;
  
  // Determine color based on value
  const getColor = () => {
    if (percentage <= 33) return 'bg-green-500';
    if (percentage <= 66) return 'bg-yellow-500';
    return 'bg-red-500';
  };
  
  // Generate tick marks for the meter
  const ticks = [];
  const tickCount = 5; // Number of ticks to show
  const tickInterval = max / (tickCount - 1);
  
  for (let i = 0; i < tickCount; i++) {
    const tickValue = Math.round(i * tickInterval);
    ticks.push(tickValue);
  }

  return (
    <div className="w-full">
      <div className="flex justify-between items-center">
        <span className="font-semibold text-lg">{value}</span>
        <span className="text-sm text-gray-500">of {max} max</span>
      </div>
      
      {/* Meter bar */}
      <div className="w-full h-2 bg-gray-200 rounded-full mt-1 mb-1">
        <div 
          className={`h-2 rounded-full ${getColor()}`} 
          style={{ width: `${percentage}%` }}
        ></div>
      </div>
      
      {/* Tick marks */}
      <div className="flex justify-between text-xs text-gray-500">
        {ticks.map((tick, index) => (
          <span key={index}>{tick}</span>
        ))}
      </div>
    </div>
  );
};

export default ContractMeter;