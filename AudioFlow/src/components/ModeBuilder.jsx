import React, { useState, useEffect } from 'react';

const ModeBuilder = ({ config, onSaveConfig }) => {
    // Current selection state
    const [selectedModeId, setSelectedModeId] = useState(null);
    const [selectedActionDefId, setSelectedActionDefId] = useState(null);

    // Local config state
    const [localConfig, setLocalConfig] = useState(config || { modes: [], action_definitions: {} });

    useEffect(() => {
        if (config) setLocalConfig(config);
    }, [config]);

    const handleSave = () => {
        onSaveConfig(localConfig);
    };

    // --- Data Helpers ---
    const getMode = (id) => (localConfig.modes || []).find(m => m.id === id);
    const getActionDef = (id) => (localConfig.action_definitions || {})[id];
    const getActionDefList = () => Object.values(localConfig.action_definitions || {});

    // --- Handlers: Modes ---
    const addMode = () => {
        const newMode = {
            id: `mode_${Date.now()}`,
            name: "New Mode",
            trigger_keywords: [],
            steps: []
        };
        setLocalConfig(prev => ({ ...prev, modes: [...(prev.modes || []), newMode] }));
        setSelectedModeId(newMode.id);
        setSelectedActionDefId(null);
    };

    const updateMode = (id, updates) => {
        setLocalConfig(prev => ({
            ...prev,
            modes: (prev.modes || []).map(m => m.id === id ? { ...m, ...updates } : m)
        }));
    };

    const addStepToMode = (modeId, actionDefId) => {
        const mode = getMode(modeId);
        if (!mode) return; // Safety check
        const newStep = {
            id: `step_${Date.now()}`,
            action_def_id: actionDefId || "", // Allow empty for manual selection
            dependency: null
        };
        updateMode(modeId, { steps: [...(mode.steps || []), newStep] });
    };

    const removeStep = (modeId, stepId) => {
        const mode = getMode(modeId);
        if (!mode) return;
        updateMode(modeId, { steps: (mode.steps || []).filter(s => s.id !== stepId) });
    };

    const updateStep = (modeId, stepId, updates) => {
        const mode = getMode(modeId);
        if (!mode) return;
        const newSteps = (mode.steps || []).map(s => s.id === stepId ? { ...s, ...updates } : s);
        updateMode(modeId, { steps: newSteps });
    };

    // ... (Left Panel Logic)

    // --- Handlers: Action Library ---
    const addActionDef = () => {
        const id = `act_def_${Date.now()}`;
        const newDef = {
            id,
            name: "New Action",
            type: "text_generation", // Default
            model: "gemini-1.5-flash",
            prompt: ""
        };
        setLocalConfig(prev => ({
            ...prev,
            action_definitions: { ...(prev.action_definitions || {}), [id]: newDef }
        }));
        setSelectedActionDefId(id);
        setSelectedModeId(null);
    };

    const updateActionDef = (id, updates) => {
        setLocalConfig(prev => ({
            ...prev,
            action_definitions: {
                ...(prev.action_definitions || {}),
                [id]: { ...(prev.action_definitions || {})[id], ...updates }
            }
        }));
    };

    // --- Render ---

    const selectedMode = selectedModeId ? getMode(selectedModeId) : null;
    const selectedDef = selectedActionDefId ? getActionDef(selectedActionDefId) : null;

    // Simple deep comparison for dirty state
    const hasChanges = JSON.stringify(localConfig) !== JSON.stringify(config);

    const SaveButton = () => (
        <div style={{ marginTop: '20px', borderTop: '1px solid #444', paddingTop: '20px' }}>
            <button
                onClick={handleSave}
                disabled={!hasChanges}
                title={!hasChanges ? "no changes were made" : ""}
                style={{
                    padding: '10px 20px',
                    backgroundColor: hasChanges ? '#007bff' : '#444',
                    color: hasChanges ? 'white' : '#888',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: hasChanges ? 'pointer' : 'not-allowed'
                }}
            >
                Save Changes
            </button>
        </div>
    );

    return (
        <div style={{ display: 'flex', height: '100%' }}>
            {/* LEFT PANEL: Multi-Section */}
            <div style={{ width: '320px', borderRight: '1px solid #444', display: 'flex', flexDirection: 'column', backgroundColor: '#2a2a2a' }}>

                {/* Section 1: Modes */}
                <div style={{ flex: 1, overflowY: 'auto', borderBottom: '1px solid #444' }}>
                    <div style={{ padding: '10px', fontWeight: 'bold', backgroundColor: '#333', display: 'flex', justifyContent: 'space-between' }}>
                        <span>Workflow Modes</span>
                        <button onClick={addMode} style={{ fontSize: '0.8em', padding: '2px 8px' }}>+ New</button>
                    </div>
                    <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                        {(localConfig.modes || []).map(mode => (
                            <li
                                key={mode.id}
                                onClick={() => { setSelectedModeId(mode.id); setSelectedActionDefId(null); }}
                                style={{
                                    padding: '10px',
                                    cursor: 'pointer',
                                    borderLeft: selectedModeId === mode.id ? '4px solid #007bff' : '4px solid transparent',
                                    backgroundColor: selectedModeId === mode.id ? '#3a3a3a' : 'transparent',
                                }}
                            >
                                {mode.name} <span style={{ fontSize: '0.8em', color: '#888' }}>({(mode.steps || []).length} steps)</span>
                            </li>
                        ))}
                    </ul>
                </div>

                {/* Section 2: Action Library */}
                <div style={{ flex: 1, overflowY: 'auto' }}>
                    <div style={{ padding: '10px', fontWeight: 'bold', backgroundColor: '#333', display: 'flex', justifyContent: 'space-between' }}>
                        <span>Action Library</span>
                        <button onClick={addActionDef} style={{ fontSize: '0.8em', padding: '2px 8px' }}>+ New</button>
                    </div>
                    <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                        {getActionDefList().map(def => (
                            <li
                                key={def.id}
                                onClick={() => { setSelectedActionDefId(def.id); setSelectedModeId(null); }}
                                style={{
                                    padding: '10px',
                                    cursor: 'pointer',
                                    borderLeft: selectedActionDefId === def.id ? '4px solid #28a745' : '4px solid transparent',
                                    backgroundColor: selectedActionDefId === def.id ? '#3a3a3a' : 'transparent'
                                }}
                            >
                                {def.name} <span style={{ fontSize: '0.8em', color: '#888' }}>({def.type})</span>
                            </li>
                        ))}
                    </ul>
                </div>

                {/* Save Button Removed from side panel */}
            </div>

            {/* RIGHT PANEL: Editor */}
            <div style={{ flex: 1, padding: '20px', overflowY: 'auto', backgroundColor: '#1e1e1e' }}>

                {selectedMode && (
                    <div>
                        <h2 style={{ borderBottom: '1px solid #444', paddingBottom: '10px' }}>Edit Mode: {selectedMode.name}</h2>

                        <div style={{ marginBottom: '20px' }}>
                            <label style={{ display: 'block', color: '#aaa', marginBottom: '5px' }}>Mode Name</label>
                            <input
                                value={selectedMode.name}
                                dir="auto"
                                onChange={(e) => updateMode(selectedMode.id, { name: e.target.value })}
                                style={{ width: '100%', padding: '8px', backgroundColor: '#333', color: 'white', border: '1px solid #555' }}
                            />
                        </div>

                        <div style={{ marginBottom: '20px' }}>
                            <label style={{ display: 'block', color: '#aaa', marginBottom: '5px' }}>Trigger Keywords (comma separated)</label>
                            <input
                                value={selectedMode.trigger_keywords.join(', ')}
                                dir="auto"
                                onChange={(e) => updateMode(selectedMode.id, { trigger_keywords: e.target.value.split(',').map(s => s.trim()) })}
                                style={{ width: '100%', padding: '8px', backgroundColor: '#333', color: 'white', border: '1px solid #555' }}
                            />
                        </div>

                        <h3>Workflow Steps</h3>

                        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '15px' }}>
                            {(selectedMode.steps || []).map((step, idx) => {
                                const availableDeps = (selectedMode.steps || []).slice(0, idx); // Can only depend on previous steps

                                return (
                                    <div key={step.id} style={{ padding: '15px', backgroundColor: '#2a2a2a', border: '1px solid #444', borderRadius: '4px' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px', alignItems: 'center' }}>
                                            <div style={{ flex: 1, marginRight: '10px' }}>
                                                <label style={{ display: 'block', color: '#aaa', fontSize: '0.8em', marginBottom: '2px' }}>Action Type</label>
                                                <select
                                                    value={step.action_def_id}
                                                    onChange={(e) => updateStep(selectedMode.id, step.id, { action_def_id: e.target.value })}
                                                    style={{ width: '100%', padding: '6px', backgroundColor: '#333', color: 'white', border: '1px solid #555' }}
                                                >
                                                    <option value="">-- Select Action --</option>
                                                    {getActionDefList().map(def => (
                                                        <option key={def.id} value={def.id}>{def.name}</option>
                                                    ))}
                                                </select>
                                            </div>
                                            <button onClick={() => removeStep(selectedMode.id, step.id)} style={{ color: '#dc3545', background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.2em' }}>&times;</button>
                                        </div>

                                        {/* Dependency Selector */}
                                        {idx > 0 && (
                                            <div style={{ fontSize: '0.9em' }}>
                                                <label style={{ color: '#aaa' }}>Input from:</label>
                                                <select
                                                    value={step.dependency || ""}
                                                    onChange={(e) => updateStep(selectedMode.id, step.id, { dependency: e.target.value || null })}
                                                    style={{ marginLeft: '10px', padding: '4px', backgroundColor: '#333', color: 'white', border: '1px solid #555' }}
                                                >
                                                    <option value="">(None - Independent)</option>
                                                    {availableDeps.map((prevStep, prevIdx) => {
                                                        const prevDef = getActionDef(prevStep.action_def_id);
                                                        return <option key={prevStep.id} value={prevStep.id}>{prevIdx + 1}. {prevDef ? prevDef.name : '(Unnamed Action)'}</option>;
                                                    })}
                                                </select>
                                            </div>
                                        )}
                                        {idx === 0 && <span style={{ color: '#666', fontSize: '0.8em' }}>First step always runs on source</span>}
                                    </div>
                                );
                            })}
                            {(selectedMode.steps || []).length === 0 && <div style={{ color: '#666', fontStyle: 'italic' }}>No steps defined yet.</div>}
                        </div>

                        <div style={{ marginBottom: '30px' }}>
                            <button
                                onClick={() => addStepToMode(selectedMode.id, "")}
                                style={{ padding: '8px 16px', backgroundColor: '#333', color: 'white', border: '1px dashed #555', borderRadius: '4px', width: '100%', cursor: 'pointer' }}
                            >
                                + Add Step
                            </button>
                        </div>

                        <SaveButton />
                    </div>
                )}

                {selectedDef && (
                    <div>
                        <h2 style={{ borderBottom: '1px solid #444', paddingBottom: '10px', color: '#28a745' }}>Edit Action: {selectedDef.name}</h2>

                        <div style={{ marginBottom: '20px' }}>
                            <label style={{ display: 'block', color: '#aaa', marginBottom: '5px' }}>Action Name</label>
                            <input
                                value={selectedDef.name}
                                dir="auto"
                                onChange={(e) => updateActionDef(selectedDef.id, { name: e.target.value })}
                                style={{ width: '100%', padding: '8px', backgroundColor: '#333', color: 'white', border: '1px solid #555' }}
                            />
                        </div>

                        <div style={{ marginBottom: '20px' }}>
                            <label style={{ display: 'block', color: '#aaa', marginBottom: '5px' }}>Action Type</label>
                            <select
                                value={selectedDef.type === "transcription" ? "transcription" : "text_generation"}
                                onChange={(e) => updateActionDef(selectedDef.id, { type: e.target.value })}
                                style={{ width: '100%', padding: '8px', backgroundColor: '#333', color: 'white', border: '1px solid #555' }}
                            >
                                <option value="transcription">Audio Transcription (Audio &rarr; Text)</option>
                                <option value="text_generation">Text Processing (Text &rarr; Text)</option>
                            </select>
                            <div style={{ fontSize: '0.8em', color: '#666', marginTop: '5px' }}>
                                Use "Text Processing" for Summaries, Social Posts, Feedback, etc.
                            </div>
                        </div>

                        <div style={{ marginBottom: '20px' }}>
                            <label style={{ display: 'block', color: '#aaa', marginBottom: '5px' }}>Model</label>
                            <select
                                value={selectedDef.model || "gemini-1.5-flash"}
                                onChange={(e) => updateActionDef(selectedDef.id, { model: e.target.value })}
                                style={{ width: '100%', padding: '8px', backgroundColor: '#333', color: 'white', border: '1px solid #555' }}
                            >
                                <option value="gemini-3-pro">Gemini 3 Pro</option>
                                <option value="gemini-3-flash">Gemini 3 Flash</option>
                            </select>
                        </div>

                        <div style={{ marginBottom: '20px' }}>
                            <label style={{ display: 'block', color: '#aaa', marginBottom: '5px' }}>Prompt / System Instruction</label>
                            <textarea
                                value={selectedDef.prompt}
                                dir="auto"
                                onChange={(e) => updateActionDef(selectedDef.id, { prompt: e.target.value })}
                                style={{ width: '100%', height: '300px', padding: '10px', backgroundColor: '#333', color: '#fff', fontFamily: 'monospace', border: '1px solid #555' }}
                            />
                        </div>

                        <SaveButton />
                    </div>
                )}

                {!selectedMode && !selectedDef && (
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#666' }}>
                        Select a Mode or Action from the library to edit.
                    </div>
                )}
            </div>
        </div>
    );
};

export default ModeBuilder;
