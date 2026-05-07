/**
 * Alert/Notification component for displaying success/error messages
 */

import React, { useState, useEffect } from 'react';
import { AlertCircle, CheckCircle, Info, AlertTriangle, X } from 'lucide-react';
import { NotificationState } from '../types';

interface AlertProps extends NotificationState {
  onClose: () => void;
  autoCloseDuration?: number; // ms
}

const alertStyles = {
  success: {
    bg: 'bg-green-50',
    border: 'border-green-200',
    icon: CheckCircle,
    text: 'text-green-800',
    close: 'text-green-500 hover:text-green-700',
  },
  error: {
    bg: 'bg-red-50',
    border: 'border-red-200',
    icon: AlertCircle,
    text: 'text-red-800',
    close: 'text-red-500 hover:text-red-700',
  },
  warning: {
    bg: 'bg-yellow-50',
    border: 'border-yellow-200',
    icon: AlertTriangle,
    text: 'text-yellow-800',
    close: 'text-yellow-500 hover:text-yellow-700',
  },
  info: {
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    icon: Info,
    text: 'text-blue-800',
    close: 'text-blue-500 hover:text-blue-700',
  },
};

export const Alert: React.FC<AlertProps> = ({
  message,
  type,
  visible,
  onClose,
  autoCloseDuration = 5000,
}) => {
  useEffect(() => {
    if (!visible) return;

    const timer = setTimeout(onClose, autoCloseDuration);
    return () => clearTimeout(timer);
  }, [visible, autoCloseDuration, onClose]);

  if (!visible) return null;

  const style = alertStyles[type];
  const IconComponent = style.icon;

  return (
    <div
      className={`${style.bg} ${style.border} ${style.text} px-4 py-3 rounded-lg border flex items-center gap-3 shadow-md animate-slideDown`}
      role="alert"
    >
      <IconComponent className="w-5 h-5 flex-shrink-0" />
      <p className="flex-1 text-sm font-medium">{message}</p>
      <button
        onClick={onClose}
        className={`${style.close} transition-colors`}
        aria-label="Close alert"
      >
        <X className="w-5 h-5" />
      </button>
    </div>
  );
};
