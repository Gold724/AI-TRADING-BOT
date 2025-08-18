import React, { useState, useEffect } from 'react';

interface Position {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  size: number;
  entryPrice: number;
  currentPrice: number;
  stopLoss: number;
  takeProfit: number;
  pnl: number;
  pnlPercentage: number;
  openTime: string;
  strategy: 'fast' | 'slow' | 'scalping';
  status: 'open' | 'closed' | 'pending';
}

interface BulenoxPositionManagerProps {
  positions: Position[];
  onClosePosition: (positionId: string) => void;
  onModifyPosition: (positionId: string, stopLoss: number, takeProfit: number) => void;
  selectedStrategy: 'fast' | 'slow' | 'scalping';
}

const BulenoxPositionManager: React.FC<BulenoxPositionManagerProps> = ({
  positions,
  onClosePosition,
  onModifyPosition,
  selectedStrategy
}) => {
  const [selectedPosition, setSelectedPosition] = useState<string | null>(null);
  const [modifyValues, setModifyValues] = useState({ stopLoss: 0, takeProfit: 0 });
  const [showModifyModal, setShowModifyModal] = useState(false);
  const [filter, setFilter] = useState<'all' | 'open' | 'closed' | 'pending'>('open');
  const [sortBy, setSortBy] = useState<'pnl' | 'time' | 'symbol'>('pnl');

  // Calculate portfolio metrics
  const openPositions = positions.filter(p => p.status === 'open');
  const totalPnL = openPositions.reduce((sum, pos) => sum + pos.pnl, 0);
  const totalExposure = openPositions.reduce((sum, pos) => sum + (pos.size * pos.currentPrice), 0);
  const winningPositions = openPositions.filter(p => p.pnl > 0).length;
  const losingPositions = openPositions.filter(p => p.pnl < 0).length;

  const handleModifyPosition = (position: Position) => {
    setSelectedPosition(position.id);
    setModifyValues({
      stopLoss: position.stopLoss,
      takeProfit: position.takeProfit
    });
    setShowModifyModal(true);
  };

  const confirmModify = () => {
    if (selectedPosition) {
      onModifyPosition(selectedPosition, modifyValues.stopLoss, modifyValues.takeProfit);
      setShowModifyModal(false);
      setSelectedPosition(null);
    }
  };

  const getStrategyColor = (strategy: 'fast' | 'slow' | 'scalping') => {
    switch (strategy) {
      case 'fast': return 'bg-red-100 text-red-800';
      case 'slow': return 'bg-blue-100 text-blue-800';
      case 'scalping': return 'bg-green-100 text-green-800';
    }
  };

  const getPnLColor = (pnl: number) => {
    if (pnl > 0) return 'text-green-600';
    if (pnl < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(amount);
  };

  const formatTime = (timeString: string) => {
    return new Date(timeString).toLocaleString();
  };

  const filteredPositions = positions
    .filter(pos => filter === 'all' || pos.status === filter)
    .filter(pos => selectedStrategy === 'all' || pos.strategy === selectedStrategy)
    .sort((a, b) => {
      switch (sortBy) {
        case 'pnl': return b.pnl - a.pnl;
        case 'time': return new Date(b.openTime).getTime() - new Date(a.openTime).getTime();
        case 'symbol': return a.symbol.localeCompare(b.symbol);
        default: return 0;
      }
    });

  return (
    <div className="space-y-6">
      {/* Portfolio Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border">
          <h3 className="text-sm font-medium text-gray-600 mb-1">Total P&L</h3>
          <p className={`text-2xl font-bold ${getPnLColor(totalPnL)}`}>
            {formatCurrency(totalPnL)}
          </p>
          <p className="text-xs text-gray-500">
            {totalPnL >= 0 ? '+' : ''}{((totalPnL / totalExposure) * 100).toFixed(2)}%
          </p>
        </div>
        
        <div className="bg-white p-4 rounded-lg border">
          <h3 className="text-sm font-medium text-gray-600 mb-1">Open Positions</h3>
          <p className="text-2xl font-bold text-blue-600">{openPositions.length}</p>
          <p className="text-xs text-gray-500">
            {winningPositions}W / {losingPositions}L
          </p>
        </div>
        
        <div className="bg-white p-4 rounded-lg border">
          <h3 className="text-sm font-medium text-gray-600 mb-1">Total Exposure</h3>
          <p className="text-2xl font-bold text-purple-600">
            {formatCurrency(totalExposure)}
          </p>
          <p className="text-xs text-gray-500">Across all positions</p>
        </div>
        
        <div className="bg-white p-4 rounded-lg border">
          <h3 className="text-sm font-medium text-gray-600 mb-1">Win Rate</h3>
          <p className="text-2xl font-bold text-green-600">
            {openPositions.length > 0 ? ((winningPositions / openPositions.length) * 100).toFixed(1) : '0'}%
          </p>
          <p className="text-xs text-gray-500">Current session</p>
        </div>
      </div>

      {/* Filters and Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4 bg-white p-4 rounded-lg border">
        <div className="flex items-center space-x-4">
          <div>
            <label className="text-sm font-medium text-gray-700 mr-2">Filter:</label>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value as any)}
              className="border border-gray-300 rounded-md px-3 py-1 text-sm"
            >
              <option value="all">All Positions</option>
              <option value="open">Open Only</option>
              <option value="closed">Closed Only</option>
              <option value="pending">Pending Only</option>
            </select>
          </div>
          
          <div>
            <label className="text-sm font-medium text-gray-700 mr-2">Sort by:</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="border border-gray-300 rounded-md px-3 py-1 text-sm"
            >
              <option value="pnl">P&L</option>
              <option value="time">Time</option>
              <option value="symbol">Symbol</option>
            </select>
          </div>
        </div>
        
        <div className="flex space-x-2">
          <button className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 text-sm">
            Close All Positions
          </button>
          <button className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 text-sm">
            Export Data
          </button>
        </div>
      </div>

      {/* Positions Table */}
      <div className="bg-white rounded-lg border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Symbol</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Side</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Size</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Entry</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Current</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">P&L</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">SL/TP</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Strategy</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Time</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filteredPositions.map((position) => (
                <tr key={position.id} className={position.status === 'open' ? 'bg-white' : 'bg-gray-50'}>
                  <td className="px-4 py-3">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono font-semibold">{position.symbol}</span>
                      <div className={`w-2 h-2 rounded-full ${
                        position.status === 'open' ? 'bg-green-500' : 
                        position.status === 'pending' ? 'bg-yellow-500' : 'bg-gray-400'
                      }`}></div>
                    </div>
                  </td>
                  
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      position.side === 'buy' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {position.side.toUpperCase()}
                    </span>
                  </td>
                  
                  <td className="px-4 py-3 font-mono text-sm">{position.size}</td>
                  
                  <td className="px-4 py-3 font-mono text-sm">{position.entryPrice.toFixed(5)}</td>
                  
                  <td className="px-4 py-3 font-mono text-sm">{position.currentPrice.toFixed(5)}</td>
                  
                  <td className="px-4 py-3">
                    <div>
                      <span className={`font-semibold ${getPnLColor(position.pnl)}`}>
                        {formatCurrency(position.pnl)}
                      </span>
                      <div className={`text-xs ${getPnLColor(position.pnl)}`}>
                        ({position.pnlPercentage >= 0 ? '+' : ''}{position.pnlPercentage.toFixed(2)}%)
                      </div>
                    </div>
                  </td>
                  
                  <td className="px-4 py-3">
                    <div className="text-xs space-y-1">
                      <div>SL: {position.stopLoss.toFixed(5)}</div>
                      <div>TP: {position.takeProfit.toFixed(5)}</div>
                    </div>
                  </td>
                  
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      getStrategyColor(position.strategy)
                    }`}>
                      {position.strategy.toUpperCase()}
                    </span>
                  </td>
                  
                  <td className="px-4 py-3 text-xs text-gray-600">
                    {formatTime(position.openTime)}
                  </td>
                  
                  <td className="px-4 py-3">
                    <div className="flex space-x-1">
                      {position.status === 'open' && (
                        <>
                          <button
                            onClick={() => handleModifyPosition(position)}
                            className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs hover:bg-blue-200"
                          >
                            Modify
                          </button>
                          <button
                            onClick={() => onClosePosition(position.id)}
                            className="bg-red-100 text-red-700 px-2 py-1 rounded text-xs hover:bg-red-200"
                          >
                            Close
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        
        {filteredPositions.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <p>No positions found matching the current filters.</p>
          </div>
        )}
      </div>

      {/* Modify Position Modal */}
      {showModifyModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">Modify Position</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Stop Loss
                </label>
                <input
                  type="number"
                  step="0.00001"
                  value={modifyValues.stopLoss}
                  onChange={(e) => setModifyValues(prev => ({ ...prev, stopLoss: Number(e.target.value) }))}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Take Profit
                </label>
                <input
                  type="number"
                  step="0.00001"
                  value={modifyValues.takeProfit}
                  onChange={(e) => setModifyValues(prev => ({ ...prev, takeProfit: Number(e.target.value) }))}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
            
            <div className="flex space-x-3 mt-6">
              <button
                onClick={confirmModify}
                className="flex-1 bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700"
              >
                Update Position
              </button>
              <button
                onClick={() => setShowModifyModal(false)}
                className="flex-1 bg-gray-300 text-gray-700 py-2 rounded-md hover:bg-gray-400"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default BulenoxPositionManager;