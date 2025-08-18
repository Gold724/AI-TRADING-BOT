import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';

interface PerformanceMetrics {
  totalTrades: number;
  winRate: number;
  totalPnL: number;
  avgWin: number;
  avgLoss: number;
  maxDrawdown: number;
  sharpeRatio: number;
  profitFactor: number;
  avgHoldTime: string;
  bestTrade: number;
  worstTrade: number;
}

interface StrategyPerformance {
  strategy: 'fast' | 'slow' | 'scalping';
  metrics: PerformanceMetrics;
  dailyPnL: Array<{date: string; pnl: number; trades: number}>;
  hourlyStats: Array<{hour: number; trades: number; pnl: number; winRate: number}>;
  symbolStats: Array<{symbol: string; trades: number; pnl: number; winRate: number}>;
}

interface BulenoxPerformanceTrackerProps {
  selectedStrategy: 'fast' | 'slow' | 'scalping';
  timeframe: '1D' | '1W' | '1M' | '3M' | 'ALL';
  onExportData: (data: any) => void;
}

const BulenoxPerformanceTracker: React.FC<BulenoxPerformanceTrackerProps> = ({
  selectedStrategy,
  timeframe,
  onExportData
}) => {
  const [activeTab, setActiveTab] = useState<'overview' | 'charts' | 'analysis' | 'comparison'>('overview');
  const [performanceData, setPerformanceData] = useState<StrategyPerformance[]>([]);
  const [loading, setLoading] = useState(false);

  // Mock performance data - in real app, this would come from API
  const mockPerformanceData: StrategyPerformance[] = [
    {
      strategy: 'fast',
      metrics: {
        totalTrades: 245,
        winRate: 68.5,
        totalPnL: 12450.75,
        avgWin: 85.30,
        avgLoss: -42.15,
        maxDrawdown: -1250.00,
        sharpeRatio: 1.85,
        profitFactor: 2.15,
        avgHoldTime: '2h 15m',
        bestTrade: 450.00,
        worstTrade: -180.50
      },
      dailyPnL: [
        {date: '2024-01-15', pnl: 250.50, trades: 12},
        {date: '2024-01-16', pnl: -125.25, trades: 8},
        {date: '2024-01-17', pnl: 380.75, trades: 15},
        {date: '2024-01-18', pnl: 195.30, trades: 10},
        {date: '2024-01-19', pnl: 420.15, trades: 18}
      ],
      hourlyStats: [
        {hour: 8, trades: 15, pnl: 450.25, winRate: 73.3},
        {hour: 9, trades: 22, pnl: 680.50, winRate: 68.2},
        {hour: 10, trades: 18, pnl: 320.75, winRate: 61.1},
        {hour: 13, trades: 35, pnl: 1250.00, winRate: 77.1},
        {hour: 14, trades: 28, pnl: 890.25, winRate: 71.4}
      ],
      symbolStats: [
        {symbol: 'EURUSD', trades: 85, pnl: 4250.50, winRate: 72.9},
        {symbol: 'GBPUSD', trades: 62, pnl: 3180.25, winRate: 66.1},
        {symbol: 'USDJPY', trades: 48, pnl: 2890.75, winRate: 64.6},
        {symbol: 'AUDUSD', trades: 35, pnl: 1580.25, winRate: 68.6}
      ]
    },
    {
      strategy: 'slow',
      metrics: {
        totalTrades: 89,
        winRate: 74.2,
        totalPnL: 8950.25,
        avgWin: 185.50,
        avgLoss: -78.25,
        maxDrawdown: -850.00,
        sharpeRatio: 2.15,
        profitFactor: 2.85,
        avgHoldTime: '8h 45m',
        bestTrade: 680.00,
        worstTrade: -220.75
      },
      dailyPnL: [
        {date: '2024-01-15', pnl: 180.25, trades: 3},
        {date: '2024-01-16', pnl: 420.50, trades: 4},
        {date: '2024-01-17', pnl: -125.75, trades: 2},
        {date: '2024-01-18', pnl: 350.80, trades: 5},
        {date: '2024-01-19', pnl: 280.15, trades: 3}
      ],
      hourlyStats: [
        {hour: 8, trades: 8, pnl: 680.25, winRate: 87.5},
        {hour: 13, trades: 12, pnl: 1250.50, winRate: 83.3},
        {hour: 14, trades: 10, pnl: 890.75, winRate: 80.0},
        {hour: 15, trades: 15, pnl: 1580.25, winRate: 73.3}
      ],
      symbolStats: [
        {symbol: 'EURUSD', trades: 28, pnl: 3250.50, winRate: 78.6},
        {symbol: 'GBPUSD', trades: 22, pnl: 2680.25, winRate: 72.7},
        {symbol: 'USDJPY', trades: 18, pnl: 1890.75, winRate: 72.2},
        {symbol: 'AUDUSD', trades: 15, pnl: 1128.75, winRate: 73.3}
      ]
    },
    {
      strategy: 'scalping',
      metrics: {
        totalTrades: 1250,
        winRate: 62.4,
        totalPnL: 6750.50,
        avgWin: 25.80,
        avgLoss: -18.45,
        maxDrawdown: -580.00,
        sharpeRatio: 1.45,
        profitFactor: 1.85,
        avgHoldTime: '12m',
        bestTrade: 125.50,
        worstTrade: -85.25
      },
      dailyPnL: [
        {date: '2024-01-15', pnl: 125.50, trades: 45},
        {date: '2024-01-16', pnl: 85.25, trades: 38},
        {date: '2024-01-17', pnl: 180.75, trades: 52},
        {date: '2024-01-18', pnl: -45.30, trades: 28},
        {date: '2024-01-19', pnl: 220.15, trades: 65}
      ],
      hourlyStats: [
        {hour: 8, trades: 85, pnl: 250.25, winRate: 65.9},
        {hour: 9, trades: 125, pnl: 380.50, winRate: 64.0},
        {hour: 13, trades: 180, pnl: 580.75, winRate: 66.7},
        {hour: 14, trades: 165, pnl: 520.25, winRate: 63.6},
        {hour: 15, trades: 145, pnl: 450.80, winRate: 62.1}
      ],
      symbolStats: [
        {symbol: 'EURUSD', trades: 425, pnl: 2250.50, winRate: 64.7},
        {symbol: 'GBPUSD', trades: 380, pnl: 1980.25, winRate: 61.8},
        {symbol: 'USDJPY', trades: 285, pnl: 1580.75, winRate: 60.4},
        {symbol: 'AUDUSD', trades: 160, pnl: 939.00, winRate: 63.1}
      ]
    }
  ];

  useEffect(() => {
    setPerformanceData(mockPerformanceData);
  }, []);

  const getCurrentStrategyData = () => {
    return performanceData.find(data => data.strategy === selectedStrategy) || performanceData[0];
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(value);
  };

  const formatPercentage = (value: number) => {
    return `${value.toFixed(1)}%`;
  };

  const getMetricColor = (value: number, isPositive: boolean = true) => {
    if (isPositive) {
      return value >= 0 ? 'text-green-600' : 'text-red-600';
    }
    return value >= 0 ? 'text-red-600' : 'text-green-600';
  };

  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

  const currentData = getCurrentStrategyData();

  const renderOverview = () => (
    <div className="space-y-6">
      {/* Key Metrics Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border">
          <div className="text-sm text-gray-600 mb-1">Total P&L</div>
          <div className={`text-2xl font-bold ${getMetricColor(currentData.metrics.totalPnL)}`}>
            {formatCurrency(currentData.metrics.totalPnL)}
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg border">
          <div className="text-sm text-gray-600 mb-1">Win Rate</div>
          <div className="text-2xl font-bold text-blue-600">
            {formatPercentage(currentData.metrics.winRate)}
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg border">
          <div className="text-sm text-gray-600 mb-1">Total Trades</div>
          <div className="text-2xl font-bold text-gray-800">
            {currentData.metrics.totalTrades.toLocaleString()}
          </div>
        </div>
        
        <div className="bg-white p-4 rounded-lg border">
          <div className="text-sm text-gray-600 mb-1">Sharpe Ratio</div>
          <div className="text-2xl font-bold text-purple-600">
            {currentData.metrics.sharpeRatio.toFixed(2)}
          </div>
        </div>
      </div>

      {/* Detailed Metrics */}
      <div className="bg-white rounded-lg border overflow-hidden">
        <div className="p-4 bg-gray-50 border-b">
          <h3 className="text-lg font-semibold">Detailed Performance Metrics</h3>
        </div>
        
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="space-y-4">
              <h4 className="font-semibold text-gray-800">Risk Metrics</h4>
              
              <div className="flex justify-between">
                <span className="text-gray-600">Max Drawdown:</span>
                <span className={`font-semibold ${getMetricColor(currentData.metrics.maxDrawdown, false)}`}>
                  {formatCurrency(currentData.metrics.maxDrawdown)}
                </span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-gray-600">Profit Factor:</span>
                <span className="font-semibold text-green-600">
                  {currentData.metrics.profitFactor.toFixed(2)}
                </span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-gray-600">Avg Hold Time:</span>
                <span className="font-semibold text-gray-800">
                  {currentData.metrics.avgHoldTime}
                </span>
              </div>
            </div>
            
            <div className="space-y-4">
              <h4 className="font-semibold text-gray-800">Trade Analysis</h4>
              
              <div className="flex justify-between">
                <span className="text-gray-600">Avg Win:</span>
                <span className="font-semibold text-green-600">
                  {formatCurrency(currentData.metrics.avgWin)}
                </span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-gray-600">Avg Loss:</span>
                <span className="font-semibold text-red-600">
                  {formatCurrency(currentData.metrics.avgLoss)}
                </span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-gray-600">Risk/Reward:</span>
                <span className="font-semibold text-blue-600">
                  1:{(Math.abs(currentData.metrics.avgWin / currentData.metrics.avgLoss)).toFixed(2)}
                </span>
              </div>
            </div>
            
            <div className="space-y-4">
              <h4 className="font-semibold text-gray-800">Extremes</h4>
              
              <div className="flex justify-between">
                <span className="text-gray-600">Best Trade:</span>
                <span className="font-semibold text-green-600">
                  {formatCurrency(currentData.metrics.bestTrade)}
                </span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-gray-600">Worst Trade:</span>
                <span className="font-semibold text-red-600">
                  {formatCurrency(currentData.metrics.worstTrade)}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  const renderCharts = () => (
    <div className="space-y-6">
      {/* Daily P&L Chart */}
      <div className="bg-white rounded-lg border p-6">
        <h3 className="text-lg font-semibold mb-4">Daily P&L Trend</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={currentData.dailyPnL}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="date" />
            <YAxis />
            <Tooltip formatter={(value) => [formatCurrency(Number(value)), 'P&L']} />
            <Legend />
            <Line type="monotone" dataKey="pnl" stroke="#8884d8" strokeWidth={2} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Hourly Performance */}
      <div className="bg-white rounded-lg border p-6">
        <h3 className="text-lg font-semibold mb-4">Hourly Performance Analysis</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={currentData.hourlyStats}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="hour" />
            <YAxis yAxisId="left" />
            <YAxis yAxisId="right" orientation="right" />
            <Tooltip />
            <Legend />
            <Bar yAxisId="left" dataKey="pnl" fill="#8884d8" name="P&L" />
            <Line yAxisId="right" type="monotone" dataKey="winRate" stroke="#82ca9d" name="Win Rate %" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Symbol Distribution */}
      <div className="bg-white rounded-lg border p-6">
        <h3 className="text-lg font-semibold mb-4">Performance by Symbol</h3>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={currentData.symbolStats}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({symbol, pnl}) => `${symbol}: ${formatCurrency(pnl)}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="pnl"
              >
                {currentData.symbolStats.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => [formatCurrency(Number(value)), 'P&L']} />
            </PieChart>
          </ResponsiveContainer>
          
          <div className="space-y-3">
            {currentData.symbolStats.map((symbol, index) => (
              <div key={symbol.symbol} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <div className="flex items-center space-x-3">
                  <div 
                    className="w-4 h-4 rounded" 
                    style={{backgroundColor: COLORS[index % COLORS.length]}}
                  ></div>
                  <span className="font-semibold">{symbol.symbol}</span>
                </div>
                <div className="text-right">
                  <div className={`font-semibold ${getMetricColor(symbol.pnl)}`}>
                    {formatCurrency(symbol.pnl)}
                  </div>
                  <div className="text-sm text-gray-600">
                    {symbol.trades} trades • {formatPercentage(symbol.winRate)} win rate
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  const renderAnalysis = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg border p-6">
        <h3 className="text-lg font-semibold mb-4">Strategy Analysis</h3>
        
        <div className="space-y-4">
          <div className="p-4 bg-blue-50 rounded-lg">
            <h4 className="font-semibold text-blue-800 mb-2">Strengths</h4>
            <ul className="space-y-1 text-sm text-blue-700">
              {currentData.metrics.winRate > 65 && <li>• High win rate indicates good entry timing</li>}
              {currentData.metrics.sharpeRatio > 1.5 && <li>• Strong risk-adjusted returns</li>}
              {currentData.metrics.profitFactor > 2 && <li>• Excellent profit factor shows good risk management</li>}
              <li>• Consistent performance across different market conditions</li>
            </ul>
          </div>
          
          <div className="p-4 bg-yellow-50 rounded-lg">
            <h4 className="font-semibold text-yellow-800 mb-2">Areas for Improvement</h4>
            <ul className="space-y-1 text-sm text-yellow-700">
              {currentData.metrics.maxDrawdown < -1000 && <li>• Consider reducing position sizes to limit drawdown</li>}
              {currentData.metrics.winRate < 60 && <li>• Review entry criteria to improve win rate</li>}
              <li>• Monitor performance during low volatility periods</li>
              <li>• Consider diversifying across more currency pairs</li>
            </ul>
          </div>
          
          <div className="p-4 bg-green-50 rounded-lg">
            <h4 className="font-semibold text-green-800 mb-2">Recommendations</h4>
            <ul className="space-y-1 text-sm text-green-700">
              <li>• Focus trading during high-volume overlap periods</li>
              <li>• Maintain current risk management parameters</li>
              <li>• Consider scaling up position sizes gradually</li>
              <li>• Monitor correlation between different symbols</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );

  const renderComparison = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-lg border overflow-hidden">
        <div className="p-4 bg-gray-50 border-b">
          <h3 className="text-lg font-semibold">Strategy Comparison</h3>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Metric</th>
                <th className="px-4 py-3 text-center text-sm font-medium text-gray-700">Fast</th>
                <th className="px-4 py-3 text-center text-sm font-medium text-gray-700">Slow</th>
                <th className="px-4 py-3 text-center text-sm font-medium text-gray-700">Scalping</th>
                <th className="px-4 py-3 text-center text-sm font-medium text-gray-700">Best</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {[
                {key: 'totalPnL', label: 'Total P&L', format: formatCurrency},
                {key: 'winRate', label: 'Win Rate', format: formatPercentage},
                {key: 'totalTrades', label: 'Total Trades', format: (v: number) => v.toLocaleString()},
                {key: 'sharpeRatio', label: 'Sharpe Ratio', format: (v: number) => v.toFixed(2)},
                {key: 'profitFactor', label: 'Profit Factor', format: (v: number) => v.toFixed(2)},
                {key: 'maxDrawdown', label: 'Max Drawdown', format: formatCurrency}
              ].map((metric) => {
                const values = performanceData.map(data => data.metrics[metric.key as keyof PerformanceMetrics]);
                const bestIndex = metric.key === 'maxDrawdown' 
                  ? values.indexOf(Math.max(...values as number[]))
                  : values.indexOf(Math.max(...values as number[]));
                
                return (
                  <tr key={metric.key}>
                    <td className="px-4 py-3 font-medium">{metric.label}</td>
                    {performanceData.map((data, index) => {
                      const value = data.metrics[metric.key as keyof PerformanceMetrics];
                      const isBest = index === bestIndex;
                      
                      return (
                        <td key={data.strategy} className={`px-4 py-3 text-center ${
                          isBest ? 'bg-green-100 font-semibold text-green-800' : ''
                        }`}>
                          {metric.format(value as number)}
                        </td>
                      );
                    })}
                    <td className="px-4 py-3 text-center font-semibold text-green-600">
                      {performanceData[bestIndex].strategy.toUpperCase()}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white p-6 rounded-lg">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold mb-2">Performance Tracker</h2>
            <p className="text-lg opacity-90">
              {selectedStrategy.charAt(0).toUpperCase() + selectedStrategy.slice(1)} Strategy • {timeframe}
            </p>
          </div>
          <div className="text-right">
            <button
              onClick={() => onExportData(currentData)}
              className="bg-white text-purple-600 px-4 py-2 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
            >
              Export Data
            </button>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white rounded-lg border">
        <div className="flex border-b">
          {[
            {key: 'overview', label: 'Overview', icon: '📊'},
            {key: 'charts', label: 'Charts', icon: '📈'},
            {key: 'analysis', label: 'Analysis', icon: '🔍'},
            {key: 'comparison', label: 'Comparison', icon: '⚖️'}
          ].map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`flex-1 px-4 py-3 text-center font-medium transition-colors ${
                activeTab === tab.key
                  ? 'border-b-2 border-blue-500 text-blue-600 bg-blue-50'
                  : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>
        
        <div className="p-6">
          {activeTab === 'overview' && renderOverview()}
          {activeTab === 'charts' && renderCharts()}
          {activeTab === 'analysis' && renderAnalysis()}
          {activeTab === 'comparison' && renderComparison()}
        </div>
      </div>
    </div>
  );
};

export default BulenoxPerformanceTracker;