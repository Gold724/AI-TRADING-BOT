import React, { useState, useEffect } from 'react';
import BulenoxTimeTable from './BulenoxTimeTable';
import BulenoxStrategySelector from './BulenoxStrategySelector';
import BulenoxPositionManager from './BulenoxPositionManager';
import BulenoxRiskManager from './BulenoxRiskManager';
import BulenoxMarketHours from './BulenoxMarketHours';
import BulenoxPerformanceTracker from './BulenoxPerformanceTracker';

interface BulenoxTradingPanelProps {
  onTradeExecute?: (tradeData: any) => void;
}

interface TradingSession {
  id: string;
  name: string;
  startTime: string;
  endTime: string;
  strategy: 'fast' | 'slow' | 'scalping';
  isActive: boolean;
  symbol: string;
  riskLevel: number;
}

interface Position {
  id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  entryPrice: number;
  currentPrice: number;
  stopLoss: number;
  takeProfit: number;
  pnl: number;
  timestamp: string;
}

const BulenoxTradingPanel: React.FC<BulenoxTradingPanelProps> = ({ onTradeExecute }) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'timetable' | 'positions' | 'performance'>('overview');
  const [selectedStrategy, setSelectedStrategy] = useState<'fast' | 'slow' | 'scalping'>('fast');
  const [tradingSessions, setTradingSessions] = useState<TradingSession[]>([
    {
      id: '1',
      name: 'London Session - Fast',
      startTime: '08:00',
      endTime: '12:00',
      strategy: 'fast',
      isActive: true,
      symbol: 'EURUSD',
      riskLevel: 2
    },
    {
      id: '2',
      name: 'New York Session - Scalping',
      startTime: '13:00',
      endTime: '17:00',
      strategy: 'scalping',
      isActive: false,
      symbol: 'GBPUSD',
      riskLevel: 1
    },
    {
      id: '3',
      name: 'Asian Session - Slow',
      startTime: '22:00',
      endTime: '06:00',
      strategy: 'slow',
      isActive: false,
      symbol: 'USDJPY',
      riskLevel: 3
    }
  ]);
  
  const [positions, setPositions] = useState<Position[]>([]);
  const [isAutoTradingEnabled, setIsAutoTradingEnabled] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting'>('disconnected');
  const [accountBalance, setAccountBalance] = useState(10000);
  
  // Risk management state
  const [riskSettings, setRiskSettings] = useState({
    maxDailyLoss: 500,
    maxPositionSize: 1000,
    riskPerTrade: 2,
    maxDrawdown: 10,
    correlationLimit: 0.7,
    leverageLimit: 10,
    stopLossRequired: true,
    takeProfitRequired: false
  });
  
  const [riskMetrics, setRiskMetrics] = useState({
    currentDrawdown: 2.5,
    dailyPnL: 150,
    openPositions: positions.length,
    totalExposure: 2500,
    riskUtilization: 25,
    correlationRisk: 0.3
  });

  // Strategy configurations
  const strategyConfigs = {
    fast: {
      name: 'Fast Trading',
      description: 'Quick entries and exits, 1-5 minute timeframes',
      maxPositions: 3,
      riskPerTrade: 1,
      timeframe: '1m',
      color: 'bg-red-500'
    },
    slow: {
      name: 'Slow Trading',
      description: 'Longer-term positions, 15-60 minute timeframes',
      maxPositions: 2,
      riskPerTrade: 2,
      timeframe: '15m',
      color: 'bg-blue-500'
    },
    scalping: {
      name: 'Scalping',
      description: 'Ultra-fast trades, seconds to minutes',
      maxPositions: 5,
      riskPerTrade: 0.5,
      timeframe: '15s',
      color: 'bg-green-500'
    }
  };

  useEffect(() => {
    // Simulate connection status
    const interval = setInterval(() => {
      setConnectionStatus(prev => {
        if (prev === 'disconnected') return 'connecting';
        if (prev === 'connecting') return 'connected';
        return 'connected';
      });
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const handleStrategyChange = (strategy: 'fast' | 'slow' | 'scalping') => {
    setSelectedStrategy(strategy);
  };

  const handleRiskSettingsChange = (settings: typeof riskSettings) => {
    setRiskSettings(settings);
  };

  const handleClosePosition = (positionId: string) => {
    setPositions(prev => prev.filter(pos => pos.id !== positionId));
    console.log('Position closed:', positionId);
  };

  const handleModifyPosition = (positionId: string, stopLoss: number, takeProfit: number) => {
    setPositions(prev => prev.map(pos => 
      pos.id === positionId 
        ? { ...pos, stopLoss, takeProfit }
        : pos
    ));
    console.log('Position modified:', positionId, { stopLoss, takeProfit });
  };

  const handleSessionToggle = (sessionId: string) => {
    setTradingSessions(prev => 
      prev.map(session => 
        session.id === sessionId 
          ? { ...session, isActive: !session.isActive }
          : session
      )
    );
  };

  const handleTradeExecution = (tradeData: any) => {
    const newPosition: Position = {
      id: Date.now().toString(),
      symbol: tradeData.symbol,
      side: tradeData.side,
      quantity: tradeData.quantity,
      entryPrice: tradeData.price,
      currentPrice: tradeData.price,
      pnl: 0,
      timestamp: new Date().toISOString()
    };
    
    setPositions(prev => [...prev, newPosition]);
    onTradeExecute?.(tradeData);
  };

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'text-green-600';
      case 'connecting': return 'text-yellow-600';
      case 'disconnected': return 'text-red-600';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">Bulenox Trading Panel</h2>
          <p className="text-gray-600">Advanced trading automation for Bulenox platform</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className={`flex items-center space-x-2 ${getConnectionStatusColor()}`}>
            <div className={`w-3 h-3 rounded-full ${
              connectionStatus === 'connected' ? 'bg-green-500' :
              connectionStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' :
              'bg-red-500'
            }`}></div>
            <span className="font-medium capitalize">{connectionStatus}</span>
          </div>
          <button
            onClick={() => setIsAutoTradingEnabled(!isAutoTradingEnabled)}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              isAutoTradingEnabled 
                ? 'bg-green-600 text-white hover:bg-green-700' 
                : 'bg-gray-300 text-gray-700 hover:bg-gray-400'
            }`}
          >
            Auto Trading: {isAutoTradingEnabled ? 'ON' : 'OFF'}
          </button>
        </div>
      </div>

      {/* Strategy Selector */}
      <BulenoxStrategySelector
        selectedStrategy={selectedStrategy}
        onStrategyChange={handleStrategyChange}
        onConfigUpdate={(strategy, config) => {
          console.log('Strategy config updated:', strategy, config);
          // Handle strategy configuration updates here
        }}
      />

      {/* Navigation Tabs */}
      <div className="flex space-x-1 mb-6 bg-gray-100 p-1 rounded-lg">
        {[
          { id: 'overview', label: 'Overview' },
          { id: 'timetable', label: 'Time Table' },
          { id: 'positions', label: 'Positions' },
          { id: 'performance', label: 'Performance' }
        ].map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id as any)}
            className={`flex-1 py-2 px-4 rounded-md font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-white text-blue-600 shadow-sm'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="min-h-[400px]">
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <BulenoxMarketHours 
              selectedStrategy={selectedStrategy}
              onStrategyOptimization={(recommendations) => {
                console.log('Strategy optimization recommendations:', recommendations);
                // Handle strategy optimization recommendations here
              }}
            />
            <BulenoxRiskManager 
              riskSettings={riskSettings}
              riskMetrics={riskMetrics}
              onRiskSettingsChange={handleRiskSettingsChange}
              selectedStrategy={selectedStrategy}
              accountBalance={accountBalance}
            />
          </div>
        )}

        {activeTab === 'timetable' && (
          <BulenoxTimeTable
            sessions={tradingSessions}
            onSessionToggle={handleSessionToggle}
            selectedStrategy={selectedStrategy}
          />
        )}

        {activeTab === 'positions' && (
          <BulenoxPositionManager
            positions={positions}
            onClosePosition={handleClosePosition}
            onModifyPosition={handleModifyPosition}
            selectedStrategy={selectedStrategy}
          />
        )}

        {activeTab === 'performance' && (
          <BulenoxPerformanceTracker
            selectedStrategy={selectedStrategy}
            positions={positions}
          />
        )}
      </div>
    </div>
  );
};

export default BulenoxTradingPanel;