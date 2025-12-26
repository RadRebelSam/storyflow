
import React, { useState } from 'react';
import { X, Mic, Search, ExternalLink, Play } from 'lucide-react';
import axios from 'axios';

const PodcastModal = ({ isOpen, onClose, onSelect }) => {
    const [rssUrl, setRssUrl] = useState('');
    const [loading, setLoading] = useState(false);
    const [feedData, setFeedData] = useState(null);
    const [error, setError] = useState(null);

    const handleFetch = async () => {
        if (!rssUrl) return;
        setLoading(true);
        setError(null);
        setFeedData(null);

        try {
            const res = await axios.post('http://localhost:8000/tools/rss-feed', { url: rssUrl });
            if (res.data.error) {
                setError(res.data.error);
            } else {
                setFeedData(res.data);
            }
        } catch (err) {
            setError(err.response?.data?.detail || "Failed to fetch feed.");
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') handleFetch();
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
                width: '90%', maxWidth: '700px',
                maxHeight: '80vh',
                border: '1px solid #27272a',
                position: 'relative',
                display: 'flex', flexDirection: 'column'
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

                <h2 style={{ marginTop: 0, marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <Mic size={24} color="#a855f7" /> Podcast Browser
                </h2>

                {/* Input Area */}
                <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
                    <input
                        type="text"
                        placeholder="Paste RSS Feed URL (e.g. https://feeds.simplecast.com/...)"
                        value={rssUrl}
                        onChange={(e) => setRssUrl(e.target.value)}
                        onKeyDown={handleKeyDown}
                        style={{
                            flex: 1, padding: '0.75rem', borderRadius: '8px',
                            background: '#27272a', border: '1px solid #3f3f46', color: 'white'
                        }}
                    />
                </ div>
                <p style={{ marginTop: '-1rem', marginBottom: '1.5rem', fontSize: '0.8rem', color: '#a1a1aa' }}>
                    *Supported formats: RSS Feeds usually ending in .xml
                </p>
                <div style={{ display: 'none' }}>
                    {/* Hidden button to keep layout reference if needed for other styles, 
                           but actually we want the button next to input. 
                           Let's restructure the input container.
                       */}
                </div>

                {/* Error */}
                {error && (
                    <div style={{ color: '#ef4444', marginBottom: '1rem', background: 'rgba(239,68,68,0.1)', padding: '0.5rem', borderRadius: '4px' }}>
                        Error: {error}
                    </div>
                )}

                {/* Results List */}
                {feedData && (
                    <div style={{ flex: 1, overflowY: 'auto', borderTop: '1px solid #27272a', paddingTop: '1rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
                            {feedData.image && <img src={feedData.image} alt="Podcast Cover" style={{ width: 60, height: 60, borderRadius: 8, objectFit: 'cover' }} />}
                            <div>
                                <h3 style={{ margin: 0, fontSize: '1.1rem' }}>{feedData.title}</h3>
                                <p style={{ margin: 0, color: '#a1a1aa', fontSize: '0.9rem' }}>{feedData.episodes.length} Episodes found</p>
                            </div>
                        </div>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                            {feedData.episodes.map((ep, idx) => (
                                <div key={idx} style={{
                                    background: '#27272a', padding: '1rem', borderRadius: '8px',
                                    display: 'flex', alignItems: 'center', gap: '1rem',
                                    transition: '0.2s'
                                }}>
                                    <div style={{ flex: 1 }}>
                                        <div style={{ fontWeight: 'bold', marginBottom: '0.25rem' }}>{ep.title}</div>
                                        <div style={{ fontSize: '0.8rem', color: '#a1a1aa' }}>
                                            {ep.published} • {ep.duration ? ep.duration : 'Unknown Duration'}
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => {
                                            onSelect(ep.audio_url);
                                            onClose();
                                        }}
                                        style={{
                                            background: '#3f3f46', border: 'none', color: 'white',
                                            padding: '0.5rem 1rem', borderRadius: '6px', cursor: 'pointer',
                                            display: 'flex', alignItems: 'center', gap: '0.5rem'
                                        }}
                                        className="hover-btn"
                                    >
                                        <Play size={16} /> Select
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default PodcastModal;
