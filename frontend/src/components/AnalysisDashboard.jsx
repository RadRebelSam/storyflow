import React, { useRef } from 'react';
import YouTube from 'react-youtube';
import { PlayCircle, Award, BookOpen, Clock } from 'lucide-react';

const AnalysisDashboard = ({ data }) => {
    const playerRef = useRef(null);

    // Initial checks
    if (!data) return null;
    const { meta, analysis, transcript } = data;

    // Safety check for critical data
    if (!meta || !analysis) {
        return (
            <div className="container" style={{ padding: '2rem', textAlign: 'center' }}>
                <div style={{ padding: '1rem', background: 'rgba(239,68,68,0.1)', color: '#ef4444', borderRadius: '8px', display: 'inline-block' }}>
                    Error: Incomplete analysis data.
                </div>
            </div>
        );
    }

    const onPlayerReady = (event) => {
        playerRef.current = event.target;
    };

    const seekTo = (seconds) => {
        if (playerRef.current) {
            playerRef.current.seekTo(seconds, true);
            playerRef.current.playVideo();
        }
    };

    // Helper for timestamp conversion
    const convertTimestampToSeconds = (timestamp) => {
        if (!timestamp) return 0;
        if (typeof timestamp === 'number') return timestamp;
        const parts = timestamp.split(':').map(Number);
        if (parts.length === 2) return parts[0] * 60 + parts[1];
        if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
        return 0;
    };

    const videoId = meta.video_id;
    const isYouTube = videoId && videoId.length === 11 && !videoId.startsWith('url_');

    return (
        <div className="dashboard container" style={{ paddingBottom: '4rem' }}>

            {/* Header Info */}
            <div style={{ margin: '2rem 0' }}>
                <h2 style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>{meta.title}</h2>
                <div style={{ display: 'flex', gap: '1rem', color: 'var(--text-secondary)' }}>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Clock size={16} /> {meta.duration ? Math.floor(meta.duration / 60) : 0} mins
                    </span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Award size={16} /> {analysis.learning_moments?.length || 0} Key Insights
                    </span>
                </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'minmax(300px, 1fr) 400px', gap: '2rem' }}>

                {/* Left Column: Player & Analysis */}
                <div className="main-content">

                    {/* Media Player Container */}
                    <div className="video-container card" style={{ padding: '0', overflow: 'hidden', marginBottom: '2rem' }}>
                        <div style={{ position: 'relative', paddingBottom: '56.25%', height: 0, background: '#000' }}>
                            {isYouTube ? (
                                <YouTube
                                    videoId={videoId}
                                    opts={{
                                        width: '100%',
                                        height: '100%',
                                        playerVars: { autoplay: 0 }
                                    }}
                                    onReady={onPlayerReady}
                                    style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }}
                                />
                            ) : (
                                <div style={{
                                    position: 'absolute', top: 0, left: 0, width: '100%', height: '100%',
                                    background: 'linear-gradient(135deg, #2e1065 0%, #000000 100%)',
                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                    color: 'white', flexDirection: 'column'
                                }}>
                                    <BookOpen size={48} style={{ opacity: 0.8, marginBottom: '1rem', color: 'var(--accent-purple)' }} />
                                    <h2 style={{ fontSize: '1.8rem', fontWeight: 'bold' }}>
                                        {videoId && videoId.startsWith('url_') ? "Audio Analysis" : "Analysis Complete"}
                                    </h2>
                                    <p style={{ opacity: 0.7, marginTop: '0.5rem' }}>{meta.title}</p>
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="narrative-arc card">
                        <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                            <BookOpen size={20} color="var(--accent-purple)" /> Narrative Arc
                        </h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                            {(Array.isArray(analysis.narrative_arc) ? analysis.narrative_arc : []).map((phase, idx) => (
                                <div key={idx} style={{
                                    display: 'flex',
                                    gap: '1rem',
                                    padding: '1rem',
                                    background: 'rgba(255,255,255,0.03)',
                                    borderRadius: '8px',
                                    borderLeft: '4px solid var(--accent-purple)'
                                }}>
                                    <div style={{ minWidth: '80px', fontWeight: 'bold', color: 'var(--accent-blue)' }}>{phase.start_time}</div>
                                    <div>
                                        <div style={{ fontWeight: 'bold', marginBottom: '0.25rem' }}>{phase.phase}</div>
                                        <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{phase.description}</div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Learning Moments */}
                    <div style={{ marginTop: '2rem' }}>
                        <h3 style={{ marginBottom: '1rem' }}>Learning Moments</h3>
                        <div style={{ display: 'grid', gap: '1rem' }}>
                            {(Array.isArray(analysis.learning_moments) ? analysis.learning_moments : []).map((moment, idx) => (
                                <div key={idx} className="card"
                                    onClick={() => seekTo(convertTimestampToSeconds(moment.timestamp_start))}
                                    style={{ cursor: 'pointer', transition: 'transform 0.2s', borderLeft: '4px solid var(--accent-blue)' }}
                                    onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
                                    onMouseLeave={(e) => e.currentTarget.style.transform = 'translateY(0)'}
                                >
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                        <span style={{
                                            background: 'rgba(59, 130, 246, 0.2)',
                                            color: 'var(--accent-blue)',
                                            padding: '0.25rem 0.5rem',
                                            borderRadius: '4px',
                                            fontSize: '0.8rem',
                                            fontWeight: 'bold'
                                        }}>
                                            {moment.category}
                                        </span>
                                        <span style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{moment.timestamp_start}</span>
                                    </div>
                                    <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '1.1rem' }}>{moment.technique_name}</h4>
                                    <p style={{ fontStyle: 'italic', color: 'var(--text-secondary)', marginBottom: '1rem', borderLeft: '2px solid var(--border-color)', paddingLeft: '0.5rem' }}>
                                        "{moment.quote}"
                                    </p>
                                    <p style={{ fontSize: '0.95rem', lineHeight: '1.6' }}>{moment.analysis}</p>
                                    <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border-color)', fontSize: '0.9rem' }}>
                                        <strong>Takeaway:</strong> {moment.takeaway}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                </div> {/* End Main Content */}

                {/* Right Column: Transcript */}
                <div className="transcript-panel card" style={{ height: 'fit-content', maxHeight: '800px', display: 'flex', flexDirection: 'column' }}>
                    <h3 style={{ marginBottom: '1rem' }}>Transcript</h3>
                    <div style={{ overflowY: 'auto', flex: 1, paddingRight: '0.5rem' }}>
                        {(Array.isArray(transcript) ? transcript : []).map((seg, idx) => (
                            <div key={idx} style={{ marginBottom: '1rem', fontSize: '0.95rem', lineHeight: '1.6' }}
                                onClick={() => seekTo(seg.start_seconds)}>
                                <div style={{ color: 'var(--text-secondary)', fontSize: '0.8rem', marginBottom: '0.2rem', cursor: 'pointer' }}>
                                    {seg.time}
                                </div>
                                <div>{seg.text}</div>
                            </div>
                        ))}
                    </div>
                </div>

            </div>
        </div>
    );
};

export default AnalysisDashboard;
