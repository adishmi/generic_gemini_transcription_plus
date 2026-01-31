import React, { useState } from 'react';

const WatchSettings = ({ config, onSaveConfig }) => {
    const [folders, setFolders] = useState(config.watched_folders || []);
    const [newPath, setNewPath] = useState("");

    const handleAdd = () => {
        if (newPath && !folders.includes(newPath)) {
            const updated = [...folders, newPath];
            setFolders(updated);
            onSaveConfig({ ...config, watched_folders: updated });
            setNewPath("");
        }
    };

    const handleRemove = (path) => {
        const updated = folders.filter(f => f !== path);
        setFolders(updated);
        onSaveConfig({ ...config, watched_folders: updated });
    };

    return (
        <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
            <h2>Watch Points (Folders)</h2>
            <p>AudioFlow monitors these folders for new files.</p>

            <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
                <input
                    value={newPath}
                    onChange={(e) => setNewPath(e.target.value)}
                    placeholder="/Users/name/start/path"
                    style={{ flex: 1, padding: '8px' }}
                />
                <button onClick={handleAdd} style={{ padding: '8px 16px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '4px' }}>
                    Add Folder
                </button>
            </div>

            <ul style={{ listStyle: 'none', padding: 0 }}>
                {folders.map((folder, idx) => (
                    <li key={idx} style={{ padding: '10px', borderBottom: '1px solid #333', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontFamily: 'monospace' }}>{folder}</span>
                        <button onClick={() => handleRemove(folder)} style={{ color: 'red', background: 'none', border: '1px solid red', padding: '4px 8px', borderRadius: '4px' }}>
                            Remove
                        </button>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default WatchSettings;
