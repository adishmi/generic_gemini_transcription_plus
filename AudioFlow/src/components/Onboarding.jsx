import React, { useState, useEffect } from 'react';

const Onboarding = ({ onComplete }) => {
    const [step, setStep] = useState(1);
    const [apiKey, setApiKey] = useState('');
    const [pythonPath, setPythonPath] = useState('python3');
    const [checks, setChecks] = useState({ python: 'pending' });

    useEffect(() => {
        if (step === 2) {
            checkDependencies();
        }
    }, [step]);

    const checkDependencies = async () => {
        setChecks(c => ({ ...c, python: 'checking' }));
        const hasPython = await window.electronAPI.checkPython(pythonPath);
        setChecks(c => ({ ...c, python: hasPython ? 'success' : 'failed' }));
    };

    const handleNext = () => {
        if (step === 1 && apiKey) setStep(2);
        else if (step === 2 && checks.python === 'success') {
            saveSettings();
            onComplete();
        }
    };

    const saveSettings = async () => {
        // Save API key to .env logic or config? 
        // PRD says .env. Node fs write needed.
        // For now, let's just assume we write to a config or .env via fsAPI
        const paths = await window.electronAPI.getAppPaths();
        const envPath = paths.userData + '/.env';
        try {
            // Write standard .env format
            await window.fsAPI.writeFile(envPath, `GOOGLE_API_KEY="${apiKey}"\n`);
        } catch (e) {
            console.error(e);
        }
    };

    return (
        <div style={{ padding: '40px', maxWidth: '600px', margin: '0 auto', fontFamily: 'sans-serif' }}>
            <h1>Welcome to AudioFlow</h1>

            {step === 1 && (
                <div>
                    <h3>Step 1: Gemini API Key</h3>
                    <p>Enter your Google Gemini API Key.</p>
                    <input
                        type="password"
                        value={apiKey}
                        onChange={(e) => setApiKey(e.target.value)}
                        placeholder="AIzaSy..."
                        style={{ width: '100%', padding: '10px', marginTop: '10px' }}
                    />
                    <button
                        onClick={handleNext}
                        disabled={!apiKey}
                        style={{ marginTop: '20px', padding: '10px 20px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '5px' }}
                    >
                        Next
                    </button>
                </div>
            )}

            {step === 2 && (
                <div>
                    <h3>Step 2: Environment Check</h3>
                    <div style={{ marginBottom: '20px' }}>
                        <p>Python 3.10+:
                            <span style={{
                                marginLeft: '10px',
                                fontWeight: 'bold',
                                color: checks.python === 'success' ? 'green' : checks.python === 'failed' ? 'red' : 'orange'
                            }}>
                                {checks.python.toUpperCase()}
                            </span>
                        </p>
                        {checks.python === 'failed' && (
                            <div>
                                <p style={{ color: 'red' }}>Python 3 not found. Please install Python 3.10+.</p>
                                <button onClick={checkDependencies}>Retry</button>
                            </div>
                        )}
                    </div>

                    <button
                        onClick={handleNext}
                        disabled={checks.python !== 'success'}
                        style={{ padding: '10px 20px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '5px' }}
                    >
                        Finish Setup
                    </button>
                </div>
            )}
        </div>
    );
};

export default Onboarding;
