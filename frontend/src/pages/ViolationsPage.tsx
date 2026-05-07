/**
 * Violations page - displays all business rule violations
 */

import React, { useMemo } from 'react';
import { AlertTriangle, ArrowLeft, Filter } from 'lucide-react';
import { useViolations } from '../hooks/useViolations';
import { Spinner } from '../components/Spinner';
import { DataTable } from '../components/DataTable';
import { Violation, RuleType } from '../types';
import { useState } from 'react';

interface ViolationsPageProps {
  onBack: () => void;
}

const ruleColors: Record<RuleType, string> = {
  'Day Trading': 'bg-yellow-100 text-yellow-800',
  'Risk Concentration': 'bg-red-100 text-red-800',
  'Sell Before Buy': 'bg-orange-100 text-orange-800',
  'Invalid Values': 'bg-blue-100 text-blue-800',
};

export const ViolationsPage: React.FC<ViolationsPageProps> = ({ onBack }) => {
  const { violations, isLoading, error } = useViolations();
  const [selectedRule, setSelectedRule] = useState<RuleType | 'all'>('all');

  const filteredViolations = useMemo(() => {
    if (selectedRule === 'all') return violations;
    return violations.filter((v) => v.rule_broken === selectedRule);
  }, [violations, selectedRule]);

  const violationColumns = [
    { key: 'client_id' as const, label: 'Client ID', width: 'w-24' },
    { key: 'transaction_id' as const, label: 'Transaction ID' },
    {
      key: 'rule_broken' as const,
      label: 'Rule',
      render: (value: RuleType) => (
        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${ruleColors[value]}`}>
          {value}
        </span>
      ),
    },
    { key: 'description' as const, label: 'Description' },
    {
      key: 'timestamp' as const,
      label: 'Date',
      render: (value: string) => new Date(value).toLocaleDateString(),
    },
  ];

  const ruleOptions: RuleType[] = [
    'Day Trading',
    'Risk Concentration',
    'Sell Before Buy',
    'Invalid Values',
  ];

  const ruleCounts = useMemo(() => {
    const counts: Record<RuleType | 'all', number> = {
      all: violations.length,
      'Day Trading': 0,
      'Risk Concentration': 0,
      'Sell Before Buy': 0,
      'Invalid Values': 0,
    };

    violations.forEach((v) => {
      counts[v.rule_broken]++;
    });

    return counts;
  }, [violations]);

  if (isLoading) return <Spinner message="Loading violations..." />;

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
              <AlertTriangle className="w-7 h-7 text-red-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Violations</h1>
                <p className="text-gray-600 text-sm">
                  {violations.length} violation{violations.length !== 1 ? 's' : ''} detected
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

        {/* Filter Tabs */}
        <div className="mb-6 bg-white rounded-lg shadow p-4">
          <div className="flex items-center gap-2 mb-4">
            <Filter className="w-5 h-5 text-gray-600" />
            <h2 className="font-semibold text-gray-900">Filter by Rule</h2>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setSelectedRule('all')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                selectedRule === 'all'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              All ({ruleCounts.all})
            </button>
            {ruleOptions.map((rule) => (
              <button
                key={rule}
                onClick={() => setSelectedRule(rule)}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  selectedRule === rule
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {rule} ({ruleCounts[rule]})
              </button>
            ))}
          </div>
        </div>

        {/* Violations Table */}
        <div className="bg-white rounded-lg shadow">
          {filteredViolations.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-center">
              <AlertTriangle className="w-12 h-12 text-gray-300 mb-3" />
              <p className="text-gray-500">No violations found</p>
            </div>
          ) : (
            <div className="p-4">
              <DataTable
                columns={violationColumns}
                data={filteredViolations as Violation[]}
                keyExtractor={(row) => row.id}
              />
            </div>
          )}
        </div>

        {/* Summary Stats */}
        {violations.length > 0 && (
          <div className="mt-6 grid grid-cols-2 md:grid-cols-4 gap-4">
            {ruleOptions.map((rule) => (
              <div key={rule} className={`rounded-lg p-4 ${ruleColors[rule]}`}>
                <p className="text-sm font-medium opacity-75">{rule}</p>
                <p className="text-2xl font-bold">{ruleCounts[rule]}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
