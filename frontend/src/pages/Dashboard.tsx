/**
 * Main Dashboard page
 * Displays upload form and navigation to other sections
 */

import React, { useState } from 'react';
import { TrendingUp, AlertTriangle, Users } from 'lucide-react';
import { FileUploader } from '../components/FileUploader';
import { Alert } from '../components/Alert';
import { UploadTransactionResponse, NotificationState } from '../types';

interface DashboardProps {
  onNavigate: (page: string) => void;
}

const navigationCards = [
  {
    id: 'clients',
    title: 'Clients',
    description: 'View all clients in the system',
    icon: Users,
    color: 'bg-blue-50 border-blue-200 text-blue-700 hover:bg-blue-100',
  },
  {
    id: 'violations',
    title: 'Violations',
    description: 'Review business rule violations',
    icon: AlertTriangle,
    color: 'bg-red-50 border-red-200 text-red-700 hover:bg-red-100',
  },
  {
    id: 'analytics',
    title: 'Analytics',
    description: 'View portfolio analytics and insights',
    icon: TrendingUp,
    color: 'bg-green-50 border-green-200 text-green-700 hover:bg-green-100',
  },
];

export const Dashboard: React.FC<DashboardProps> = ({ onNavigate }) => {
  const [notification, setNotification] = useState<NotificationState>({
    message: '',
    type: 'info',
    visible: false,
  });

  const handleUploadSuccess = (response: UploadTransactionResponse) => {
    const message =
      response.status === 'success'
        ? `Successfully imported ${response.summary.successfully_imported} transactions`
        : `Partial import: ${response.summary.successfully_imported} imported, ${response.summary.errors} errors`;

    setNotification({
      message,
      type: response.status === 'success' ? 'success' : 'warning',
      visible: true,
    });
  };

  const handleUploadError = (error: string) => {
    setNotification({
      message: `Upload failed: ${error}`,
      type: 'error',
      visible: true,
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800">
    {/* Header */}
    <div className="bg-white shadow">
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="flex items-center justify-between">
        <div className="flex flex-col items-start">
            {/* Logo Image - Now large and clear */}
            <img 
            src="/logo.png" 
            alt="Lumina Capital" 
            className="h-20 w-auto object-contain mb-1" // הגדלנו את הגובה ל-20
            onError={(e) => {
                (e.target as HTMLImageElement).style.display = 'none';
            }}
            />
            <p className="text-gray-500 text-sm ml-1">Financial Transactions Platform</p>
        </div>
        </div>
    </div>
    </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Notifications */}
        {notification.visible && (
          <div className="mb-6">
            <Alert
              {...notification}
              onClose={() => setNotification((prev) => ({ ...prev, visible: false }))}
            />
          </div>
        )}

        {/* Upload Section */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Upload Transactions</h2>
          <p className="text-gray-600 mb-6">
            Upload your transaction file to process bulk imports. Supported formats: CSV, XLSX, XLS
          </p>
          <FileUploader
            onUploadSuccess={handleUploadSuccess}
            onUploadError={handleUploadError}
          />
        </div>

        {/* Navigation Cards */}
        <div>
          <h2 className="text-xl font-bold text-white mb-6">Quick Access</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {navigationCards.map((card) => {
              const Icon = card.icon;
              return (
                <button
                  key={card.id}
                  onClick={() => onNavigate(card.id)}
                  className={`border-2 rounded-lg p-6 transition-all hover:shadow-lg ${card.color}`}
                >
                  <div className="flex items-start gap-4">
                    <Icon className="w-8 h-8 flex-shrink-0 mt-1" />
                    <div className="text-left">
                      <h3 className="font-semibold text-lg">{card.title}</h3>
                      <p className="text-sm opacity-90 mt-1">{card.description}</p>
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Info Section */}
        <div className="mt-12 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="font-semibold text-blue-900 mb-3">How to Use</h3>
          <ul className="text-sm text-blue-800 space-y-2">
            <li>
              ✓ <strong>Upload:</strong> Select a CSV or Excel file with your transaction data
            </li>
            <li>
              ✓ <strong>View Clients:</strong> See all imported clients and their details
            </li>
            <li>
              ✓ <strong>Check Violations:</strong> Monitor any business rule violations
            </li>
            <li>
              ✓ <strong>Analyze:</strong> Review aggregated analytics and portfolio metrics
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};
