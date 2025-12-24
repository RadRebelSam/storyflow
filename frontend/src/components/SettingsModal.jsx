import React, { useState, useEffect } from 'react';
import { X, Save, Key, Globe, Server } from 'lucide-react';

const PROVIDERS = [
    { id: 'openai', name: 'OpenAI', defaultBaseUrl: 'https://api.openai.com/v1' },
    { id: 'anthropic', name: 'Anthropic', defaultBaseUrl: 'https://api.anthropic.com/v1' },
    { id: 'gemini', name: 'Gemini (Google)', defaultBaseUrl: 'https://generativelanguage.googleapis.com/v1beta' },
    { id: 'deepseek', name: 'DeepSeek', defaultBaseUrl: 'https://api.deepseek.com/v1' },
    { id: 'openrouter', name: 'OpenRouter', defaultBaseUrl: 'https://openrouter.ai/api/v1' },
    { id: 'ai-builders', name: 'AI Builders (Default)', defaultBaseUrl: 'https://space.ai-builders.com/backend/v1' }
];

const SettingsModal = ({ isOpen, onClose }) => {
    const [provider, setProvider] = useState('ai-builders');
    const [apiKey, setApiKey] = useState('');
    const [baseUrl, setBaseUrl] = useState('');

    // Transcription Settings
    const [transcriptionProvider, setTranscriptionProvider] = useState('youtube');
    const [deepgramKey, setDeepgramKey] = useState('');

    // Load settings on open
    useEffect(() => {
        if (isOpen) {
            const storedConfig = localStorage.getItem('llm_settings');
            if (storedConfig) {
                const config = JSON.parse(storedConfig);
                setProvider(config.provider || 'ai-builders');
                setApiKey(config.apiKey || '');
                setBaseUrl(config.baseUrl || '');
                // Load transcription settings
                setTranscriptionProvider(config.transcriptionProvider || 'youtube');
                setDeepgramKey(config.deepgramKey || '');
            } else {
                // Defaults
                setProvider('ai-builders');
                setBaseUrl('https://space.ai-builders.com/backend/v1');
                setTranscriptionProvider('youtube');
            }
        }
    }, [isOpen]);

    const handleProviderChange = (e) => {
        const newProvider = e.target.value;
        setProvider(newProvider);

        // Auto-fill base URL if it's empty or matches another default
        const providerData = PROVIDERS.find(p => p.id === newProvider);
        if (providerData) {
            setBaseUrl(providerData.defaultBaseUrl);
        }
    };

    const handleSave = () => {
        const config = {
            provider, apiKey, baseUrl,
            transcriptionProvider, deepgramKey
        };
        localStorage.setItem('llm_settings', JSON.stringify(config));
        onClose();
    };

    if (!isOpen) return null;

    return (
        <div style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(5px)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            zIndex: 1000
        }}>
            <div style={{
                background: '#0f0f11', border: '1px solid #27272a',
                borderRadius: '16px', width: '90%', maxWidth: '500px',
                padding: '2rem', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
                maxHeight: '90vh', overflowY: 'auto'
            }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2rem' }}>
                    <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold' }}>Settings</h2>
                    <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#71717a', cursor: 'pointer' }}>
                        <X size={24} />
                    </button>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>

                    {/* LLM Section */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        <h3 style={{ fontSize: '1.1rem', color: '#e4e4e7', borderBottom: '1px solid #27272a', paddingBottom: '0.5rem' }}>
                            🧠 AI Model Provider
                        </h3>

                        {/* Provider Select */}
                        <div>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', color: '#a1a1aa' }}>
                                <Server size={16} /> Provider
                            </label>
                            <select
                                value={provider}
                                onChange={handleProviderChange}
                                style={{
                                    width: '100%', padding: '0.75rem', borderRadius: '8px',
                                    background: '#18181b', border: '1px solid #27272a',
                                    color: 'white', outline: 'none'
                                }}
                            >
                                {PROVIDERS.map(p => (
                                    <option key={p.id} value={p.id}>{p.name}</option>
                                ))}
                            </select>
                        </div>

                        {/* API Key Input */}
                        <div>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', color: '#a1a1aa' }}>
                                <Key size={16} /> API Key
                            </label>
                            <input
                                type="password"
                                placeholder="sk-..."
                                value={apiKey}
                                onChange={(e) => setApiKey(e.target.value)}
                                style={{
                                    width: '100%', padding: '0.75rem', borderRadius: '8px',
                                    background: '#18181b', border: '1px solid #27272a',
                                    color: 'white', outline: 'none'
                                }}
                            />
                        </div>

                        {/* Base URL Input */}
                        <div>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', color: '#a1a1aa' }}>
                                <Globe size={16} /> Base URL
                            </label>
                            <input
                                type="text"
                                value={baseUrl}
                                onChange={(e) => setBaseUrl(e.target.value)}
                                style={{
                                    width: '100%', padding: '0.75rem', borderRadius: '8px',
                                    background: '#18181b', border: '1px solid #27272a',
                                    color: 'white', outline: 'none'
                                }}
                            />
                        </div>
                    </div>

                    {/* Transcription Section */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        <h3 style={{ fontSize: '1.1rem', color: '#e4e4e7', borderBottom: '1px solid #27272a', paddingBottom: '0.5rem' }}>
                            🎙️ Transcription & Diarization
                        </h3>
                        <div>
                            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', color: '#a1a1aa' }}>
                                <Server size={16} /> Transcriber
                            </label>
                            <select
                                value={transcriptionProvider}
                                onChange={(e) => setTranscriptionProvider(e.target.value)}
                                style={{
                                    width: '100%', padding: '0.75rem', borderRadius: '8px',
                                    background: '#18181b', border: '1px solid #27272a',
                                    color: 'white', outline: 'none'
                                }}
                            >
                                <option value="youtube">YouTube Captions (Free, No Host/Guest separation)</option>
                                <option value="deepgram">Deepgram (Paid, Identifies Speakers)</option>
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
                    </div>
                </div>

                <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
                    <button
                        onClick={onClose}
                        style={{
                            padding: '0.75rem 1.5rem', borderRadius: '8px',
                            background: 'transparent', border: '1px solid #27272a',
                            color: 'white', cursor: 'pointer'
                        }}
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSave}
                        style={{
                            padding: '0.75rem 1.5rem', borderRadius: '8px',
                            background: '#8b5cf6', border: 'none',
                            color: 'white', cursor: 'pointer', fontWeight: 'bold',
                            display: 'flex', alignItems: 'center', gap: '0.5rem'
                        }}
                    >
                        <Save size={18} /> Save Settings
                    </button>
                </div>

            </div>
        </div>
    );
};

export default SettingsModal;
