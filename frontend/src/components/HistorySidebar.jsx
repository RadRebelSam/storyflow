
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function HistorySidebar({ onSelect, refreshTrigger }) {
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(false);

    // Selection Mode
    const [isSelectionMode, setIsSelectionMode] = useState(false);
    const [selectedKeys, setSelectedKeys] = useState(new Set());

    const fetchHistory = async () => {
        setLoading(true);
        try {
            const res = await fetch("http://localhost:8000/history");
            const data = await res.json();
            setHistory(data.history || []);
        } catch (e) {
            console.error("Failed to load history", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchHistory();
    }, [refreshTrigger]);

    // Handle Checkbox Toggle
    const toggleSelection = (key, e) => {
        e.stopPropagation(); // Prevent item click (load)
        const newSet = new Set(selectedKeys);
        if (newSet.has(key)) {
            newSet.delete(key);
        } else {
            newSet.add(key);
        }
        setSelectedKeys(newSet);
    };

    // Toggle Mode
    const toggleMode = () => {
        setIsSelectionMode(!isSelectionMode);
        setSelectedKeys(new Set());
    };

    // Delete Action
    const [showConfirm, setShowConfirm] = useState(false);

    const handleDelete = async () => {
        if (selectedKeys.size === 0) return;

        if (!showConfirm) {
            setShowConfirm(true);
            setTimeout(() => setShowConfirm(false), 3000); // Reset after 3s
            return;
        }

        try {
            await axios.post("http://localhost:8000/history/delete", { keys: Array.from(selectedKeys) });
            // Refresh
            fetchHistory();
            setIsSelectionMode(false);
            setSelectedKeys(new Set());
            setShowConfirm(false);
        } catch (e) {
            alert("Failed to delete items.");
        }
    };

    const handleSelectAll = () => {
        if (selectedKeys.size === history.length) {
            setSelectedKeys(new Set());
        } else {
            setSelectedKeys(new Set(history.map(item => item.key)));
        }
    };

    return (
        <div className="history-sidebar">
            <div className="history-header">
                <h3>📜 History</h3>
                <button className="icon-btn" onClick={toggleMode} title={isSelectionMode ? "Cancel" : "Manage"}>
                    {isSelectionMode ? "✕" : "⚙️"}
                </button>
            </div>

            {isSelectionMode && (
                <div className="history-toolbar">
                    <button className="text-btn" onClick={handleSelectAll}>
                        {selectedKeys.size === history.length ? "Deselect All" : "Select All"}
                    </button>
                    {selectedKeys.size > 0 && (
                        <button
                            className="delete-btn"
                            onClick={handleDelete}
                            style={{ background: showConfirm ? '#ef4444' : '' }}
                        >
                            {showConfirm ? "Confirm?" : `Delete (${selectedKeys.size})`}
                        </button>
                    )}
                </div>
            )}

            <div className="history-list">
                {loading && <p>Loading...</p>}
                {!loading && history.length === 0 && <p className="empty-state">No history yet.</p>}
                {history.map((item) => (
                    <div
                        key={item.key}
                        className={`history-item ${selectedKeys.has(item.key) ? 'selected' : ''}`}
                        onClick={() => {
                            if (isSelectionMode) {
                                // Simulate checkbox toggle if clicking row in selection mode?
                                // Let's simplify: Row click always loads UNLESS clicking checkbox?
                                // Or better UX for delete mode: Row click selects.
                                const newSet = new Set(selectedKeys);
                                if (newSet.has(item.key)) newSet.delete(item.key);
                                else newSet.add(item.key);
                                setSelectedKeys(newSet);
                            } else {
                                onSelect(item.key);
                            }
                        }}
                    >
                        {isSelectionMode && (
                            <input
                                type="checkbox"
                                checked={selectedKeys.has(item.key)}
                                readOnly // Handled by div click
                                className="history-checkbox"
                            />
                        )}
                        <div className="history-content">
                            <div className="history-title">{item.title}</div>
                            <div className="history-meta">
                                <span>{new Date(item.timestamp).toLocaleDateString()}</span>
                                <span> • {item.model}</span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default HistorySidebar;
