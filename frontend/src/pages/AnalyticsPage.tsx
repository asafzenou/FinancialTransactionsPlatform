/**
 * Analytics page - displays aggregated portfolio analytics
 */

import React from 'react';
import { TrendingUp, ArrowLeft, TrendingDown } from 'lucide-react';
import { useAnalytics } from '../hooks/useAnalytics';
import { Spinner } from '../components/Spinner';
import { DataTable } from '../components/DataTable';
import { TopTradedISIN, AverageHoldingTime } from '../types';

interface AnalyticsPageProps {
  onBack: () => void;
}

export const AnalyticsPage: React.FC<AnalyticsPageProps> = ({ onBack }) => {
  const { data, isLoading, error } = useAnalytics();

  if (isLoading) return <Spinner message="Loading analytics..." />;

  const topTradedColumns = [
    { key: 'isin' as const, label: 'ISIN', width: 'w-24' },
    {
      key: 'transaction_count' as const,
      label: 'Transaction Count',
      render: (value: number) => (
        <span className="font-semibold text-blue-600">{value}</span>
      ),
    },
  ];

  const holdingTimeColumns = [
    { key: 'client_id' as const, label: 'Client ID', width: 'w-32' },
    {
      key: 'average_holding_days' as const,
      label: 'Avg Holding Days',
      render: (value: number) => `${value.toFixed(1)} days`,
    },
  ];

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
              <TrendingUp className="w-7 h-7 text-green-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
                <p className="text-gray-600 text-sm">Portfolio insights and metrics</p>
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

        {!data ? (
          <div className="text-center py-12">
            <p className="text-white">No analytics data available</p>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Most Volatile Client Card */}
            {data.most_volatile_client && (
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center gap-3 mb-4">
                  <TrendingDown className="w-6 h-6 text-red-600" />
                  <h2 className="text-xl font-bold text-gray-900">Most Volatile Client</h2>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600">Client ID</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {data.most_volatile_client.client_id || 'N/A'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600">Volatility</p>
                    <p className="text-2xl font-bold text-red-600">
                      ${data.most_volatile_client.volatility.toFixed(2)}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Top Traded ISINs */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Top 3 Traded ISINs</h2>
              {data.top_3_traded_isins.length > 0 ? (
                <div className="overflow-x-auto">
                  <DataTable
                    columns={topTradedColumns}
                    data={data.top_3_traded_isins as TopTradedISIN[]}
                    keyExtractor={(row) => row.isin}
                  />
                </div>
              ) : (
                <p className="text-gray-500">No trading data available</p>
              )}
            </div>

            {/* Average Holding Time */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Average Holding Time Per Client</h2>
              {data.average_holding_time_per_client.length > 0 ? (
                <div className="overflow-x-auto">
                  <DataTable
                    columns={holdingTimeColumns}
                    data={data.average_holding_time_per_client as AverageHoldingTime[]}
                    keyExtractor={(row) => row.client_id}
                  />
                </div>
              ) : (
                <p className="text-gray-500">No holding time data available</p>
              )}
            </div>

            {/* ISIN Concentration Report */}
            {data.isin_concentration_report && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-2">
                  ISIN Concentration Report
                </h2>
                <p className="text-sm text-gray-600 mb-4">
                  ISINs appearing in {data.isin_concentration_report.threshold_percent}% or more of clients
                </p>

                {data.isin_concentration_report.concentrated_isins &&
                data.isin_concentration_report.concentrated_isins.length > 0 ? (
                  <div className="space-y-3">
                    {data.isin_concentration_report.concentrated_isins.map((isin) => (
                      <div key={isin.isin} className="border border-gray-200 rounded-lg p-4">
                        <div className="flex items-center justify-between mb-2">
                          <p className="font-semibold text-gray-900">{isin.isin}</p>
                          <span className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded">
                            {isin.percentage_of_clients.toFixed(1)}%
                          </span>
                        </div>
                        <p className="text-sm text-gray-600">
                          Held by {isin.clients_holding.length} client
                          {isin.clients_holding.length !== 1 ? 's' : ''}
                        </p>
                        <div className="mt-2 flex flex-wrap gap-2">
                          {isin.clients_holding.slice(0, 5).map((client) => (
                            <span
                              key={client}
                              className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded"
                            >
                              {client}
                            </span>
                          ))}
                          {isin.clients_holding.length > 5 && (
                            <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded">
                              +{isin.clients_holding.length - 5} more
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-gray-500">No concentrated ISINs found</p>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
