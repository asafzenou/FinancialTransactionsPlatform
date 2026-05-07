/**
 * Loading spinner component
 */

import React from 'react';
import { Loader } from 'lucide-react';

interface SpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  message?: string;
  fullScreen?: boolean;
}

const sizeClasses = {
  sm: 'w-4 h-4',
  md: 'w-8 h-8',
  lg: 'w-12 h-12',
};

export const Spinner: React.FC<SpinnerProps> = ({
  size = 'md',
  message,
  fullScreen = false,
}) => {
  const content = (
    <div className="flex items-center justify-center gap-3">
      <Loader className={`${sizeClasses[size]} animate-spin text-blue-600`} />
      {message && <span className="text-sm text-gray-600">{message}</span>}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 bg-white/80 backdrop-blur-sm flex items-center justify-center z-50">
        {content}
      </div>
    );
  }

  return <div className="flex items-center justify-center py-8">{content}</div>;
};
