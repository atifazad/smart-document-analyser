import { useState, useRef } from 'react';

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setResult(null);
      setError(null);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      setResult(null);
      setError(null);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setProgress(0);
    setResult(null);
    setError(null);
    // TODO: Replace with actual API call
    setTimeout(() => {
      setProgress(100);
      setUploading(false);
      setResult('Sample result: Document processed successfully.');
    }, 1500);
  };

  return (
    <div className="min-h-screen w-screen flex flex-col items-center justify-center bg-gradient-to-br from-gray-50 to-blue-50 relative">
      <div className="flex-1 flex items-center justify-center w-full">
        <div className="bg-white rounded-2xl shadow-xl p-10 w-full max-w-lg flex flex-col gap-8">
          <h1 className="text-3xl font-extrabold text-gray-900 text-center">Smart Document Assistant</h1>
          <div
            className={`border-2 border-dashed rounded-xl p-6 flex flex-col items-center justify-center transition-colors duration-200 cursor-pointer ${dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-gray-100 hover:border-blue-400'}`}
            onClick={() => fileInputRef.current?.click()}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
          >
            <svg className="w-10 h-10 text-blue-400 mb-2" fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5V18a2.25 2.25 0 002.25 2.25h13.5A2.25 2.25 0 0021 18v-1.5M16.5 12l-4.5-4.5m0 0L7.5 12m4.5-4.5V18" />
            </svg>
            <span className="text-gray-700 font-medium">Drag & drop PDF or image here, or <span className="text-blue-600 underline">browse</span></span>
            <input
              type="file"
              accept=".pdf,image/*"
              ref={fileInputRef}
              onChange={handleFileChange}
              className="hidden"
            />
            {file && (
              <div className="mt-3 text-sm text-gray-600 truncate max-w-xs">
                <span className="font-semibold">Selected:</span> {file.name}
              </div>
            )}
          </div>
          <button
            onClick={handleUpload}
            disabled={!file || uploading}
            className="bg-blue-600 text-black py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {uploading ? 'Uploading...' : 'Upload & Process'}
          </button>
          {uploading && (
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div
                className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          )}
          {result && (
            <div className="bg-green-50 border border-green-200 text-green-800 rounded-xl p-4 mt-2">
              <strong>Result:</strong>
              <div>{result}</div>
            </div>
          )}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-800 rounded-xl p-4 mt-2">
              <strong>Error:</strong>
              <div>{error}</div>
            </div>
          )}
        </div>
      </div>
      <footer className="w-full text-center text-gray-400 text-xs pb-4">
        &copy; {new Date().getFullYear()} Smart Document Assistant
      </footer>
    </div>
  );
}

export default App;
