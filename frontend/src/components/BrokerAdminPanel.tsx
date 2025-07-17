import React, { useState, useEffect } from 'react';

interface BrokerConfig {
  name: string;
  apiKey: string;
  defaultRiskPercent: number;
}

const BrokerAdminPanel: React.FC = () => {
  const [brokers, setBrokers] = useState<BrokerConfig[]>([]);
  const [newBroker, setNewBroker] = useState<BrokerConfig>({ name: '', apiKey: '', defaultRiskPercent: 0.5 });

  useEffect(() => {
    // Load brokers.json from backend
    fetch('/api/brokers')
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success' && Array.isArray(data.brokers)) {
          setBrokers(data.brokers);
        }
      })
      .catch(err => console.error('Failed to load brokers', err));
  }, []);

  const handleAddBroker = () => {
    if (!newBroker.name) return;
    const updatedBrokers = [...brokers, newBroker];
    setBrokers(updatedBrokers);
    setNewBroker({ name: '', apiKey: '', defaultRiskPercent: 0.5 });
    // Save updated brokers to backend
    fetch('/api/brokers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ brokers: updatedBrokers })
    }).catch(err => console.error('Failed to save brokers', err));
  };

  const handleInputChange = (index: number, field: keyof BrokerConfig, value: string | number) => {
    const updatedBrokers = [...brokers];
    updatedBrokers[index] = { ...updatedBrokers[index], [field]: value };
    setBrokers(updatedBrokers);
  };

  return (
    <div className="p-4 border rounded shadow-md">
      <h2 className="text-xl font-bold mb-4">Broker Admin Panel</h2>
      <table className="w-full mb-4 border-collapse border border-gray-300">
        <thead>
          <tr>
            <th className="border border-gray-300 p-2">Name</th>
            <th className="border border-gray-300 p-2">API Key</th>
            <th className="border border-gray-300 p-2">Default Risk %</th>
          </tr>
        </thead>
        <tbody>
          {brokers.map((broker, index) => (
            <tr key={index}>
              <td className="border border-gray-300 p-2">
                <input
                  type="text"
                  value={broker.name}
                  onChange={e => handleInputChange(index, 'name', e.target.value)}
                  className="w-full"
                />
              </td>
              <td className="border border-gray-300 p-2">
                <input
                  type="text"
                  value={broker.apiKey}
                  onChange={e => handleInputChange(index, 'apiKey', e.target.value)}
                  className="w-full"
                />
              </td>
              <td className="border border-gray-300 p-2">
                <input
                  type="number"
                  step="0.01"
                  value={broker.defaultRiskPercent}
                  onChange={e => handleInputChange(index, 'defaultRiskPercent', parseFloat(e.target.value))}
                  className="w-full"
                />
              </td>
            </tr>
          ))}
          <tr>
            <td className="border border-gray-300 p-2">
              <input
                type="text"
                placeholder="New broker name"
                value={newBroker.name}
                onChange={e => setNewBroker({ ...newBroker, name: e.target.value })}
                className="w-full"
              />
            </td>
            <td className="border border-gray-300 p-2">
              <input
                type="text"
                placeholder="API Key"
                value={newBroker.apiKey}
                onChange={e => setNewBroker({ ...newBroker, apiKey: e.target.value })}
                className="w-full"
              />
            </td>
            <td className="border border-gray-300 p-2">
              <input
                type="number"
                step="0.01"
                placeholder="Risk %"
                value={newBroker.defaultRiskPercent}
                onChange={e => setNewBroker({ ...newBroker, defaultRiskPercent: parseFloat(e.target.value) })}
                className="w-full"
              />
            </td>
          </tr>
        </tbody>
      </table>
      <button
        onClick={handleAddBroker}
        className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
      >
        Add Broker
      </button>
    </div>
  );
};

export default BrokerAdminPanel;