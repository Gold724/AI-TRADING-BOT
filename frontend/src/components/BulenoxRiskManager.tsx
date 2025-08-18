import React, { useState, useEffect } from 'react';

interface RiskSettings {
  maxDailyLoss: number;
  maxPositionSize: number;
  riskPerTrade: number;
  maxDrawdown: number;
  correlationLimit: number;
  leverageLimit: number;
  stopLossRequired: boolean;
  takeProfitRequired: boolean;
}

interface RiskMetrics {
  currentDrawdown: number;
  dailyPnL: number;
  openPositions: number;
  totalExposure: number;
  riskUtilization: number;
  correlationRisk: number;
}

interface BulenoxRiskManagerProps {
  riskSettings: RiskSettings;
  riskMetrics: RiskMetrics;
  onRiskSettingsChange: (settings: RiskSettings) => void;
  selectedStrategy: 'fast' | 'slow' | 'scalping';
  accountBalance: number;
}

const BulenoxRiskManager: React.FC<BulenoxRiskManagerProps> = ({
  riskSettings,
  riskMetrics,
  onRiskSettingsChange,
  selectedStrategy,
  accountBalance
}) => {
  const [activeTab, setActiveTab] = useState<'settings' | 'metrics' | 'alerts'>('settings');
  const [alerts, setAlerts] = useState<Array<{id: string, type: 'warning' | 'danger', message: string, timestamp: string}>>([]);
  const [showAdvanced, setShowAdvanced] = useState(false);

  // Calculate risk levels and warnings
  useEffect(() => {
    const newAlerts = [];
    
    if (riskMetrics.currentDrawdown > riskSettings.maxDrawdown * 0.8) {
      newAlerts.push({
        id: 'drawdown-warning',
        type: 'warning' as const,
        message: `Approaching maximum drawdown limit (${(riskMetrics.currentDrawdown).toFixed(2)}%)`,
        timestamp: new Date().toISOString()
      });
    }
    
    if (riskMetrics.dailyPnL < -riskSettings.maxDailyLoss * 0.8) {
      newAlerts.push({
        id: 'daily-loss-warning',
        type: 'danger' as const,
        message: `Approaching daily loss limit ($${Math.abs(riskMetrics.dailyPnL).toFixed(2)})`,
        timestamp: new Date().toISOString()
      });
    }
    
    if (riskMetrics.riskUtilization > 80) {
      newAlerts.push({
        id: 'risk-utilization-warning',
        type: 'warning' as const,
        message: `High risk utilization (${riskMetrics.riskUtilization.toFixed(1)}%)`,
        timestamp: new Date().toISOString()
      });
    }
    
    if (riskMetrics.correlationRisk > riskSettings.correlationLimit) {
      newAlerts.push({
        id: 'correlation-warning',
        type: 'warning' as const,
        message: `High correlation risk detected (${riskMetrics.correlationRisk.toFixed(2)})`,
        timestamp: new Date().toISOString()
      });
    }
    
    setAlerts(newAlerts);
  }, [riskMetrics, riskSettings]);

  const handleSettingChange = (key: keyof RiskSettings, value: any) => {
    const newSettings = { ...riskSettings, [key]: value };
    onRiskSettingsChange(newSettings);
  };

  const getRiskColor = (percentage: number) => {
    if (percentage < 50) return 'text-green-600';
    if (percentage < 80) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getRiskBgColor = (percentage: number) => {
    if (percentage < 50) return 'bg-green-100';
    if (percentage < 80) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  const calculatePositionSize = (riskAmount: number, stopLossPips: number, symbolValue: number = 10) => {
    return (riskAmount / (stopLossPips * symbolValue)).toFixed(2);
  };

  const getStrategyRiskProfile = (strategy: 'fast' | 'slow' | 'scalping') => {
    switch (strategy) {
      case 'fast':
        return { risk: 'High', color: 'text-red-600', description: 'Quick trades with higher frequency' };
      case 'slow':
        return { risk: 'Low', color: 'text-green-600', description: 'Conservative long-term positions' };
      case 'scalping':
        return { risk: 'Medium', color: 'text-yellow-600', description: 'Frequent small profit trades' };
    }
  };

  const strategyProfile = getStrategyRiskProfile(selectedStrategy);

  return (
    <div className="space-y-6">
      {/* Risk Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border">
          <h3 className="text-sm font-medium text-gray-600 mb-1">Daily P&L</h3>
          <p className={`text-2xl font-bold ${
            riskMetrics.dailyPnL >= 0 ? 'text-green-600' : 'text-red-600'
          }`}>
            ${riskMetrics.dailyPnL.toFixed(2)}
          </p>
          <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
            <div 
              className={`h-2 rounded-full ${
                riskMetrics.dailyPnL >= 0 ? 'bg-green-500' : 'bg-red-500'
              }`}
              style={{ width: `${Math.min(Math.abs(riskMetrics.dailyPnL) / riskSettings.maxDailyLoss * 100, 100)}%` }}
            ></div>
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg border">
          <h3 className="text-sm font-medium text-gray-600 mb-1">Drawdown</h3>
          <p className={`text-2xl font-bold ${getRiskColor((riskMetrics.currentDrawdown / riskSettings.maxDrawdown) * 100)}`}>
            {riskMetrics.currentDrawdown.toFixed(2)}%
          </p>
          <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
            <div 
              className={`h-2 rounded-full ${getRiskBgColor((riskMetrics.currentDrawdown / riskSettings.maxDrawdown) * 100).replace('bg-', 'bg-').replace('-100', '-500')}`}
              style={{ width: `${(riskMetrics.currentDrawdown / riskSettings.maxDrawdown) * 100}%` }}
            ></div>
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg border">
          <h3 className="text-sm font-medium text-gray-600 mb-1">Risk Utilization</h3>
          <p className={`text-2xl font-bold ${getRiskColor(riskMetrics.riskUtilization)}`}>
            {riskMetrics.riskUtilization.toFixed(1)}%
          </p>
          <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
            <div 
              className={`h-2 rounded-full ${getRiskBgColor(riskMetrics.riskUtilization).replace('bg-', 'bg-').replace('-100', '-500')}`}
              style={{ width: `${riskMetrics.riskUtilization}%` }}
            ></div>
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg border">
          <h3 className="text-sm font-medium text-gray-600 mb-1">Open Positions</h3>
          <p className="text-2xl font-bold text-blue-600">{riskMetrics.openPositions}</p>
          <p className="text-xs text-gray-500">
            Exposure: ${riskMetrics.totalExposure.toFixed(0)}
          </p>
        </div>
      </div>

      {/* Strategy Risk Profile */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-4 rounded-lg border">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">Current Strategy: {selectedStrategy.toUpperCase()}</h3>
            <p className="text-gray-600">{strategyProfile.description}</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-600">Risk Level</p>
            <p className={`text-xl font-bold ${strategyProfile.color}`}>{strategyProfile.risk}</p>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {(['settings', 'metrics', 'alerts'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
              {tab === 'alerts' && alerts.length > 0 && (
                <span className="ml-2 bg-red-500 text-white text-xs rounded-full px-2 py-1">
                  {alerts.length}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'settings' && (
        <div className="bg-white rounded-lg border p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-lg font-semibold">Risk Management Settings</h3>
            <button
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="bg-gray-100 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-200"
            >
              {showAdvanced ? 'Hide Advanced' : 'Show Advanced'}
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Basic Settings */}
            <div className="space-y-4">
              <h4 className="font-semibold text-gray-800">Basic Risk Controls</h4>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max Daily Loss ($)
                </label>
                <input
                  type="number"
                  value={riskSettings.maxDailyLoss}
                  onChange={(e) => handleSettingChange('maxDailyLoss', Number(e.target.value))}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Risk Per Trade (%)
                </label>
                <input
                  type="number"
                  min="0.1"
                  max="10"
                  step="0.1"
                  value={riskSettings.riskPerTrade}
                  onChange={(e) => handleSettingChange('riskPerTrade', Number(e.target.value))}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max Position Size (lots)
                </label>
                <input
                  type="number"
                  min="0.01"
                  step="0.01"
                  value={riskSettings.maxPositionSize}
                  onChange={(e) => handleSettingChange('maxPositionSize', Number(e.target.value))}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>

            {/* Advanced Settings */}
            <div className="space-y-4">
              <h4 className="font-semibold text-gray-800">Advanced Controls</h4>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Max Drawdown (%)
                </label>
                <input
                  type="number"
                  min="1"
                  max="50"
                  value={riskSettings.maxDrawdown}
                  onChange={(e) => handleSettingChange('maxDrawdown', Number(e.target.value))}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Correlation Limit
                </label>
                <input
                  type="number"
                  min="0.1"
                  max="1"
                  step="0.1"
                  value={riskSettings.correlationLimit}
                  onChange={(e) => handleSettingChange('correlationLimit', Number(e.target.value))}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Leverage Limit
                </label>
                <input
                  type="number"
                  min="1"
                  max="500"
                  value={riskSettings.leverageLimit}
                  onChange={(e) => handleSettingChange('leverageLimit', Number(e.target.value))}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
          </div>

          {showAdvanced && (
            <div className="mt-6 pt-6 border-t">
              <h4 className="font-semibold text-gray-800 mb-4">Trade Requirements</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={riskSettings.stopLossRequired}
                    onChange={(e) => handleSettingChange('stopLossRequired', e.target.checked)}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                  />
                  <label className="text-sm font-medium text-gray-700">
                    Require Stop Loss on all trades
                  </label>
                </div>
                
                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={riskSettings.takeProfitRequired}
                    onChange={(e) => handleSettingChange('takeProfitRequired', e.target.checked)}
                    className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                  />
                  <label className="text-sm font-medium text-gray-700">
                    Require Take Profit on all trades
                  </label>
                </div>
              </div>
            </div>
          )}

          {/* Position Size Calculator */}
          <div className="mt-6 pt-6 border-t">
            <h4 className="font-semibold text-gray-800 mb-4">Position Size Calculator</h4>
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Account Balance:</span>
                  <span className="ml-2 font-semibold">${accountBalance.toFixed(2)}</span>
                </div>
                <div>
                  <span className="text-gray-600">Risk Amount:</span>
                  <span className="ml-2 font-semibold">
                    ${(accountBalance * riskSettings.riskPerTrade / 100).toFixed(2)}
                  </span>
                </div>
                <div>
                  <span className="text-gray-600">Suggested Lot Size (20 pips SL):</span>
                  <span className="ml-2 font-semibold">
                    {calculatePositionSize(accountBalance * riskSettings.riskPerTrade / 100, 20)} lots
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'metrics' && (
        <div className="bg-white rounded-lg border p-6">
          <h3 className="text-lg font-semibold mb-6">Risk Metrics Dashboard</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <h4 className="font-semibold text-gray-800">Current Risk Status</h4>
              
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                  <span>Daily Loss Limit Usage</span>
                  <span className={getRiskColor(Math.abs(riskMetrics.dailyPnL) / riskSettings.maxDailyLoss * 100)}>
                    {((Math.abs(riskMetrics.dailyPnL) / riskSettings.maxDailyLoss) * 100).toFixed(1)}%
                  </span>
                </div>
                
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                  <span>Drawdown vs Limit</span>
                  <span className={getRiskColor((riskMetrics.currentDrawdown / riskSettings.maxDrawdown) * 100)}>
                    {((riskMetrics.currentDrawdown / riskSettings.maxDrawdown) * 100).toFixed(1)}%
                  </span>
                </div>
                
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                  <span>Position Correlation</span>
                  <span className={getRiskColor((riskMetrics.correlationRisk / riskSettings.correlationLimit) * 100)}>
                    {riskMetrics.correlationRisk.toFixed(2)}
                  </span>
                </div>
              </div>
            </div>
            
            <div className="space-y-4">
              <h4 className="font-semibold text-gray-800">Portfolio Exposure</h4>
              
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                  <span>Total Exposure</span>
                  <span className="font-semibold">${riskMetrics.totalExposure.toFixed(2)}</span>
                </div>
                
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                  <span>Exposure vs Balance</span>
                  <span className={getRiskColor((riskMetrics.totalExposure / accountBalance) * 100)}>
                    {((riskMetrics.totalExposure / accountBalance) * 100).toFixed(1)}%
                  </span>
                </div>
                
                <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
                  <span>Available Risk Capital</span>
                  <span className="font-semibold text-green-600">
                    ${(accountBalance * (riskSettings.riskPerTrade / 100) * (10 - riskMetrics.openPositions)).toFixed(2)}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'alerts' && (
        <div className="bg-white rounded-lg border p-6">
          <h3 className="text-lg font-semibold mb-6">Risk Alerts & Warnings</h3>
          
          {alerts.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <div className="text-4xl mb-2">✅</div>
              <p>No active risk alerts. All systems operating within safe parameters.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {alerts.map((alert) => (
                <div
                  key={alert.id}
                  className={`p-4 rounded-lg border-l-4 ${
                    alert.type === 'danger'
                      ? 'bg-red-50 border-red-500 text-red-800'
                      : 'bg-yellow-50 border-yellow-500 text-yellow-800'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <span className="text-lg">
                        {alert.type === 'danger' ? '🚨' : '⚠️'}
                      </span>
                      <span className="font-medium">{alert.message}</span>
                    </div>
                    <span className="text-xs opacity-75">
                      {new Date(alert.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default BulenoxRiskManager;