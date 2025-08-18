import React, { useState, useEffect } from 'react';

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

interface BulenoxTimeTableProps {
  sessions: TradingSession[];
  onSessionToggle: (sessionId: string) => void;
  selectedStrategy: 'fast' | 'slow' | 'scalping';
}

const BulenoxTimeTable: React.FC<BulenoxTimeTableProps> = ({
  sessions,
  onSessionToggle,
  selectedStrategy
}) => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [newSession, setNewSession] = useState({
    name: '',
    startTime: '',
    endTime: '',
    strategy: selectedStrategy,
    symbol: 'EURUSD',
    riskLevel: 1
  });
  const [showAddForm, setShowAddForm] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  const isSessionActive = (session: TradingSession) => {
    const now = currentTime;
    const currentTimeStr = now.toTimeString().slice(0, 5);
    
    // Handle sessions that cross midnight
    if (session.startTime > session.endTime) {
      return currentTimeStr >= session.startTime || currentTimeStr <= session.endTime;
    }
    
    return currentTimeStr >= session.startTime && currentTimeStr <= session.endTime;
  };

  const getStrategyColor = (strategy: 'fast' | 'slow' | 'scalping') => {
    switch (strategy) {
      case 'fast': return 'bg-red-100 text-red-800 border-red-200';
      case 'slow': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'scalping': return 'bg-green-100 text-green-800 border-green-200';
    }
  };

  const getTimeUntilSession = (session: TradingSession) => {
    const now = new Date();
    const today = now.toDateString();
    const sessionStart = new Date(`${today} ${session.startTime}`);
    
    if (sessionStart < now) {
      sessionStart.setDate(sessionStart.getDate() + 1);
    }
    
    const diff = sessionStart.getTime() - now.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    return `${hours}h ${minutes}m`;
  };

  const handleAddSession = () => {
    // In a real app, this would call an API to add the session
    console.log('Adding new session:', newSession);
    setShowAddForm(false);
    setNewSession({
      name: '',
      startTime: '',
      endTime: '',
      strategy: selectedStrategy,
      symbol: 'EURUSD',
      riskLevel: 1
    });
  };

  return (
    <div className="space-y-6">
      {/* Current Time Display */}
      <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white p-4 rounded-lg">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-lg font-semibold">Current Time</h3>
            <p className="text-2xl font-mono">{currentTime.toTimeString().slice(0, 8)}</p>
          </div>
          <div className="text-right">
            <p className="text-sm opacity-90">Active Sessions</p>
            <p className="text-xl font-bold">
              {sessions.filter(s => s.isActive && isSessionActive(s)).length}
            </p>
          </div>
        </div>
      </div>

      {/* Session Management */}
      <div className="flex justify-between items-center">
        <h3 className="text-xl font-semibold text-gray-800">Trading Sessions</h3>
        <button
          onClick={() => setShowAddForm(!showAddForm)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          + Add Session
        </button>
      </div>

      {/* Add Session Form */}
      {showAddForm && (
        <div className="bg-gray-50 p-4 rounded-lg border">
          <h4 className="font-semibold mb-3">Create New Trading Session</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <input
              type="text"
              placeholder="Session Name"
              value={newSession.name}
              onChange={(e) => setNewSession(prev => ({ ...prev, name: e.target.value }))}
              className="p-2 border rounded-md"
            />
            <input
              type="time"
              value={newSession.startTime}
              onChange={(e) => setNewSession(prev => ({ ...prev, startTime: e.target.value }))}
              className="p-2 border rounded-md"
            />
            <input
              type="time"
              value={newSession.endTime}
              onChange={(e) => setNewSession(prev => ({ ...prev, endTime: e.target.value }))}
              className="p-2 border rounded-md"
            />
            <select
              value={newSession.strategy}
              onChange={(e) => setNewSession(prev => ({ ...prev, strategy: e.target.value as any }))}
              className="p-2 border rounded-md"
            >
              <option value="fast">Fast Trading</option>
              <option value="slow">Slow Trading</option>
              <option value="scalping">Scalping</option>
            </select>
            <input
              type="text"
              placeholder="Symbol (e.g., EURUSD)"
              value={newSession.symbol}
              onChange={(e) => setNewSession(prev => ({ ...prev, symbol: e.target.value }))}
              className="p-2 border rounded-md"
            />
            <select
              value={newSession.riskLevel}
              onChange={(e) => setNewSession(prev => ({ ...prev, riskLevel: Number(e.target.value) }))}
              className="p-2 border rounded-md"
            >
              <option value={1}>Low Risk</option>
              <option value={2}>Medium Risk</option>
              <option value={3}>High Risk</option>
            </select>
          </div>
          <div className="flex space-x-2 mt-4">
            <button
              onClick={handleAddSession}
              className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700"
            >
              Create Session
            </button>
            <button
              onClick={() => setShowAddForm(false)}
              className="bg-gray-400 text-white px-4 py-2 rounded-md hover:bg-gray-500"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Sessions Table */}
      <div className="bg-white rounded-lg border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Session</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Time</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Strategy</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Symbol</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Risk</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Status</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Next Start</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {sessions.map((session) => {
                const isCurrentlyActive = isSessionActive(session);
                return (
                  <tr key={session.id} className={isCurrentlyActive ? 'bg-green-50' : ''}>
                    <td className="px-4 py-3">
                      <div className="flex items-center space-x-2">
                        <div className={`w-3 h-3 rounded-full ${
                          isCurrentlyActive ? 'bg-green-500 animate-pulse' : 'bg-gray-300'
                        }`}></div>
                        <span className="font-medium">{session.name}</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 font-mono text-sm">
                      {session.startTime} - {session.endTime}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium border ${
                        getStrategyColor(session.strategy)
                      }`}>
                        {session.strategy.toUpperCase()}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono text-sm">{session.symbol}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center space-x-1">
                        {[...Array(3)].map((_, i) => (
                          <div
                            key={i}
                            className={`w-2 h-2 rounded-full ${
                              i < session.riskLevel ? 'bg-red-500' : 'bg-gray-200'
                            }`}
                          ></div>
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        session.isActive
                          ? isCurrentlyActive
                            ? 'bg-green-100 text-green-800'
                            : 'bg-yellow-100 text-yellow-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {session.isActive
                          ? isCurrentlyActive
                            ? 'RUNNING'
                            : 'SCHEDULED'
                          : 'DISABLED'
                        }
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {!isCurrentlyActive && session.isActive ? getTimeUntilSession(session) : '-'}
                    </td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => onSessionToggle(session.id)}
                        className={`px-3 py-1 rounded-md text-sm font-medium transition-colors ${
                          session.isActive
                            ? 'bg-red-100 text-red-700 hover:bg-red-200'
                            : 'bg-green-100 text-green-700 hover:bg-green-200'
                        }`}
                      >
                        {session.isActive ? 'Disable' : 'Enable'}
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <h4 className="font-semibold text-blue-800 mb-2">Fast Trading Sessions</h4>
          <p className="text-2xl font-bold text-blue-600">
            {sessions.filter(s => s.strategy === 'fast').length}
          </p>
          <p className="text-sm text-blue-600">
            {sessions.filter(s => s.strategy === 'fast' && s.isActive).length} active
          </p>
        </div>
        <div className="bg-green-50 p-4 rounded-lg border border-green-200">
          <h4 className="font-semibold text-green-800 mb-2">Scalping Sessions</h4>
          <p className="text-2xl font-bold text-green-600">
            {sessions.filter(s => s.strategy === 'scalping').length}
          </p>
          <p className="text-sm text-green-600">
            {sessions.filter(s => s.strategy === 'scalping' && s.isActive).length} active
          </p>
        </div>
        <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
          <h4 className="font-semibold text-purple-800 mb-2">Slow Trading Sessions</h4>
          <p className="text-2xl font-bold text-purple-600">
            {sessions.filter(s => s.strategy === 'slow').length}
          </p>
          <p className="text-sm text-purple-600">
            {sessions.filter(s => s.strategy === 'slow' && s.isActive).length} active
          </p>
        </div>
      </div>
    </div>
  );
};

export default BulenoxTimeTable;