/**
 * File uploader component with drag-and-drop support
 * Accepts .xlsx, .xls, .csv files
 */

import React, { useRef, useState } from 'react';
import { Upload, FileIcon, CheckCircle, AlertCircle } from 'lucide-react';
import { Spinner } from './Spinner';
import { UploadTransactionResponse } from '../types';

interface FileUploaderProps {
  onUploadSuccess: (response: UploadTransactionResponse) => void;
  onUploadError: (error: string) => void;
}

export const FileUploader: React.FC<FileUploaderProps> = ({
  onUploadSuccess,
  onUploadError,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const ACCEPTED_FORMATS = ['.xlsx', '.xls', '.csv'];
  const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB

  const validateFile = (file: File): string | null => {
    const fileExtension = `.${file.name.split('.').pop()?.toLowerCase()}`;

    if (!ACCEPTED_FORMATS.includes(fileExtension)) {
      return `Invalid file format. Accepted formats: ${ACCEPTED_FORMATS.join(', ')}`;
    }

    if (file.size > MAX_FILE_SIZE) {
      return `File size exceeds ${MAX_FILE_SIZE / 1024 / 1024}MB limit`;
    }

    return null;
  };

  const handleFileSelect = async (file: File) => {
    const error = validateFile(file);
    if (error) {
      onUploadError(error);
      return;
    }

    setSelectedFile(file);

    try {
      setIsLoading(true);

      // Import transactionService here to avoid circular imports
      const { transactionService } = await import('../api/client');
      const response = await transactionService.uploadTransactions(file);

      onUploadSuccess(response);
      setSelectedFile(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Upload failed';
      onUploadError(errorMessage);
    } finally {
      setIsLoading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  if (isLoading) {
    return <Spinner message="Uploading transactions..." />;
  }

  return (
    <div className="w-full">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center transition-colors cursor-pointer
          ${
            isDragging
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 bg-gray-50 hover:bg-gray-100'
          }
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPTED_FORMATS.join(',')}
          onChange={handleFileInputChange}
          className="hidden"
        />

        <div
          onClick={() => fileInputRef.current?.click()}
          className="flex flex-col items-center gap-3"
        >
          <div className="p-3 bg-blue-100 rounded-lg">
            <Upload className="w-6 h-6 text-blue-600" />
          </div>

          <div>
            <p className="text-sm font-medium text-gray-900">
              Drag and drop your transaction file here
            </p>
            <p className="text-xs text-gray-600 mt-1">
              or click to browse. Accepted formats: {ACCEPTED_FORMATS.join(', ')}
            </p>
            <p className="text-xs text-gray-500 mt-2">Maximum file size: 50MB</p>
          </div>

          {selectedFile && (
            <div className="mt-4 flex items-center gap-2 p-2 bg-white rounded border border-gray-200">
              <FileIcon className="w-4 h-4 text-blue-600" />
              <span className="text-sm text-gray-700">{selectedFile.name}</span>
            </div>
          )}
        </div>
      </div>

      <div className="mt-4 text-xs text-gray-600">
        <p className="font-medium mb-2">Expected file format:</p>
        <ul className="list-disc list-inside space-y-1">
          <li>Required columns: ClientId, TransactionId, ISIN, Action, Quantity, Price, Timestamp</li>
          <li>Action must be "buy" or "sell"</li>
          <li>ISIN must be 12 characters</li>
          <li>Quantity and Price must be positive numbers</li>
        </ul>
      </div>
    </div>
  );
};
