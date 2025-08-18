import React, { useState, useEffect } from 'react';

interface MarketSession {
  name: string;
  timezone: string;
  openTime: string;
  closeTime: string;
  isActive: boolean;
  volume: 'high' | 'medium' | 'low';
  volatility: 'high' | 'medium' | 'low';
  optimalFor: ('fast' | 'slow' | 'scalping')[];
}

interface BulenoxMarketHoursProps {
  selectedStrategy: 'fast' | 'slow' | 'scalping';
  onStrategyOptimization: (recommendations: string[]) => void;
}

const BulenoxMarketHours: React.FC<BulenoxMarketHoursProps> = ({
  selectedStrategy,
  onStrategyOptimization
}) => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [selectedTimezone, setSelectedTimezone] = useState('UTC');
  const [showRecommendations, setShowRecommendations] = useState(true);

  const marketSessions: MarketSession[] = [
    {
      name: 'Sydney',
      timezone: 'AEDT',
      openTime: '22:00',
      closeTime: '07:00',
      isActive: false,
      volume: 'low',
      volatility: 'low',
      optimalFor: ['slow']
    },
    {
      name: 'Tokyo',
      timezone: 'JST',
      openTime: '00:00',
      closeTime: '09:00',
      isActive: false,
      volume: 'medium',
      volatility: 'medium',
      optimalFor: ['fast', 'scalping']
    },
    {
      name: 'London',
      timezone: 'GMT',
      openTime: '08:00',
      closeTime: '17:00',
      isActive: true,
      volume: 'high',
      volatility: 'high',
      optimalFor: ['fast', 'scalping']
    },
    {
      name: 'New York',
      timezone: 'EST',
      openTime: '13:00',
      closeTime: '22:00',
      isActive: true,
      volume: 'high',
      volatility: 'high',
      optimalFor: ['fast', 'slow', 'scalping']
    }
  ];

  const overlapPeriods = [
    {
      name: 'Tokyo-London Overlap',
      time: '08:00 - 09:00 UTC',
      description: 'Moderate volatility, good for scalping',
      intensity: 'medium',
      optimalFor: ['scalping', 'fast']
    },
    {
      name: 'London-New York Overlap',
      time: '13:00 - 17:00 UTC',
      description: 'Highest volatility period, excellent for all strategies',
      intensity: 'high',
      optimalFor: ['fast', 'slow', 'scalping']
    }
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    // Generate strategy recommendations based on current time and selected strategy
    const recommendations = generateRecommendations();
    onStrategyOptimization(recommendations);
  }, [selectedStrategy, currentTime]);

  const generateRecommendations = (): string[] => {
    const currentHour = currentTime.getUTCHours();
    const recommendations: string[] = [];

    // London-NY overlap (13:00-17:00 UTC)
    if (currentHour >= 13 && currentHour < 17) {
      recommendations.push('🔥 Prime trading time! London-NY overlap provides maximum liquidity');
      if (selectedStrategy === 'scalping') {
        recommendations.push('⚡ Perfect for scalping - high volatility and tight spreads');
      }
      if (selectedStrategy === 'fast') {
        recommendations.push('🚀 Ideal for fast trading - strong directional moves expected');
      }
    }

    // Tokyo session (00:00-09:00 UTC)
    else if (currentHour >= 0 && currentHour < 9) {
      if (selectedStrategy === 'slow') {
        recommendations.push('🐢 Good time for slow trading - steady Asian session trends');
      } else {
        recommendations.push('⚠️ Lower volatility period - consider reducing position sizes');
      }
    }

    // London session start (08:00-13:00 UTC)
    else if (currentHour >= 8 && currentHour < 13) {
      recommendations.push('📈 London session active - expect increased volatility');
      if (selectedStrategy === 'fast' || selectedStrategy === 'scalping') {
        recommendations.push('✅ Good conditions for your selected strategy');
      }
    }

    // Off-hours
    else {
      recommendations.push('😴 Low activity period - consider smaller positions or avoid trading');
      if (selectedStrategy === 'slow') {
        recommendations.push('💡 Consider setting pending orders for upcoming sessions');
      }
    }

    return recommendations;
  };

  const isSessionActive = (session: MarketSession) => {
    const currentHour = currentTime.getUTCHours();
    const openHour = parseInt(session.openTime.split(':')[0]);
    const closeHour = parseInt(session.closeTime.split(':')[0]);
    
    if (openHour > closeHour) {
      // Session crosses midnight
      return currentHour >= openHour || currentHour < closeHour;
    }
    return currentHour >= openHour && currentHour < closeHour;
  };

  const getVolumeColor = (volume: 'high' | 'medium' | 'low') => {
    switch (volume) {
      case 'high': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-gray-600 bg-gray-100';
    }
  };

  const getVolatilityColor = (volatility: 'high' | 'medium' | 'low') => {
    switch (volatility) {
      case 'high': return 'text-red-600 bg-red-100';
      case 'medium': return 'text-orange-600 bg-orange-100';
      case 'low': return 'text-blue-600 bg-blue-100';
    }
  };

  const getIntensityColor = (intensity: string) => {
    switch (intensity) {
      case 'high': return 'bg-red-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-green-500';
      default: return 'bg-gray-500';
    }
  };

  const isOptimalForStrategy = (session: MarketSession) => {
    return session.optimalFor.includes(selectedStrategy);
  };

  return (
    <div className="space-y-6">
      {/* Current Time and Status */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6 rounded-lg">
        <div className="flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold mb-2">Global Market Hours</h2>
            <p className="text-lg font-mono">
              {currentTime.toUTCString().slice(0, -4)} UTC
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm opacity-90">Active Sessions</p>
            <p className="text-3xl font-bold">
              {marketSessions.filter(s => isSessionActive(s)).length}
            </p>
          </div>
        </div>
      </div>

      {/* Strategy Recommendations */}
      {showRecommendations && (
        <div className="bg-white rounded-lg border p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Strategy Recommendations</h3>
            <button
              onClick={() => setShowRecommendations(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>
          <div className="space-y-2">
            {generateRecommendations().map((rec, index) => (
              <div key={index} className="flex items-start space-x-2 p-3 bg-blue-50 rounded-lg">
                <span className="text-blue-600 font-medium">{rec}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Market Sessions */}
      <div className="bg-white rounded-lg border overflow-hidden">
        <div className="p-4 bg-gray-50 border-b">
          <h3 className="text-lg font-semibold">Major Trading Sessions</h3>
          <p className="text-sm text-gray-600 mt-1">
            Sessions optimal for <span className="font-semibold text-blue-600">{selectedStrategy}</span> strategy are highlighted
          </p>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Session</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Time (UTC)</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Status</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Volume</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Volatility</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Optimal For</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">Recommendation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {marketSessions.map((session, index) => {
                const isActive = isSessionActive(session);
                const isOptimal = isOptimalForStrategy(session);
                
                return (
                  <tr 
                    key={index} 
                    className={`${
                      isOptimal ? 'bg-green-50 border-l-4 border-green-500' : ''
                    } ${isActive ? 'bg-blue-50' : ''}`}
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center space-x-2">
                        <div className={`w-3 h-3 rounded-full ${
                          isActive ? 'bg-green-500 animate-pulse' : 'bg-gray-300'
                        }`}></div>
                        <span className="font-semibold">{session.name}</span>
                        <span className="text-xs text-gray-500">({session.timezone})</span>
                      </div>
                    </td>
                    
                    <td className="px-4 py-3 font-mono text-sm">
                      {session.openTime} - {session.closeTime}
                    </td>
                    
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        isActive 
                          ? 'bg-green-100 text-green-800' 
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {isActive ? 'OPEN' : 'CLOSED'}
                      </span>
                    </td>
                    
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        getVolumeColor(session.volume)
                      }`}>
                        {session.volume.toUpperCase()}
                      </span>
                    </td>
                    
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        getVolatilityColor(session.volatility)
                      }`}>
                        {session.volatility.toUpperCase()}
                      </span>
                    </td>
                    
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {session.optimalFor.map((strategy) => (
                          <span 
                            key={strategy}
                            className={`px-2 py-1 rounded text-xs font-medium ${
                              strategy === selectedStrategy
                                ? 'bg-blue-100 text-blue-800 border border-blue-300'
                                : 'bg-gray-100 text-gray-600'
                            }`}
                          >
                            {strategy}
                          </span>
                        ))}
                      </div>
                    </td>
                    
                    <td className="px-4 py-3">
                      {isOptimal ? (
                        <span className="text-green-600 font-medium text-sm">✅ Recommended</span>
                      ) : (
                        <span className="text-gray-400 text-sm">Not optimal</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Overlap Periods */}
      <div className="bg-white rounded-lg border p-6">
        <h3 className="text-lg font-semibold mb-4">High-Impact Overlap Periods</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {overlapPeriods.map((overlap, index) => {
            const isOptimalForCurrentStrategy = overlap.optimalFor.includes(selectedStrategy);
            
            return (
              <div 
                key={index} 
                className={`p-4 rounded-lg border-2 ${
                  isOptimalForCurrentStrategy 
                    ? 'border-green-300 bg-green-50' 
                    : 'border-gray-200 bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold">{overlap.name}</h4>
                  <div className={`w-3 h-3 rounded-full ${getIntensityColor(overlap.intensity)}`}></div>
                </div>
                
                <p className="text-sm text-gray-600 mb-2">{overlap.time}</p>
                <p className="text-sm mb-3">{overlap.description}</p>
                
                <div className="flex flex-wrap gap-1">
                  {overlap.optimalFor.map((strategy) => (
                    <span 
                      key={strategy}
                      className={`px-2 py-1 rounded text-xs font-medium ${
                        strategy === selectedStrategy
                          ? 'bg-blue-100 text-blue-800 border border-blue-300'
                          : 'bg-gray-100 text-gray-600'
                      }`}
                    >
                      {strategy}
                    </span>
                  ))}
                </div>
                
                {isOptimalForCurrentStrategy && (
                  <div className="mt-2 text-green-600 text-sm font-medium">
                    🎯 Perfect for your {selectedStrategy} strategy!
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Market Clock */}
      <div className="bg-white rounded-lg border p-6">
        <h3 className="text-lg font-semibold mb-4">24-Hour Market Clock</h3>
        <div className="relative">
          <div className="flex justify-between items-center mb-4">
            <span className="text-sm text-gray-600">00:00 UTC</span>
            <span className="text-sm text-gray-600">12:00 UTC</span>
            <span className="text-sm text-gray-600">24:00 UTC</span>
          </div>
          
          <div className="relative h-8 bg-gray-200 rounded-full overflow-hidden">
            {/* Sydney */}
            <div className="absolute h-full bg-blue-300 opacity-70" style={{left: '91.67%', width: '37.5%'}}></div>
            
            {/* Tokyo */}
            <div className="absolute h-full bg-green-300 opacity-70" style={{left: '0%', width: '37.5%'}}></div>
            
            {/* London */}
            <div className="absolute h-full bg-yellow-300 opacity-70" style={{left: '33.33%', width: '37.5%'}}></div>
            
            {/* New York */}
            <div className="absolute h-full bg-red-300 opacity-70" style={{left: '54.17%', width: '37.5%'}}></div>
            
            {/* Current time indicator */}
            <div 
              className="absolute top-0 w-1 h-full bg-black z-10"
              style={{left: `${(currentTime.getUTCHours() / 24) * 100}%`}}
            ></div>
          </div>
          
          <div className="flex justify-between mt-2 text-xs">
            <span className="text-blue-600">Sydney</span>
            <span className="text-green-600">Tokyo</span>
            <span className="text-yellow-600">London</span>
            <span className="text-red-600">New York</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BulenoxMarketHours;