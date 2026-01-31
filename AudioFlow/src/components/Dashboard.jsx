import React from 'react';

const Dashboard = ({ jobs, engineStatus, onToggleEngine }) => {
    return (
        <div style={{ padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
                <h2>AudioFlow Dashboard</h2>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{
                        width: '10px', height: '10px', borderRadius: '50%',
                        backgroundColor: engineStatus === 'running' ? '#28a745' : '#dc3545'
                    }} />
                    <span>{engineStatus === 'running' ? 'Engine Running' : 'Engine Stopped'}</span>
                    <button onClick={onToggleEngine}>
                        {engineStatus === 'running' ? 'Stop' : 'Start'}
                    </button>
                </div>
            </div>

            <div style={{ border: '1px solid #ccc', borderRadius: '5px', padding: '10px' }}>
                <h3>Active Jobs</h3>
                {Object.keys(jobs).length === 0 ? (
                    <p style={{ color: '#888' }}>No active jobs. Drop files in watched folders.</p>
                ) : (
                    <ul style={{ listStyle: 'none', padding: 0 }}>
                        {Object.entries(jobs).map(([jobId, job]) => (
                            <li key={jobId} style={{ borderBottom: '1px solid #eee', padding: '10px 0' }}>
                                <div style={{ fontWeight: 'bold' }}>{job.filepath.split('/').pop()}</div>
                                <div style={{ fontSize: '0.9em', color: '#555' }}>
                                    Status: <span style={{ color: getStatusColor(job.status) }}>{job.status}</span>
                                </div>
                                <div style={{ fontSize: '0.8em', marginTop: '5px' }}>
                                    Completed: {job.completed_steps.join(', ')}
                                    {job.completed_steps.length > 0 && job.pending_steps.length > 0 && <span> &rarr; </span>}
                                    {job.pending_steps.length > 0 ? (
                                        <span style={{ color: '#007bff' }}>Current: {job.pending_steps[0]}</span>
                                    ) : (
                                        <span style={{ color: 'green' }}>Done</span>
                                    )}
                                </div>
                                {job.error && <div style={{ color: 'red', fontSize: '0.8em' }}>Error: {job.error}</div>}
                            </li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );
};

const getStatusColor = (status) => {
    switch (status) {
        case 'processing': return '#007bff';
        case 'completed': return '#28a745';
        case 'error': return '#dc3545';
        default: return '#666';
    }
};

export default Dashboard;
