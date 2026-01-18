import { useState, useRef } from 'react';
import { Upload, FileText, Loader2, X } from 'lucide-react';
import { extractPdf } from '../api/client';
import type { PdfExtractionResult } from '../types';

interface PdfUploaderProps {
  onExtracted: (data: PdfExtractionResult) => void;
}

export default function PdfUploader({ onExtracted }: PdfUploaderProps) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
      setError(null);
    } else {
      setError('Please select a PDF file');
    }
  };

  const handleExtract = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);

    try {
      const result = await extractPdf(file);
      onExtracted(result);
      setFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err) {
      setError('Failed to extract PDF data. Please try again.');
      console.error('PDF extraction error:', err);
    } finally {
      setLoading(false);
    }
  };

  const clearFile = () => {
    setFile(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 p-4">
      <h3 className="text-lg font-medium text-gray-100 mb-3">PDF Auto-Extract</h3>
      <p className="text-sm text-gray-400 mb-4">
        Upload a vendor offer PDF to automatically extract data.
      </p>

      <div className="space-y-3">
        <div className="flex items-center gap-3">
          <label className="flex-1">
            <div className="flex items-center justify-center gap-2 px-4 py-3 bg-gray-700 border-2 border-dashed border-gray-600 rounded-lg cursor-pointer hover:border-blue-500 hover:bg-gray-700/50 transition-colors">
              <Upload className="h-5 w-5 text-gray-400" />
              <span className="text-gray-300">
                {file ? file.name : 'Choose PDF file...'}
              </span>
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept="application/pdf"
              onChange={handleFileChange}
              className="hidden"
            />
          </label>
          {file && (
            <button
              type="button"
              onClick={clearFile}
              className="p-2 text-gray-400 hover:text-gray-200 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          )}
        </div>

        {file && (
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <FileText className="h-4 w-4" />
            <span>{(file.size / 1024).toFixed(1)} KB</span>
          </div>
        )}

        {error && (
          <div className="text-sm text-red-400 bg-red-900/20 px-3 py-2 rounded-lg">
            {error}
          </div>
        )}

        <button
          type="button"
          onClick={handleExtract}
          disabled={!file || loading}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 disabled:cursor-not-allowed rounded-lg font-medium transition-colors"
        >
          {loading ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Extracting...
            </>
          ) : (
            <>
              <FileText className="h-4 w-4" />
              Extract Data
            </>
          )}
        </button>
      </div>
    </div>
  );
}
