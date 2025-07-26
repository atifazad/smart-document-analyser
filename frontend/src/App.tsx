import { useState, useRef } from 'react';

interface Question {
  id: string;
  text: string;
  answer: string;
  timestamp: Date;
}

interface DocumentResult {
  image: string;
  enhanced_image?: string;
  llava_result: any;
  llava_error?: string;
  ocr_text: string;
  ocr_error?: string;
  text_analysis: any;
  document_id?: string;
}

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState<DocumentResult[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'upload' | 'qa' | 'analysis'>('upload');
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [askingQuestion, setAskingQuestion] = useState(false);
  const [selectedDocument, setSelectedDocument] = useState<DocumentResult | null>(null);
  const [processingComplete, setProcessingComplete] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [dragActive, setDragActive] = useState(false);
  const progressIntervalRef = useRef<number | null>(null);
  const [currentPage, setCurrentPage] = useState<number | null>(null);
  const [totalPages, setTotalPages] = useState<number | null>(null);
  const [currentStep, setCurrentStep] = useState<string | null>(null);
  const [stepDescription, setStepDescription] = useState<string>("");

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setResults(null);
      setError(null);
      setQuestions([]);
      setSelectedDocument(null);
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
      setQuestions([]);
      setSelectedDocument(null);
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

  const startProgressTracking = (jobId: string) => {
    setProgress(0);
    setCurrentPage(null);
    setTotalPages(null);
    setCurrentStep(null);
    setStepDescription("");
    
            const pollProgress = async () => {
          try {
            const response = await fetch(`http://localhost:8000/api/jobs/${jobId}`);
            if (response.ok) {
              const jobStatus = await response.json();
              setProgress(jobStatus.progress_percentage || 0);
              setCurrentPage(jobStatus.current_page || null);
              setTotalPages(jobStatus.total_pages || null);
              setCurrentStep(jobStatus.current_step || null);
              setStepDescription(jobStatus.step_description || "");
          
          if (jobStatus.status === 'completed') {
            setResults(jobStatus.results || []);
            if (jobStatus.results && jobStatus.results.length > 0) {
              setSelectedDocument(jobStatus.results[0]);
              setActiveTab('analysis');
              setProcessingComplete(true);
            }
            setUploading(false);
            setProgress(100);
            return true; // Stop polling
          } else if (jobStatus.status === 'failed') {
            setError(jobStatus.error || 'Processing failed');
            setUploading(false);
            return true; // Stop polling
          }
        }
      } catch (error) {
        console.error('Error polling progress:', error);
      }
      return false; // Continue polling
    };
    
    // Poll every 1 second
    const pollInterval = setInterval(async () => {
      const shouldStop = await pollProgress();
      if (shouldStop) {
        clearInterval(pollInterval);
      }
    }, 1000);
    
    // Store the interval reference for cleanup
    progressIntervalRef.current = pollInterval;
  };

  const stopProgressTracking = () => {
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
    setQuestions([]);
    setSelectedDocument(null);
    setProcessingComplete(false);

    try {
      const formData = new FormData();
      formData.append('file', file);
      
      // Use async upload endpoint for real progress tracking
      const response = await fetch('http://localhost:8000/api/upload/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Upload failed');
      }
      
      const data = await response.json();
      
      // Start real progress tracking with the job ID
      if (data.job_id) {
        startProgressTracking(data.job_id);
      } else {
        // Fallback to sync endpoint if no job_id
        const syncResponse = await fetch('http://localhost:8000/api/upload/upload-sync', {
          method: 'POST',
          body: formData,
        });
        
        if (!syncResponse.ok) {
          const err = await syncResponse.json();
          throw new Error(err.detail || 'Upload failed');
        }
        
        const syncData = await syncResponse.json();
        setProgress(100);
        setResults(syncData.results || []);
        if (syncData.results && syncData.results.length > 0) {
          setSelectedDocument(syncData.results[0]);
          setActiveTab('analysis');
          setProcessingComplete(true);
        }
        setUploading(false);
      }
    } catch (err: any) {
      setError(err.message || 'Upload failed');
      setUploading(false);
      stopProgressTracking();
    }
  };

  const askQuestion = async (questionText: string, documentId?: string) => {
    if (!selectedDocument || !questionText.trim()) return;

    setAskingQuestion(true);
    const questionId = Date.now().toString();

    try {
      const response = await fetch('http://localhost:8000/api/analysis/answer-question', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text_content: selectedDocument.ocr_text,
          question: questionText,
          document_id: documentId
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to get answer');
      }
      
      const data = await response.json();
    
      const newQuestion: Question = {
        id: questionId,
        text: questionText,
        answer: data.answer,
        timestamp: new Date()
      };
      
      setQuestions(prev => [newQuestion, ...prev]);
      setCurrentQuestion('');
    } catch (err: any) {
      const errorQuestion: Question = {
        id: questionId,
        text: questionText,
        answer: `Error: ${err.message}`,
        timestamp: new Date()
      };
      setQuestions(prev => [errorQuestion, ...prev]);
    } finally {
      setAskingQuestion(false);
    }
  };

  const handleQuestionSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (currentQuestion.trim() && selectedDocument) {
      askQuestion(currentQuestion.trim(), selectedDocument.document_id);
    }
  };

  const renderLlavaResult = (llavaResult: any, llavaError?: string) => {
    if (!llavaResult && !llavaError) return null;
    
    // If LLaVA is disabled, show a message
    if (llavaError && llavaError.includes("disabled")) {
      return (
        <div className="mb-3">
          <div className="flex items-center gap-3 mb-1">
            <span className="font-semibold text-gray-600">Visual Analysis</span>
            <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded">Disabled for Performance</span>
          </div>
          <div className="text-gray-500 text-sm bg-gray-50 p-2 rounded">
            LLaVA visual analysis has been disabled to improve processing speed. 
            Only OCR text extraction and text analysis are performed.
          </div>
        </div>
      );
    }
    
    // Handle the new response format
    let response = '';
    let duration = 'N/A';
    let model = 'Unknown';
    
    if (typeof llavaResult === 'object') {
      if (llavaResult.response) {
        response = llavaResult.response;
      } else if (typeof llavaResult === 'string') {
        response = llavaResult;
      } else {
        response = JSON.stringify(llavaResult);
      }
      
      if (llavaResult.processing_time) {
        duration = llavaResult.processing_time.toFixed(2) + 's';
      } else if (llavaResult.total_duration) {
        duration = (llavaResult.total_duration / 1_000_000_000).toFixed(2) + 's';
      }
      
      if (llavaResult.model) {
        model = llavaResult.model;
      }
    } else {
      response = String(llavaResult);
    }
    
    return (
      <div className="mb-3">
        <div className="flex items-center gap-3 mb-1">
          <span className="font-semibold text-blue-700">Visual Analysis</span>
          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">Processing time: {duration}</span>
          <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">Model: {model}</span>
        </div>
        <div className="text-gray-800 whitespace-pre-wrap text-sm bg-gray-50 p-2 rounded">
          {response}
        </div>
      </div>
    );
  };

  const renderTextAnalysis = (textAnalysis: any) => {
    if (!textAnalysis || textAnalysis.error) {
      return null;
    }
    return (
      <div className="space-y-4">
        {/* Summary */}
        {textAnalysis.summary && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <h3 className="font-semibold text-green-800 mb-2">Summary</h3>
            <div className="text-sm text-green-700 whitespace-pre-wrap">
              {typeof textAnalysis.summary === 'string'
                ? textAnalysis.summary
                : textAnalysis.summary.summary || textAnalysis.summary.error || 'No summary available'
              }
            </div>
            {textAnalysis.summary.original_length && textAnalysis.summary.summary_length && (
              <div className="text-xs text-green-600 mt-2">
                Compression: {Math.round(textAnalysis.summary.summary_length / textAnalysis.summary.original_length * 100) / 100}x
              </div>
            )}
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
        {textAnalysis.action_items && !textAnalysis.action_items.error && (
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <h3 className="font-semibold text-orange-800 mb-2">Action Items</h3>
            {textAnalysis.action_items.action_items && Array.isArray(textAnalysis.action_items.action_items) ? (
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
            ) : (
              <div className="text-sm text-orange-700">
                {typeof textAnalysis.action_items === 'string'
                  ? textAnalysis.action_items
                  : textAnalysis.action_items.summary || 'No action items available'
                }
              </div>
            )}
          </div>
        )}

        {/* Debug Information */}
        {textAnalysis && (
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <h3 className="font-semibold text-gray-800 mb-2">Debug Info</h3>
            <div className="text-xs text-gray-600">
              <div>Has Summary: {textAnalysis.summary ? 'Yes' : 'No'}</div>
              <div>Has Structured Data: {textAnalysis.structured_data ? 'Yes' : 'No'}</div>
              <div>Has Action Items: {textAnalysis.action_items ? 'Yes' : 'No'}</div>
              <div>Document Type: {textAnalysis.document_type || 'Unknown'}</div>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderQATab = () => (
    <div className="space-y-6">
      {/* Document Selection */}
      {results && results.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Select Document</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {results.map((result, idx) => (
              <button
                key={idx}
                onClick={() => setSelectedDocument(result)}
                className={`p-4 rounded-lg border-2 transition-all ${
                  selectedDocument === result
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-blue-300 hover:bg-gray-50'
                }`}
              >
                <div className="text-sm font-medium text-gray-900">
                  {result.image}
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {result.text_analysis?.document_type || 'Unknown type'}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Q&A Interface */}
      {selectedDocument && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">Ask Questions</h3>
              <p className="text-sm text-gray-600">Get insights about your document</p>
            </div>
          </div>

          {/* Question Input */}
          <form onSubmit={handleQuestionSubmit} className="mb-6">
            <div className="flex gap-3">
              <input
                type="text"
                value={currentQuestion}
                onChange={(e) => setCurrentQuestion(e.target.value)}
                placeholder="Ask a question about your document..."
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={askingQuestion}
              />
              <button
                type="submit"
                disabled={!currentQuestion.trim() || askingQuestion}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {askingQuestion ? (
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Asking...
                  </div>
                ) : (
                  'Ask'
                )}
              </button>
            </div>
          </form>

          {/* Questions and Answers */}
          <div className="space-y-4">
            {questions.map((question) => (
              <div key={question.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <svg className="w-3 h-3 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="flex-1">
                    <p className="font-medium text-gray-900 mb-2">{question.text}</p>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <p className="text-gray-700 whitespace-pre-wrap">{question.answer}</p>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">
                      {question.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="min-h-screen w-screen flex flex-col items-center justify-center bg-gradient-to-br from-gray-50 to-blue-50 relative">
      <div className="flex-1 flex items-center justify-center w-full">
        <div className="bg-white rounded-2xl shadow-xl p-10 w-full max-w-4xl flex flex-col gap-8">
          <h1 className="text-3xl font-extrabold text-gray-900 text-center">Smart Document Assistant</h1>

          {/* Tabs */}
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button
                onClick={() => setActiveTab('upload')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'upload'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Upload Document
              </button>
              <button
                onClick={() => setActiveTab('qa')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'qa'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Q&A Interface
              </button>
              <button
                onClick={() => setActiveTab('analysis')}
                className={`py-2 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'analysis'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                Analysis Results
              </button>
            </nav>
          </div>

          {/* Tab Content */}
          {activeTab === 'upload' && (
            <>
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
                    <span>{stepDescription || "Processing document..."}</span>
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
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-800 rounded-xl p-4 mt-2">
                  <strong>Error:</strong>
                  <div>{error}</div>
                </div>
              )}
              {processingComplete && results && (
                <div className="bg-green-50 border border-green-200 text-green-800 rounded-xl p-4 mt-2">
                  <div className="flex items-center gap-2">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <strong>Processing Complete!</strong>
                  </div>
                  <div className="mt-1 text-sm">
                    Successfully processed {results.length} document{results.length > 1 ? 's' : ''}. 
                    Switch to the "Analysis Results" tab to view the results.
                  </div>
                </div>
              )}
            </>
          )}

          {activeTab === 'qa' && renderQATab()}

          {activeTab === 'analysis' && (
            <>
              {results && results.length > 0 && (
                <div className="flex flex-col gap-6 mt-4">
                  {/* Document Title Header */}
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h2 className="text-xl font-bold text-blue-900 mb-2">
                      📄 Document Analysis Results
                    </h2>
                    <p className="text-blue-700">
                      Processed {results.length} document{results.length > 1 ? 's' : ''} from "{file?.name}"
                    </p>
                  </div>
                  
                  {results.map((res, idx) => (
                    <div key={idx} className="bg-gray-50 border border-gray-200 rounded-xl p-6 shadow-sm">
                      <div className="font-semibold text-blue-700 mb-3 text-lg">
                        Image: {res.image}
                        {res.enhanced_image && res.enhanced_image !== res.image && (
                          <span className="text-sm text-gray-500 ml-2">(Enhanced: {res.enhanced_image})</span>
                        )}
                      </div>
                      {renderLlavaResult(res.llava_result, res.llava_error)}
                      {renderTextAnalysis(res.text_analysis)}
                      {res.ocr_error && (
                        <div className="mb-2 text-red-700 text-sm">OCR Error: {res.ocr_error}</div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </>
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
