import React, { useState } from 'react';

interface StrategyConfig {
  name: string;
  description: string;
  timeframe: string;
  riskLevel: number;
  maxPositions: number;
  stopLoss: number;
  takeProfit: number;
  lotSize: number;
  enabled: boolean;
}

interface BulenoxStrategySelectorProps {
  selectedStrategy: 'fast' | 'slow' | 'scalping';
  onStrategyChange: (strategy: 'fast' | 'slow' | 'scalping') => void;
  onConfigUpdate: (strategy: 'fast' | 'slow' | 'scalping', config: StrategyConfig) => void;
}

const BulenoxStrategySelector: React.FC<BulenoxStrategySelectorProps> = ({
  selectedStrategy,
  onStrategyChange,
  onConfigUpdate
}) => {
  const [configs, setConfigs] = useState<Record<'fast' | 'slow' | 'scalping', StrategyConfig>>({
    fast: {
      name: 'Fast Trading',
      description: 'Quick scalping with high frequency trades',
      timeframe: '1m-5m',
      riskLevel: 3,
      maxPositions: 5,
      stopLoss: 10,
      takeProfit: 15,
      lotSize: 0.01,
      enabled: true
    },
    slow: {
      name: 'Slow Trading',
      description: 'Conservative swing trading approach',
      timeframe: '1h-4h',
      riskLevel: 1,
      maxPositions: 2,
      stopLoss: 50,
      takeProfit: 100,
      lotSize: 0.05,
      enabled: true
    },
    scalping: {
      name: 'Scalping',
      description: 'Ultra-fast micro trades for small profits',
      timeframe: '15s-1m',
      riskLevel: 2,
      maxPositions: 10,
      stopLoss: 5,
      takeProfit: 8,
      lotSize: 0.01,
      enabled: true
    }
  });

  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleConfigChange = (field: keyof StrategyConfig, value: any) => {
    const newConfig = {
      ...configs[selectedStrategy],
      [field]: value
    };
    
    setConfigs(prev => ({
      ...prev,
      [selectedStrategy]: newConfig
    }));
    
    onConfigUpdate(selectedStrategy, newConfig);
  };

  const getStrategyIcon = (strategy: 'fast' | 'slow' | 'scalping') => {
    switch (strategy) {
      case 'fast': return '⚡';
      case 'slow': return '🐢';
      case 'scalping': return '🎯';
    }
  };

  const getStrategyColor = (strategy: 'fast' | 'slow' | 'scalping') => {
    switch (strategy) {
      case 'fast': return 'border-red-500 bg-red-50';
      case 'slow': return 'border-blue-500 bg-blue-50';
      case 'scalping': return 'border-green-500 bg-green-50';
    }
  };

  const getRiskColor = (level: number) => {
    switch (level) {
      case 1: return 'text-green-600';
      case 2: return 'text-yellow-600';
      case 3: return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getRiskLabel = (level: number) => {
    switch (level) {
      case 1: return 'Low Risk';
      case 2: return 'Medium Risk';
      case 3: return 'High Risk';
      default: return 'Unknown';
    }
  };

  const currentConfig = configs[selectedStrategy];

  return (
    <div className="space-y-6">
      {/* Strategy Selection Cards */}
      <div>
        <h3 className="text-lg font-semibold text-gray-800 mb-4">Select Trading Strategy</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {(['fast', 'slow', 'scalping'] as const).map((strategy) => {
            const config = configs[strategy];
            const isSelected = selectedStrategy === strategy;
            
            return (
              <div
                key={strategy}
                onClick={() => onStrategyChange(strategy)}
                className={`p-4 rounded-lg border-2 cursor-pointer transition-all hover:shadow-md ${
                  isSelected 
                    ? getStrategyColor(strategy) + ' shadow-md'
                    : 'border-gray-200 bg-white hover:border-gray-300'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-2xl">{getStrategyIcon(strategy)}</span>
                    <h4 className="font-semibold">{config.name}</h4>
                  </div>
                  {config.enabled && (
                    <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
                  )}
                </div>
                
                <p className="text-sm text-gray-600 mb-3">{config.description}</p>
                
                <div className="space-y-1 text-xs">
                  <div className="flex justify-between">
                    <span>Timeframe:</span>
                    <span className="font-mono">{config.timeframe}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Risk Level:</span>
                    <span className={`font-semibold ${getRiskColor(config.riskLevel)}`}>
                      {getRiskLabel(config.riskLevel)}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Max Positions:</span>
                    <span className="font-semibold">{config.maxPositions}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Selected Strategy Configuration */}
      <div className="bg-white rounded-lg border p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <span className="text-3xl">{getStrategyIcon(selectedStrategy)}</span>
            <div>
              <h3 className="text-xl font-semibold">{currentConfig.name} Configuration</h3>
              <p className="text-gray-600">{currentConfig.description}</p>
            </div>
          </div>
          <button
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200 transition-colors"
          >
            {showAdvanced ? 'Hide Advanced' : 'Show Advanced'}
          </button>
        </div>

        {/* Basic Configuration */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Strategy Enabled</label>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={currentConfig.enabled}
                onChange={(e) => handleConfigChange('enabled', e.target.checked)}
                className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
              />
              <span className={`text-sm font-medium ${
                currentConfig.enabled ? 'text-green-600' : 'text-gray-500'
              }`}>
                {currentConfig.enabled ? 'Active' : 'Inactive'}
              </span>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Risk Level</label>
            <select
              value={currentConfig.riskLevel}
              onChange={(e) => handleConfigChange('riskLevel', Number(e.target.value))}
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            >
              <option value={1}>Low Risk</option>
              <option value={2}>Medium Risk</option>
              <option value={3}>High Risk</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Max Positions</label>
            <input
              type="number"
              min="1"
              max="20"
              value={currentConfig.maxPositions}
              onChange={(e) => handleConfigChange('maxPositions', Number(e.target.value))}
              className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
        </div>

        {/* Advanced Configuration */}
        {showAdvanced && (
          <div className="border-t pt-6">
            <h4 className="text-lg font-semibold mb-4">Advanced Settings</h4>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Stop Loss (pips)</label>
                <input
                  type="number"
                  min="1"
                  max="200"
                  value={currentConfig.stopLoss}
                  onChange={(e) => handleConfigChange('stopLoss', Number(e.target.value))}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Take Profit (pips)</label>
                <input
                  type="number"
                  min="1"
                  max="500"
                  value={currentConfig.takeProfit}
                  onChange={(e) => handleConfigChange('takeProfit', Number(e.target.value))}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Lot Size</label>
                <input
                  type="number"
                  min="0.01"
                  max="10"
                  step="0.01"
                  value={currentConfig.lotSize}
                  onChange={(e) => handleConfigChange('lotSize', Number(e.target.value))}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Timeframe</label>
                <input
                  type="text"
                  value={currentConfig.timeframe}
                  onChange={(e) => handleConfigChange('timeframe', e.target.value)}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                  placeholder="e.g., 1m-5m"
                />
              </div>
            </div>

            {/* Risk/Reward Ratio Display */}
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <h5 className="font-semibold mb-2">Risk/Reward Analysis</h5>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Risk/Reward Ratio:</span>
                  <span className="ml-2 font-semibold">
                    1:{(currentConfig.takeProfit / currentConfig.stopLoss).toFixed(2)}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Max Risk per Trade:</span>
                  <span className="ml-2 font-semibold">
                    ${(currentConfig.lotSize * currentConfig.stopLoss * 10).toFixed(2)}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Max Profit per Trade:</span>
                  <span className="ml-2 font-semibold text-green-600">
                    ${(currentConfig.lotSize * currentConfig.takeProfit * 10).toFixed(2)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex space-x-3 mt-6">
          <button className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors">
            Save Configuration
          </button>
          <button className="bg-gray-200 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-300 transition-colors">
            Reset to Default
          </button>
          <button className="bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors">
            Test Strategy
          </button>
        </div>
      </div>

      {/* Strategy Performance Preview */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-6 border">
        <h4 className="text-lg font-semibold mb-4">Strategy Performance Metrics</h4>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-blue-600">85%</p>
            <p className="text-sm text-gray-600">Win Rate</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-green-600">+12.5%</p>
            <p className="text-sm text-gray-600">Monthly Return</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-purple-600">1.8</p>
            <p className="text-sm text-gray-600">Avg R/R Ratio</p>
          </div>
          <div className="text-center">
            <p className="text-2xl font-bold text-orange-600">156</p>
            <p className="text-sm text-gray-600">Trades/Month</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BulenoxStrategySelector;