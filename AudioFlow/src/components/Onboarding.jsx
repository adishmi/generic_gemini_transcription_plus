import React, { useState, useEffect } from 'react';

const Onboarding = ({ onComplete }) => {
    const [step, setStep] = useState(1);
    const [apiKey, setApiKey] = useState('');
    const [folders, setFolders] = useState([]);
    const [newFolder, setNewFolder] = useState('');
    const [checks, setChecks] = useState({ python: 'pending' });

    // Step 4: Environment Check
    useEffect(() => {
        if (step === 4) {
            checkDependencies();
        }
    }, [step]);

    const checkDependencies = async () => {
        setChecks(c => ({ ...c, python: 'checking' }));
        const hasPython = await window.electronAPI.checkPython('python3');
        setChecks(c => ({ ...c, python: hasPython ? 'success' : 'failed' }));
    };

    const handleNext = () => {
        if (step === 1 && apiKey) setStep(2);
        else if (step === 2) setStep(3); // Concepts -> Watch Folders
        else if (step === 3) setStep(4); // Watch Folders -> Checks
        else if (step === 4 && checks.python === 'success') {
            onComplete({
                gemini_api_key: apiKey,
                watched_folders: folders.length > 0 ? folders : []
            });
        }
    };

    const addFolder = () => {
        if (newFolder && !folders.includes(newFolder)) {
            setFolders([...folders, newFolder]);
            setNewFolder("");
        }
    };

    const removeFolder = (f) => setFolders(folders.filter(x => x !== f));

    return (
        <div style={{ padding: '60px', maxWidth: '800px', margin: '0 auto', fontFamily: 'sans-serif', color: '#eee' }}>
            <h1 style={{ textAlign: 'center', marginBottom: '40px' }}>Welcome to AudioFlow</h1>

            {/* Progress */}
            <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', marginBottom: '40px' }}>
                {[1, 2, 3, 4].map(s => (
                    <div key={s} style={{
                        width: '12px', height: '12px', borderRadius: '50%',
                        backgroundColor: step >= s ? '#007bff' : '#444'
                    }} />
                ))}
            </div>

            {/* Step 1: API Key */}
            {step === 1 && (
                <div style={stepContainerStyle}>
                    <h2>1. Connect Intelligence</h2>
                    <p style={{ lineHeight: '1.6' }}>
                        AudioFlow uses Google's Gemini models to understand your audio. You'll need an API Key to get started.
                    </p>

                    <div style={{ backgroundColor: '#333', padding: '15px', borderRadius: '8px', marginBottom: '20px' }}>
                        <strong>How to get a key:</strong>
                        <ol style={{ paddingLeft: '20px', marginTop: '10px' }}>
                            <li style={{ marginBottom: '8px' }}>Go to <a href="#" onClick={() => window.open('https://aistudio.google.com/app/apikey')} style={{ color: '#4caf50' }}>Google AI Studio</a>.</li>
                            <li>Click "Create API key" and copy the string.</li>
                        </ol>
                    </div>

                    <input
                        type="password"
                        value={apiKey}
                        onChange={(e) => setApiKey(e.target.value)}
                        placeholder="Paste your API Key here (AIza...)"
                        style={inputStyle}
                    />

                    <div style={{ textAlign: 'right', marginTop: '20px' }}>
                        <button onClick={handleNext} disabled={!apiKey} style={buttonStyle}>
                            Continue &rarr;
                        </button>
                    </div>
                </div>
            )}

            {/* Step 2: Concepts */}
            {step === 2 && (
                <div style={stepContainerStyle}>
                    <h2>2. How It Works</h2>
                    <p>AudioFlow ignores busywork by using <strong>Modes</strong>.</p>

                    <div style={{ display: 'flex', gap: '20px', alignItems: 'stretch', margin: '30px 0' }}>
                        <div style={cardStyle}>
                            <div style={{ fontSize: '30px', marginBottom: '10px' }}>📁</div>
                            <h3>Input</h3>
                            <p style={{ fontSize: '0.9em', color: '#aaa' }}>
                                You drop a file into a watched folder.
                            </p>
                            <div style={{ backgroundColor: '#222', padding: '5px', borderRadius: '4px', marginTop: '10px', fontFamily: 'monospace', fontSize: '0.8em' }}>
                                "branding_workshop.mp3"
                            </div>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', fontSize: '24px', color: '#666' }}>&rarr;</div>

                        <div style={cardStyle}>
                            <div style={{ fontSize: '30px', marginBottom: '10px' }}>⚡</div>
                            <h3>Mode Trigger</h3>
                            <p style={{ fontSize: '0.9em', color: '#aaa' }}>
                                AudioFlow sees the word <strong>"workshop"</strong> and activates the <strong>Workshop Mode</strong>.
                            </p>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', fontSize: '24px', color: '#666' }}>&rarr;</div>

                        <div style={cardStyle}>
                            <div style={{ fontSize: '30px', marginBottom: '10px' }}>⚙️</div>
                            <h3>Actions</h3>
                            <p style={{ fontSize: '0.9em', color: '#aaa' }}>
                                It executes the steps defined in that mode:
                            </p>
                            <ul style={{ textAlign: 'left', fontSize: '0.85em', color: '#ccc', paddingLeft: '20px' }}>
                                <li>Step 1: Transcribe</li>
                                <li>Step 2: Summarize</li>
                            </ul>
                        </div>
                    </div>

                    <div style={{ textAlign: 'right', marginTop: '20px' }}>
                        <button onClick={handleNext} style={buttonStyle}>Got it &rarr;</button>
                    </div>
                </div>
            )}

            {/* Step 3: Watch Folders */}
            {step === 3 && (
                <div style={stepContainerStyle}>
                    <h2>3. Set Watch Points</h2>
                    <p>Tell AudioFlow where to look for files. These are the "Watch Folders".</p>
                    <p style={{ fontSize: '0.9em', color: '#aaa', marginBottom: '20px' }}>
                        Any audio file saved to these folders (or their subfolders) will be automatically detected.
                    </p>

                    <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
                        <input
                            value={newFolder}
                            onChange={(e) => setNewFolder(e.target.value)}
                            placeholder="/Users/me/Recordings"
                            style={inputStyle}
                        />
                        <button onClick={addFolder} style={{ ...buttonStyle, backgroundColor: '#28a745' }}>Add</button>
                    </div>

                    <ul style={{ listStyle: 'none', padding: 0, marginBottom: '20px', border: '1px solid #444', borderRadius: '4px', maxHeight: '150px', overflowY: 'auto' }}>
                        {folders.map((f, i) => (
                            <li key={i} style={{ padding: '10px', borderBottom: '1px solid #444', display: 'flex', justifyContent: 'space-between' }}>
                                <span style={{ fontFamily: 'monospace' }}>{f}</span>
                                <span onClick={() => removeFolder(f)} style={{ cursor: 'pointer', color: '#ff6b6b' }}>&times;</span>
                            </li>
                        ))}
                        {folders.length === 0 && <li style={{ padding: '15px', color: '#666', textAlign: 'center' }}>No folders added yet. You can add them later too.</li>}
                    </ul>

                    <div style={{ textAlign: 'right', marginTop: '20px' }}>
                        <button onClick={handleNext} style={buttonStyle}>
                            Next &rarr;
                        </button>
                    </div>
                </div>
            )}

            {/* Step 4: Checks */}
            {step === 4 && (
                <div style={stepContainerStyle}>
                    <h2>4. System Check</h2>
                    <p>Verifying local requirements...</p>

                    <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#333', borderRadius: '8px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span>Python Environment</span>
                            <span style={{
                                fontWeight: 'bold',
                                color: checks.python === 'success' ? '#4caf50' : checks.python === 'failed' ? '#f44336' : '#ff9800'
                            }}>
                                {checks.python.toUpperCase()}
                            </span>
                        </div>
                        {checks.python === 'failed' && (
                            <div style={{ marginTop: '10px', color: '#f44336', fontSize: '0.9em' }}>
                                Python 3 not found. Please install Python 3.10+ and restart.
                            </div>
                        )}
                    </div>

                    <div style={{ textAlign: 'right', marginTop: '20px' }}>
                        <button
                            onClick={handleNext}
                            disabled={checks.python !== 'success'}
                            style={{ ...buttonStyle, opacity: checks.python !== 'success' ? 0.5 : 1 }}
                        >
                            Finish Setup 🚀
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

// Styles
const stepContainerStyle = {
    backgroundColor: '#2a2a2a',
    padding: '30px',
    borderRadius: '12px',
    boxShadow: '0 4px 20px rgba(0,0,0,0.3)'
};

const inputStyle = {
    width: '100%',
    padding: '12px',
    backgroundColor: '#333',
    border: '1px solid #555',
    borderRadius: '6px',
    color: 'white',
    fontSize: '1em'
};

const buttonStyle = {
    padding: '12px 24px',
    backgroundColor: '#007bff',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '1em',
    fontWeight: '500'
};

const cardStyle = {
    flex: 1,
    backgroundColor: '#333',
    padding: '15px',
    borderRadius: '8px',
    textAlign: 'center',
    border: '1px solid #444'
};

export default Onboarding;
