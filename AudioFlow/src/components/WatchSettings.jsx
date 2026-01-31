import React, { useState, useEffect } from 'react';

const Settings = ({ config, onSaveConfig }) => {
    const [folders, setFolders] = useState(config.watched_folders || []);
    const [apiKey, setApiKey] = useState(config.gemini_api_key || "");
    const [newPath, setNewPath] = useState("");
    const [showKey, setShowKey] = useState(false);

    // Sync if config prop changes externally
    useEffect(() => {
        if (config) {
            setFolders(config.watched_folders || []);
            setApiKey(config.gemini_api_key || "");
        }
    }, [config]);

    const handleSaveGeneral = () => {
        onSaveConfig({ ...config, gemini_api_key: apiKey });
    };

    const handleAddFolder = () => {
        if (newPath && !folders.includes(newPath)) {
            const updated = [...folders, newPath];
            setFolders(updated);
            onSaveConfig({ ...config, watched_folders: updated }); // Auto-save for folders
            setNewPath("");
        }
    };

    const handleRemoveFolder = (path) => {
        const updated = folders.filter(f => f !== path);
        setFolders(updated);
        onSaveConfig({ ...config, watched_folders: updated });
    };

    const maskKey = (key) => {
        if (!key) return "";
        if (key.length <= 8) return "********";
        return "..." + key.slice(-4);
    };

    return (
        <div style={{ padding: '20px', margin: '0 20px' }}>
            <h1 style={{ marginBottom: '30px', borderBottom: '1px solid #444', paddingBottom: '10px' }}>Settings</h1>

            {/* General Settings */}
            <div style={{ marginBottom: '40px', backgroundColor: '#2a2a2a', padding: '20px', borderRadius: '8px' }}>
                <h3 style={{ marginTop: 0 }}>General Configuration</h3>

                <div style={{ marginBottom: '15px' }}>
                    <label style={{ display: 'block', marginBottom: '8px', color: '#ccc' }}>Gemini API Key</label>
                    <div style={{ display: 'flex', gap: '10px' }}>
                        <input
                            type={showKey ? "text" : "password"}
                            value={apiKey}
                            onChange={(e) => setApiKey(e.target.value)}
                            placeholder="Update Gemini API Key..."
                            style={{ flex: 1, padding: '10px', backgroundColor: '#333', border: '1px solid #555', color: '#fff', borderRadius: '4px' }}
                        />
                        <button
                            onClick={() => setShowKey(!showKey)}
                            style={{ padding: '0 15px', backgroundColor: '#444', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                        >
                            {showKey ? "Hide" : "Show"}
                        </button>
                    </div>
                    {apiKey && (
                        <div style={{ marginTop: '5px', fontSize: '0.85em', color: '#888' }}>
                            Current Key: {showKey ? apiKey : maskKey(apiKey)}
                        </div>
                    )}
                </div>

                <div style={{ textAlign: 'right' }}>
                    <button
                        onClick={handleSaveGeneral}
                        disabled={apiKey === (config.gemini_api_key || "")}
                        style={{
                            padding: '8px 20px',
                            backgroundColor: apiKey === (config.gemini_api_key || "") ? '#555' : '#007bff',
                            color: apiKey === (config.gemini_api_key || "") ? '#888' : 'white',
                            border: 'none',
                            borderRadius: '4px',
                            cursor: apiKey === (config.gemini_api_key || "") ? 'not-allowed' : 'pointer'
                        }}
                    >
                        Update API Key
                    </button>
                </div>
            </div>

            {/* Watch Folders */}
            <div style={{ backgroundColor: '#2a2a2a', padding: '20px', borderRadius: '8px' }}>
                <h3 style={{ marginTop: 0 }}>Watch Folders</h3>
                <p style={{ color: '#aaa', fontSize: '0.9em', marginBottom: '20px' }}>
                    AudioFlow monitors these folders for new audio files (.mp3, .m4a).
                    When a file is detected, it checks if the filename matches any "Workflow Mode" triggers.
                </p>

                <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
                    <input
                        value={newPath}
                        onChange={(e) => setNewPath(e.target.value)}
                        placeholder="/Users/name/start/path"
                        style={{ flex: 1, padding: '10px', backgroundColor: '#333', border: '1px solid #555', color: '#fff', borderRadius: '4px' }}
                    />
                    <button onClick={handleAddFolder} style={{ padding: '10px 20px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}>
                        Add Folder
                    </button>
                </div>

                <ul style={{ listStyle: 'none', padding: 0 }}>
                    {folders.map((folder, idx) => (
                        <li key={idx} style={{ padding: '12px', borderBottom: '1px solid #444', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span style={{ fontFamily: 'monospace', color: '#eee' }}>{folder}</span>
                            <button onClick={() => handleRemoveFolder(folder)} style={{ color: '#ff6b6b', background: 'none', border: '1px solid #ff6b6b', padding: '4px 10px', borderRadius: '4px', cursor: 'pointer' }}>
                                Remove
                            </button>
                        </li>
                    ))}
                    {folders.length === 0 && (
                        <li style={{ padding: '20px', textAlign: 'center', color: '#666', fontStyle: 'italic' }}>
                            No folders watched. Add one above.
                        </li>
                    )}
                </ul>
            </div>
        </div>
    );
};

export default Settings;
