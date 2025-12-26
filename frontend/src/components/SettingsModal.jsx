
import React, { useState, useEffect } from 'react';
import { X, Key } from 'lucide-react';

const SettingsModal = ({ isOpen, onClose }) => {
    const [provider, setProvider] = useState('openai');
    const [apiKey, setApiKey] = useState('');
    const [baseUrl, setBaseUrl] = useState('');

    // Transcription Settings
    const [transcriptionProvider, setTranscriptionProvider] = useState('youtube');
    const [deepgramKey, setDeepgramKey] = useState('');
    const [whisperKey, setWhisperKey] = useState('');
    const [uniscribeKey, setUniscribeKey] = useState('');

    // Reuse OpenAI key for Whisper if same provider? 
    // Simplify: "OpenAI Whisper" option uses the main OpenAI key if available, or we could add a field.
    // Let's rely on the main "API Key" field if provider is OpenAI, or maybe a dedicated field?
    // User requested "add openai whisper as an option for transcriber".
    // Let's try to keep it simple: if Transcriber is Whisper, use the main LLM key ?? 
    // No, LLM provider might be Anthropic. So we need a separate key field potentially.
    // Actually, let's keep it clean: 
    // If Transcriber == OpenAI Whisper, show "OpenAI API Key" field specific to transcription?
    // Or just rename "Deepgram API Key" to "Transcription API Key" and treat it generic?
    // Let's do dedicated fields to avoid confusion.



    useEffect(() => {
        if (isOpen) {
            const stored = localStorage.getItem('llm_settings');
            if (stored) {
                const parsed = JSON.parse(stored);
                setProvider(parsed.provider || 'openai');
                setApiKey(parsed.apiKey || '');
                setBaseUrl(parsed.baseUrl || '');
                setTranscriptionProvider(parsed.transcriptionProvider || 'youtube');
                setDeepgramKey(parsed.deepgramKey || '');
                setWhisperKey(parsed.whisperKey || '');
                setUniscribeKey(parsed.uniscribeKey || '');
            }
        }
    }, [isOpen]);

    const handleSave = () => {
        // If using Whisper but no key provided, maybe fallback to main key if provider is OpenAI?
        // Let's implement that logic in the backend or handleSubmit?
        // Better to be explicit here.

        // Construct config
        // We'll save whisperKey but mostly likely use it as 'openai_api_key' for transcription config

        // For the backend input section:
        // It reads 'llm_settings'. 
        // We need to store it there.

        const settings = {
            provider,
            apiKey,
            baseUrl,
            transcriptionProvider,
            deepgramKey,
            whisperKey,
            uniscribeKey
        };

        localStorage.setItem('llm_settings', JSON.stringify(settings));
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.8)', zIndex: 1000,
            display: 'flex', alignItems: 'center', justifyContent: 'center'
        }}>
            <div style={{
                background: '#18181b',
                padding: '2rem',
                borderRadius: '12px',
                width: '90%', maxWidth: '500px',
                border: '1px solid #27272a',
                position: 'relative'
            }}>
                <button
                    onClick={onClose}
                    style={{
                        position: 'absolute', top: '1rem', right: '1rem',
                        background: 'none', border: 'none', color: '#a1a1aa', cursor: 'pointer'
                    }}
                >
                    <X size={20} />
                </button>

                <h2 style={{ marginTop: 0, marginBottom: '2rem' }}>⚙️ Settings</h2>

                {/* LLM Section */}
                <div style={{ marginBottom: '2rem' }}>
                    <h3 style={{ fontSize: '1rem', color: '#a1a1aa', marginBottom: '1rem' }}>Brain (LLM)</h3>

                    <div style={{ marginBottom: '1rem' }}>
                        <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Provider</label>
                        <select
                            value={provider}
                            onChange={(e) => setProvider(e.target.value)}
                            style={{
                                width: '100%', padding: '0.75rem', borderRadius: '8px',
                                background: '#27272a', border: '1px solid #3f3f46', color: 'white'
                            }}
                        >
                            <option value="openai">OpenAI</option>
                            <option value="anthropic">Anthropic</option>
                            <option value="gemini">Google Gemini</option>
                            <option value="deepseek">DeepSeek</option>
                            <option value="openrouter">OpenRouter</option>
                            <option value="ai-builders">AI Builders (Custom)</option>
                        </select>
                    </div>

                    <div style={{ marginBottom: '1rem' }}>
                        <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>API Key</label>
                        <input
                            type="password"
                            value={apiKey}
                            onChange={(e) => setApiKey(e.target.value)}
                            placeholder="sk-..."
                            style={{
                                width: '100%', padding: '0.75rem', borderRadius: '8px',
                                background: '#27272a', border: '1px solid #3f3f46', color: 'white'
                            }}
                        />
                    </div>

                    {(provider === 'ai-builders' || provider === 'openrouter') && (
                        <div style={{ marginBottom: '1rem' }}>
                            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Base URL (Optional)</label>
                            <input
                                type="text"
                                value={baseUrl}
                                onChange={(e) => setBaseUrl(e.target.value)}
                                placeholder="https://api.example.com/v1"
                                style={{
                                    width: '100%', padding: '0.75rem', borderRadius: '8px',
                                    background: '#27272a', border: '1px solid #3f3f46', color: 'white'
                                }}
                            />
                        </div>
                    )}
                </div>

                {/* Transcription Section */}
                <div style={{ marginBottom: '2rem', borderTop: '1px solid #27272a', paddingTop: '2rem' }}>
                    <h3 style={{ fontSize: '1rem', color: '#a1a1aa', marginBottom: '1rem' }}>Ears (Transcription)</h3>

                    <div style={{ marginBottom: '1rem' }}>
                        <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem' }}>Provider</label>
                        <select
                            value={transcriptionProvider}
                            onChange={(e) => setTranscriptionProvider(e.target.value)}
                            style={{
                                width: '100%', padding: '0.75rem', borderRadius: '8px',
                                background: '#27272a', border: '1px solid #3f3f46', color: 'white'
                            }}
                        >
                            <option value="youtube">YouTube Captions (Free, No Host/Guest separation)</option>
                            <option value="deepgram">Deepgram (Paid, Identifies Speakers)</option>
                            <option value="openai_whisper">OpenAI Whisper (Paid)</option>
                            <option value="uniscribe">Uniscribe (Paid, Beta)</option>
                        </select>
                    </div>

                    {transcriptionProvider === 'deepgram' && (
                        <div>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', color: '#a1a1aa' }}>
                                <Key size={16} /> Deepgram API Key
                            </label>
                            <input
                                type="password"
                                placeholder="Token..."
                                value={deepgramKey}
                                onChange={(e) => setDeepgramKey(e.target.value)}
                                style={{
                                    width: '100%', padding: '0.75rem', borderRadius: '8px',
                                    background: '#18181b', border: '1px solid #27272a',
                                    color: 'white', outline: 'none'
                                }}
                            />
                            <p style={{ fontSize: '0.8rem', color: '#eab308', marginTop: '0.5rem' }}>
                                ⚠️ Requires <b>ffmpeg</b> installed on your PC.
                            </p>
                        </div>
                    )}

                    {transcriptionProvider === 'openai_whisper' && (
                        <div>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', color: '#a1a1aa' }}>
                                <Key size={16} /> OpenAI API Key (Whisper)
                            </label>
                            <input
                                type="password"
                                placeholder="sk-..."
                                value={whisperKey}
                                onChange={(e) => setWhisperKey(e.target.value)}
                                style={{
                                    width: '100%', padding: '0.75rem', borderRadius: '8px',
                                    background: '#18181b', border: '1px solid #27272a',
                                    color: 'white', outline: 'none'
                                }}
                            />
                        </div>
                    )}

                    {transcriptionProvider === 'uniscribe' && (
                        <div>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', color: '#a1a1aa' }}>
                                <Key size={16} /> Uniscribe API Key
                            </label>
                            <input
                                type="password"
                                placeholder="Key..."
                                value={uniscribeKey}
                                onChange={(e) => setUniscribeKey(e.target.value)}
                                style={{
                                    width: '100%', padding: '0.75rem', borderRadius: '8px',
                                    background: '#18181b', border: '1px solid #27272a',
                                    color: 'white', outline: 'none'
                                }}
                            />
                        </div>
                    )}
                </div>

                <button
                    onClick={handleSave}
                    className="btn-primary"
                    style={{ width: '100%' }}
                >
                    Save Configuration
                </button>

            </div>
        </div>
    );
};

export default SettingsModal;
