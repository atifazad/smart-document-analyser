import { useState, useRef } from 'react';

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<any[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const progressIntervalRef = useRef<number | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setResults(null);
      setError(null);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      setResults(null);
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

  const startProgressSimulation = () => {
    setProgress(0);
    let currentProgress = 0;
    
    // Phase 1: Upload (0-30%)
    const uploadPhase = setInterval(() => {
      currentProgress += 2;
      if (currentProgress <= 30) {
        setProgress(currentProgress);
      } else {
        clearInterval(uploadPhase);
        
        // Phase 2: Processing (30-90%)
        const processingPhase = setInterval(() => {
          currentProgress += 1;
          if (currentProgress <= 90) {
            setProgress(currentProgress);
          } else {
            clearInterval(processingPhase);
            
            // Phase 3: Finalizing (90-100%)
            const finalizingPhase = setInterval(() => {
              currentProgress += 0.5;
              if (currentProgress <= 100) {
                setProgress(currentProgress);
              } else {
                clearInterval(finalizingPhase);
              }
            }, 100);
          }
        }, 200);
      }
    }, 100);
  };

  const stopProgressSimulation = () => {
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current);
      progressIntervalRef.current = null;
    }
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    setResults(null);
    
    // Start progress simulation
    startProgressSimulation();
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      const response = await fetch('http://localhost:8000/api/upload', {
        method: 'POST',
        body: formData,
      });
      
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Upload failed');
      }
      
      const data = await response.json();
      setProgress(100);
      setResults(data.results || []);
    } catch (err: any) {
      setError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
      stopProgressSimulation();
    }
  };

  const renderLlavaResult = (llavaResult: any) => {
    if (!llavaResult) return null;
    const response = typeof llavaResult === 'object' && llavaResult.response ? llavaResult.response : llavaResult;
    let duration = 'N/A';
    if (typeof llavaResult === 'object' && llavaResult.total_duration) {
      duration = (llavaResult.total_duration / 1_000_000_000).toFixed(2) + 's';
    }
    return (
      <div className="mb-3">
        <div className="flex items-center gap-3 mb-1">
          <span className="font-semibold text-blue-700">Visual Analysis</span>
          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">Processing time: {duration}</span>
        </div>
        <div className="text-gray-800 whitespace-pre-wrap text-sm bg-gray-50 p-2 rounded">
          {response}
        </div>
      </div>
    );
  };

  const renderTextAnalysis = (textAnalysis: any) => {
    if (!textAnalysis || textAnalysis.error) return null;
    
    return (
      <div className="space-y-4">
        {/* Summary */}
        {textAnalysis.summary && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <h3 className="font-semibold text-green-800 mb-2">Summary</h3>
            <div className="text-sm text-green-700 whitespace-pre-wrap">
              {textAnalysis.summary.summary}
            </div>
            <div className="text-xs text-green-600 mt-2">
              Compression: {textAnalysis.summary.compression_ratio}x
            </div>
          </div>
        )}

        {/* Structured Data */}
        {textAnalysis.structured_data && !textAnalysis.structured_data.error && (
          <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
            <h3 className="font-semibold text-purple-800 mb-2">Structured Data</h3>
            <pre className="text-xs text-purple-700 bg-purple-100 p-2 rounded overflow-x-auto">
              {JSON.stringify(textAnalysis.structured_data, null, 2)}
            </pre>
          </div>
        )}

        {/* Action Items */}
        {textAnalysis.action_items && !textAnalysis.action_items.error && textAnalysis.action_items.action_items && (
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <h3 className="font-semibold text-orange-800 mb-2">Action Items</h3>
            <div className="space-y-2">
              {textAnalysis.action_items.action_items.map((item: any, idx: number) => (
                <div key={idx} className="flex items-start gap-2 text-sm">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    item.priority === 'high' ? 'bg-red-100 text-red-800' :
                    item.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {item.priority || 'medium'}
                  </span>
                  <span className="text-orange-700">{item.action}</span>
                  {item.assignee && (
                    <span className="text-xs text-orange-600">→ {item.assignee}</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="min-h-screen w-screen flex flex-col items-center justify-center bg-gradient-to-br from-gray-50 to-blue-50 relative">
      <div className="flex-1 flex items-center justify-center w-full">
        <div className="bg-white rounded-2xl shadow-xl p-10 w-full max-w-4xl flex flex-col gap-8">
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
            {uploading ? 'Processing...' : 'Upload & Process'}
          </button>
          {uploading && (
            <div className="w-full">
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Processing document...</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2.5">
                <div
                  className="bg-blue-600 h-2.5 rounded-full transition-all duration-300 ease-out"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
            </div>
          )}
          {results && results.length > 0 && (
            <div className="flex flex-col gap-6 mt-4">
              {results.map((res, idx) => (
                <div key={idx} className="bg-gray-50 border border-gray-200 rounded-xl p-6 shadow-sm">
                  <div className="font-semibold text-blue-700 mb-3 text-lg">
                    Image: {res.image}
                    {res.enhanced_image && res.enhanced_image !== res.image && (
                      <span className="text-sm text-gray-500 ml-2">(Enhanced: {res.enhanced_image})</span>
                    )}
                  </div>
                  {renderLlavaResult(res.llava_result)}
                  {res.llava_error && (
                    <div className="mb-2 text-red-700 text-sm">Error: {res.llava_error}</div>
                  )}
                  {renderTextAnalysis(res.text_analysis)}
                  {res.ocr_error && (
                    <div className="mb-2 text-red-700 text-sm">OCR Error: {res.ocr_error}</div>
                  )}
                </div>
              ))}
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
