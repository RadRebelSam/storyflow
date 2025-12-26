import React, { useState } from 'react';
import axios from 'axios';
import InputSection from './components/InputSection';
import AnalysisDashboard from './components/AnalysisDashboard';

import HistorySidebar from './components/HistorySidebar';

function App() {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [progress, setProgress] = useState({ percent: 0, message: 'Starting...' });
  const [refreshHistory, setRefreshHistory] = useState(0); // Trigger to reload history

  const handleHistorySelect = async (key) => {
    setLoading(true);
    setError('');
    setData(null);
    setProgress({ percent: 100, message: "Loading from cache..." });

    try {
      const res = await axios.get(`http://localhost:8000/history/${key}`);
      setData({ meta: res.data.meta, analysis: res.data.result || res.data });
      // Note: Backend might return flat object or wrapped in result. 
      // Cache stores "result" which might contain "key" and "data".
      // Let's check backend: cache_service.get_analysis_by_key returns json.loads(row[0])
      // And analyze stores: result object.
      // So res.data is likely the full result.
      setLoading(false);
    } catch (err) {
      console.error(err);
      setError("Failed to load history item.");
      setLoading(false);
    }
  };


  const handleAnalyze = async (payload) => {
    setLoading(true);
    setError('');
    setData(null);
    setProgress({ percent: 0, message: "Initiating..." });

    try {
      // 1. Start Job
      const response = await axios.post('http://localhost:8000/analyze', payload);
      const { job_id, transcript_preview, meta } = response.data;

      // Store initial data
      const initialData = { meta, transcript: transcript_preview };

      // 2. Poll Logic
      const checkStatus = async () => {
        try {
          const jobRes = await axios.get(`http://localhost:8000/jobs/${job_id}`);
          const job = jobRes.data;

          if (job.status === 'completed') {
            setLoading(false);
            setLoading(false);
            setData({ ...initialData, analysis: job.result });
            setRefreshHistory(prev => prev + 1); // Refresh history list
          } else if (job.status === 'failed') {
            setLoading(false);
            setError(job.error || "Analysis Failed");
          } else {
            setProgress({ percent: job.progress, message: job.message });
            setTimeout(checkStatus, 2000); // Poll every 2s
          }
        } catch (err) {
          console.error("Polling error", err);
          // don't stop loading immediately on network blip, maybe retry?
          // for now simple fail
          setLoading(false);
          setError("Network error checking status. Please verify backend.");
        }
      };

      // Start polling
      checkStatus();

    } catch (err) {
      console.error(err);
      setLoading(false);
      setError(err.response?.data?.detail || "Failed to start analysis");
    }
  };

  return (
    <div className="layout app-layout">
      <HistorySidebar onSelect={handleHistorySelect} refreshTrigger={refreshHistory} />
      <div className="main-content">
        <div className="App">
          <InputSection onAnalyze={handleAnalyze} loading={loading} progress={progress} />

          {error && (
            <div className="container" style={{ marginTop: '2rem', textAlign: 'center' }}>
              <div style={{
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid #ef4444',
                color: '#ef4444',
                padding: '1rem',
                borderRadius: '8px',
                display: 'inline-block'
              }}>
                {error}
              </div>
            </div>
          )}

          {data && <AnalysisDashboard data={data} />}

          {!data && !loading && !error && (
            <div style={{ textAlign: 'center', marginTop: '4rem', color: 'var(--text-secondary)' }}>
              <p>Paste a link above to discover storytelling secrets.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
