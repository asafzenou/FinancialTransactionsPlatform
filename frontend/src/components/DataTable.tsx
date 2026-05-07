/**
 * Generic data table component for displaying positions and violations
 * Supports dynamic columns and sorting
 */

import React, { useState, useMemo } from 'react';
import { ChevronUp, ChevronDown } from 'lucide-react';

type SortDirection = 'asc' | 'desc' | null;

interface Column<T> {
  key: keyof T;
  label: string;
  render?: (value: T[keyof T], row: T) => React.ReactNode;
  sortable?: boolean;
  width?: string;
}

interface DataTableProps<T extends Record<string, any>> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (row: T, index: number) => string | number;
  noDataMessage?: string;
  striped?: boolean;
}

export const DataTable = <T extends Record<string, any>>({
  columns,
  data,
  keyExtractor,
  noDataMessage = 'No data available',
  striped = true,
}: DataTableProps<T>): React.ReactElement => {
  const [sortColumn, setSortColumn] = useState<keyof T | null>(null);
  const [sortDirection, setSortDirection] = useState<SortDirection>(null);

  const handleSort = (key: keyof T) => {
    if (sortColumn === key) {
      // Cycle through: asc -> desc -> null
      setSortDirection(
        sortDirection === 'asc' ? 'desc' : sortDirection === 'desc' ? null : 'asc'
      );
      if (sortDirection === 'desc') {
        setSortColumn(null);
      }
    } else {
      setSortColumn(key);
      setSortDirection('asc');
    }
  };

  const sortedData = useMemo(() => {
    if (!sortColumn || !sortDirection) return data;

    const sorted = [...data].sort((a, b) => {
      const aValue = a[sortColumn];
      const bValue = b[sortColumn];

      if (aValue == null) return 1;
      if (bValue == null) return -1;

      if (typeof aValue === 'string') {
        return sortDirection === 'asc'
          ? aValue.localeCompare(String(bValue))
          : String(bValue).localeCompare(aValue);
      }

      if (typeof aValue === 'number') {
        return sortDirection === 'asc' ? aValue - (bValue as number) : (bValue as number) - aValue;
      }

      return 0;
    });

    return sorted;
  }, [data, sortColumn, sortDirection]);

  if (data.length === 0) {
    return (
      <div className="text-center py-8">
        <p className="text-gray-500 text-sm">{noDataMessage}</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 border-b border-gray-200">
          <tr>
            {columns.map((column) => (
              <th
                key={String(column.key)}
                className={`px-4 py-3 text-left font-semibold text-gray-900 ${
                  column.width || ''
                }`}
              >
                {column.sortable !== false ? (
                  <button
                    onClick={() => handleSort(column.key)}
                    className="flex items-center gap-2 hover:text-blue-600 transition-colors group"
                  >
                    <span>{column.label}</span>
                    <div className="flex flex-col gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                      <ChevronUp className="w-3 h-3 -mb-1" />
                      <ChevronDown className="w-3 h-3" />
                    </div>
                    {sortColumn === column.key && sortDirection && (
                      <span className="ml-1">
                        {sortDirection === 'asc' ? (
                          <ChevronUp className="w-4 h-4 text-blue-600" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-blue-600" />
                        )}
                      </span>
                    )}
                  </button>
                ) : (
                  <span>{column.label}</span>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sortedData.map((row, index) => (
            <tr
              key={keyExtractor(row, index)}
              className={`border-b border-gray-200 transition-colors hover:bg-gray-50 ${
                striped && index % 2 === 1 ? 'bg-gray-50' : 'bg-white'
              }`}
            >
              {columns.map((column) => {
                const value = row[column.key];
                const renderedValue = column.render ? column.render(value, row) : value;

                return (
                  <td key={`${keyExtractor(row, index)}-${String(column.key)}`} className="px-4 py-3">
                    <span className="text-gray-900">
                      {renderedValue ?? <span className="text-gray-400">—</span>}
                    </span>
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
