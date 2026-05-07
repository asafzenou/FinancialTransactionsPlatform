/**
 * Clients page - displays all clients and their positions
 */

import React, { useState } from 'react';
import { Users, ArrowLeft, TrendingUp } from 'lucide-react';
import { useClients, useClientPositions } from '../hooks/useClients';
import { Spinner } from '../components/Spinner';
import { DataTable } from '../components/DataTable';
import { PositionDetail } from '../types';

interface ClientsPageProps {
  onBack: () => void;
}

export const ClientsPage: React.FC<ClientsPageProps> = ({ onBack }) => {
  const { clients, isLoading, error } = useClients();
  const [selectedClientId, setSelectedClientId] = useState<string | null>(null);
  const { positions, isLoading: isLoadingPositions } = useClientPositions(selectedClientId);

  const positionColumns = [
    { key: 'isin' as const, label: 'ISIN', width: 'w-20' },
    {
      key: 'total_quantity' as const,
      label: 'Quantity',
      render: (value: number) => value.toLocaleString(),
    },
    {
      key: 'average_cost' as const,
      label: 'Avg Cost',
      render: (value: number) => `$${value.toFixed(2)}`,
    },
    {
      key: 'realized_pnl' as const,
      label: 'Realized P&L',
      render: (value: number) => (
        <span className={value >= 0 ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>
          ${value.toFixed(2)}
        </span>
      ),
    },
    {
      key: 'unrealized_pnl' as const,
      label: 'Unrealized P&L',
      render: (value: number) => (
        <span className={value >= 0 ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}>
          ${value.toFixed(2)}
        </span>
      ),
    },
  ];

  if (isLoading) return <Spinner message="Loading clients..." />;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800">
      {/* Header */}
      <div className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center gap-4">
            <button
              onClick={onBack}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-6 h-6 text-gray-600" />
            </button>
            <div className="flex items-center gap-3">
              <Users className="w-7 h-7 text-blue-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Clients</h1>
                <p className="text-gray-600 text-sm">
                  {clients.length} client{clients.length !== 1 ? 's' : ''} in the system
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Clients List */}
          <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b border-gray-200">
              <h2 className="font-semibold text-gray-900">Clients List</h2>
            </div>
            <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
              {clients.map((client) => (
                <button
                  key={client.id}
                  onClick={() => setSelectedClientId(client.id)}
                  className={`w-full text-left px-4 py-3 transition-colors ${
                    selectedClientId === client.id
                      ? 'bg-blue-50 border-l-4 border-blue-600'
                      : 'hover:bg-gray-50'
                  }`}
                >
                  <p className="text-sm font-medium text-gray-900">{client.id}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Positions Detail */}
          <div className="lg:col-span-2 bg-white rounded-lg shadow">
            {!selectedClientId ? (
              <div className="flex flex-col items-center justify-center h-64 text-center">
                <TrendingUp className="w-12 h-12 text-gray-300 mb-3" />
                <p className="text-gray-500">Select a client to view positions</p>
              </div>
            ) : isLoadingPositions ? (
              <Spinner />
            ) : positions && positions.positions.length > 0 ? (
              <div className="p-4">
                <div className="mb-4">
                  <h2 className="font-semibold text-gray-900">
                    Positions for {selectedClientId}
                  </h2>
                  <p className="text-sm text-gray-600">
                    {positions.positions.length} position{positions.positions.length !== 1 ? 's' : ''}
                  </p>
                </div>
                <DataTable
                  columns={positionColumns}
                  data={positions.positions as PositionDetail[]}
                  keyExtractor={(row) => row.isin}
                />
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-64 text-center">
                <p className="text-gray-500">No positions found for this client</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
