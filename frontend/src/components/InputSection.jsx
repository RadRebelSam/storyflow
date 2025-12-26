import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Play, Upload, MessageSquare, Mic, AlertCircle, FileText, Settings, Type, Sparkles } from 'lucide-react';
import SettingsModal from './SettingsModal';
import PodcastModal from './PodcastModal';

const InputSection = ({ onAnalyze, loading, progress }) => {
  const [url, setUrl] = useState('');
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('');
  const [customModelId, setCustomModelId] = useState('');
  const [error, setError] = useState('');
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isPodcastOpen, setIsPodcastOpen] = useState(false);

  // Settings for LLM
  const [llmProvider, setLlmProvider] = useState('ai-builders');

  // Hardcoded model options per provider
  const MODEL_OPTIONS = {
    'openai': [
      { id: 'gpt-4o', description: 'GPT-4o (Smartest)' },
      { id: 'gpt-4-turbo', description: 'GPT-4 Turbo' },
      { id: 'gpt-3.5-turbo', description: 'GPT-3.5 Turbo (Fast)' },
      { id: 'custom', description: 'Type Custom Model ID...' }
    ],
    'anthropic': [
      { id: 'claude-3-5-sonnet-20240620', description: 'Claude 3.5 Sonnet' },
      { id: 'claude-3-opus-20240229', description: 'Claude 3 Opus' },
      { id: 'claude-3-haiku-20240307', description: 'Claude 3 Haiku' },
      { id: 'custom', description: 'Type Custom Model ID...' }
    ],
    'gemini': [
      { id: 'gemini-1.5-pro', description: 'Gemini 1.5 Pro' },
      { id: 'gemini-1.5-flash', description: 'Gemini 1.5 Flash' },
      { id: 'custom', description: 'Type Custom Model ID...' }
    ],
    'deepseek': [
      { id: 'deepseek-chat', description: 'DeepSeek Chat' },
      { id: 'deepseek-coder', description: 'DeepSeek Coder' },
      { id: 'custom', description: 'Type Custom Model ID...' }
    ],
    'openrouter': [
      { id: 'openai/gpt-4o', description: 'GPT-4o (via OpenRouter)' },
      { id: 'anthropic/claude-3.5-sonnet', description: 'Claude 3.5 Sonnet (via OpenRouter)' },
      { id: 'google/gemini-pro-1.5', description: 'Gemini 1.5 Pro (via OpenRouter)' },
      { id: 'custom', description: 'Type Custom Model ID...' }
    ],
    'ai-builders': [] // Will be fetched from backend
  };

  const loadConfig = async () => {
    const stored = localStorage.getItem('llm_settings');
    let currentProvider = 'ai-builders';
    if (stored) {
      const parsed = JSON.parse(stored);
      currentProvider = parsed.provider || 'ai-builders';
    }
    setLlmProvider(currentProvider);

    if (currentProvider === 'ai-builders') {
      // Fetch from backend as before
      try {
        const response = await axios.get('http://localhost:8000/models', { timeout: 5000 });
        setModels(response.data.data);
        setSelectedModel(prev => prev || 'gpt-5');
      } catch (err) {
        console.error(err);
        setModels([{ id: 'gpt-5', description: 'Default' }]);
      }
    } else {
      // Use local static list
      const options = MODEL_OPTIONS[currentProvider] || [];
      setModels(options);
      // Set default if current selection is invalid for this provider
      if (options.length > 0) {
        setSelectedModel(options[0].id);
      }
    }
  };

  useEffect(() => {
    loadConfig();
  }, [isSettingsOpen]); // Reload when settings close


  const handleSubmit = (e) => {
    e.preventDefault();
    if (!url && !manualText) return;

    // Read Provider Config from LocalStorage
    let providerConfig = null;
    let transcriptionConfig = null;
    const storedConfig = localStorage.getItem('llm_settings');
    if (storedConfig) {
      const parsed = JSON.parse(storedConfig);
      providerConfig = {
        provider: parsed.provider,
        api_key: parsed.apiKey,
        base_url: parsed.baseUrl
      };
      transcriptionConfig = {
        transcription_provider: parsed.transcriptionProvider,
        deepgram_key: parsed.deepgramKey,
        openai_api_key: parsed.whisperKey || (parsed.provider === 'openai' ? parsed.apiKey : null),
        grok_api_key: parsed.grokKey
      };
    }

    const finalModel = selectedModel === 'custom' ? customModelId : selectedModel;
    if (!finalModel) {
      setError("Please select or enter a valid model.");
      return;
    }

    if (inputType === 'url') {
      onAnalyze({ url, model: finalModel, provider_config: providerConfig, transcription_config: transcriptionConfig });
    } else {
      onAnalyze({ transcript_text: manualText, model: finalModel, provider_config: providerConfig, transcription_config: transcriptionConfig });
    }
  };

  const [inputType, setInputType] = useState('url'); // 'url' or 'text'
  const [manualText, setManualText] = useState('');
  const [uploading, setUploading] = useState(false);

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await axios.post('http://localhost:8000/parse_file', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      setManualText(response.data.text);
    } catch (err) {
      console.error("Upload failed", err);
      setError("Failed to parse file. Please try a valid .txt, .pdf or .srt file.");
    } finally {
      setUploading(false);
      // Reset file input value so same file can be selected again if needed
      e.target.value = null;
    }
  };

  return (
    <div className="input-section" style={{
      textAlign: 'center',
      padding: '4rem 0',
      borderBottom: '1px solid var(--border-color)',
      background: 'radial-gradient(circle at center, rgba(139, 92, 246, 0.1) 0%, transparent 70%)'
    }}>
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
      />

      <PodcastModal
        isOpen={isPodcastOpen}
        onClose={() => setIsPodcastOpen(false)}
        onSelect={(url) => {
          setInputType('url');
          setUrl(url);
        }}
      />

      <div className="container" style={{ maxWidth: '800px', position: 'relative' }}>

        {/* Settings Button */}
        <button
          onClick={() => setIsSettingsOpen(true)}
          style={{
            position: 'absolute', top: 0, right: 0,
            background: 'rgba(255,255,255,0.05)', border: '1px solid var(--border-color)',
            borderRadius: '8px', padding: '0.5rem',
            color: 'var(--text-secondary)', cursor: 'pointer',
            display: 'flex', alignItems: 'center', gap: '0.5rem',
            transition: 'all 0.2s',
            zIndex: 10
          }}
          title="Configure AI Provider"
        >
          <Settings size={20} />
        </button>

        <h1 style={{
          fontSize: '3.5rem',
          fontWeight: '800',
          lineHeight: '1.2',
          marginBottom: '1rem',
          background: 'linear-gradient(to right, #fff, #a1a1aa)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }}>
          StoryFlow
        </h1>
        <p style={{
          color: 'var(--text-secondary)',
          fontSize: '1.25rem',
          marginBottom: '2.5rem'
        }}>
          Decode the art of conversation. Analyze long-form podcasts instantly.
        </p>

        {error && <div style={{ color: '#ef4444', marginBottom: '1rem' }}>{error}</div>}

        {/* Toggle Switch */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginBottom: '1.5rem' }}>
          <button
            type="button"
            className={inputType === 'url' ? 'btn-primary' : 'btn-secondary'}
            onClick={() => setInputType('url')}
          >
            YouTube / Audio Link
          </button>

          <button
            type="button"
            className="btn-secondary"
            onClick={() => setIsPodcastOpen(true)}
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
          >
            <Mic size={16} /> Podcast Browser
          </button>

          <button
            type="button"
            className={inputType === 'text' ? 'btn-primary' : 'btn-secondary'}
            onClick={() => setInputType('text')}
          >
            Start from Text
          </button>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: '1rem', flexDirection: 'column' }}>

          {inputType === 'url' ? (
            <div style={{ display: 'flex', gap: '1rem' }}>
              <input
                type="text"
                placeholder="Paste YouTube link or audio URL (e.g., .mp3)..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                style={{
                  flex: 1,
                  padding: '1rem 1.5rem',
                  borderRadius: '12px',
                  border: '1px solid var(--border-color)',
                  backgroundColor: 'rgba(255,255,255,0.05)',
                  color: 'white',
                  fontSize: '1rem',
                  outline: 'none'
                }}
              />
            </div>
          ) : (
            <div style={{ position: 'relative' }}>
              <textarea
                placeholder="Paste full transcript here or upload a file (txt, pdf, srt)..."
                value={manualText}
                onChange={(e) => setManualText(e.target.value)}
                rows={10}
                style={{
                  width: '100%',
                  padding: '1rem',
                  paddingBottom: '3rem', // Space for upload button
                  borderRadius: '12px',
                  border: '1px solid var(--border-color)',
                  backgroundColor: 'rgba(255,255,255,0.05)',
                  color: 'white',
                  fontSize: '1rem',
                  outline: 'none',
                  resize: 'vertical',
                  fontFamily: 'inherit'
                }}
              />

              <div style={{ position: 'absolute', bottom: '1rem', right: '1rem', display: 'flex', gap: '0.5rem' }}>
                <label
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    background: 'rgba(255,255,255,0.1)',
                    padding: '0.25rem 0.75rem',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    fontSize: '0.85rem',
                    color: 'var(--text-secondary)',
                    border: '1px dashed var(--border-color)',
                    transition: 'all 0.2s'
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.2)'}
                  onMouseLeave={(e) => e.currentTarget.style.background = 'rgba(255,255,255,0.1)'}
                >
                  {uploading ? 'Parsing...' : 'Upload File'}
                  <input
                    type="file"
                    accept=".txt,.pdf,.srt"
                    style={{ display: 'none' }}
                    onChange={handleFileUpload}
                    disabled={uploading}
                  />
                </label>
              </div>
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem' }}>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              style={{
                padding: '0 1.5rem',
                borderRadius: '12px',
                border: '1px solid var(--border-color)',
                backgroundColor: 'rgba(255,255,255,0.05)',
                color: 'white',
                cursor: 'pointer',
                height: '50px'
              }}
            >
              {models.map(model => (
                <option
                  key={model.id}
                  value={model.id}
                  style={{
                    backgroundColor: '#18181b', // Dark background to match theme
                    color: 'white'              // White text
                  }}
                >
                  {model.description || model.id}
                </option>
              ))}
            </select>

            {selectedModel === 'custom' && (
              <input
                type="text"
                placeholder="Enter Model ID (e.g. gpt-4-turbo)"
                value={customModelId}
                onChange={(e) => setCustomModelId(e.target.value)}
                style={{
                  padding: '0 1rem',
                  borderRadius: '12px',
                  border: '1px solid var(--border-color)',
                  backgroundColor: 'rgba(255,255,255,0.05)',
                  color: 'white',
                  height: '50px',
                  width: '200px'
                }}
              />
            )}

            <button
              type="submit"
              className="btn-primary"
              disabled={loading}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem',
                fontSize: '1.1rem',
                padding: '0 2rem',
                height: '50px',
                minWidth: '200px',
                position: 'relative',
                overflow: 'hidden'
              }}
            >
              {loading ? (
                <div style={{ width: '100%', position: 'relative', zIndex: 2 }}>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', lineHeight: '1' }}>
                    <span style={{ fontSize: '0.9rem', marginBottom: '4px' }}>{progress?.percent || 0}%</span>
                    <span style={{ fontSize: '0.75rem', opacity: 0.8 }}>{progress?.message || 'Processing...'}</span>
                  </div>
                  {/* Progress Overlay */}
                  <div style={{
                    position: 'absolute',
                    left: 0,
                    top: 0,
                    bottom: 0,
                    width: `${progress?.percent || 0}% `,
                    background: 'rgba(255,255,255,0.2)',
                    zIndex: -1,
                    transition: 'width 0.5s ease'
                  }} />
                </div>
              ) : (
                <>Analyze Story <Sparkles size={18} /></>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default InputSection;
