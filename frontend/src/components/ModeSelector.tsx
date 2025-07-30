import React from 'react';

interface ModeSelectorProps {
  value: string;
  onChange: (mode: string) => void;
}

const ModeSelector: React.FC<ModeSelectorProps> = ({ value, onChange }) => {
  return (
    <div className="bg-white p-4 rounded shadow mb-4">
      <h2 className="text-xl font-semibold mb-2">Trading Mode</h2>
      <div className="flex space-x-2">
        <button
          className={`px-4 py-2 rounded-md flex items-center ${value === 'fast' ? 'bg-orange-500 text-white' : 'bg-gray-200 text-gray-700'}`}
          onClick={() => onChange('fast')}
        >
          <span className="mr-1">🔥</span> Fast Pass
        </button>
        <button
          className={`px-4 py-2 rounded-md flex items-center ${value === 'safe' ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-700'}`}
          onClick={() => onChange('safe')}
        >
          <span className="mr-1">🌱</span> Safe Growth
        </button>
      </div>
      <div className="mt-2 text-sm text-gray-600">
        {value === 'fast' ? (
          <p>Aggressive mode targeting $15K in 5-10 days (30-50% daily)</p>
        ) : (
          <p>Conservative mode targeting $14.5K+ in 20 days (5-15% daily)</p>
        )}
      </div>
    </div>
  );
};

export default ModeSelector;