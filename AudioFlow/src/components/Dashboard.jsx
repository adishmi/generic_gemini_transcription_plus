import React, { useState, useMemo } from 'react';

const Dashboard = ({ jobs, engineStatus, onToggleEngine }) => {
    const [showHistory, setShowHistory] = useState(false);

    // Process and sort jobs
    const { activeJobs, doneTodayJobs, historyJobs } = useMemo(() => {
        const active = [];
        const doneToday = [];
        const history = [];

        const today = new Date();
        today.setHours(0, 0, 0, 0);

        Object.entries(jobs || {}).forEach(([jobId, job]) => {
            const date = parseJobDate(jobId);
            const isJobToday = date >= today;

            if (job.status === 'completed') {
                if (isJobToday) {
                    doneToday.push({ id: jobId, date, ...job });
                } else {
                    history.push({ id: jobId, date, ...job });
                }
            } else {
                // All non-completed jobs are active (processing, error, etc.)
                active.push({ id: jobId, date, ...job });
            }
        });

        // Sort Active: By Date (Assuming User wants FIFO or Newest? "Currently processed (by date)" usually means FIFO for queue.
        // But for visibility, let's put Newest at top. Wait, user said "Currently processed... In Queue".
        // If we assume Newest = ID is larger.
        active.sort((a, b) => b.date - a.date); // Newest First

        // Sort Done Today: By Time (Newest First)
        doneToday.sort((a, b) => b.date - a.date);

        // Sort History: Newest First
        history.sort((a, b) => b.date - a.date);

        return { activeJobs: active, doneTodayJobs: doneToday, historyJobs: history };
    }, [jobs]);

    return (
        <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
                <h2 style={{ margin: 0 }}>AudioFlow</h2>
                <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <div style={{
                            width: '12px', height: '12px', borderRadius: '50%',
                            backgroundColor: engineStatus === 'running' ? '#4caf50' : '#f44336',
                            boxShadow: `0 0 8px ${engineStatus === 'running' ? '#4caf50' : '#f44336'}`
                        }} />
                        <span style={{ fontSize: '14px', fontWeight: 500 }}>
                            {engineStatus === 'running' ? 'Running' : 'Stopped'}
                        </span>
                    </div>
                    <button
                        onClick={onToggleEngine}
                        style={{
                            padding: '8px 16px',
                            backgroundColor: engineStatus === 'running' ? '#333' : '#4caf50',
                            color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer',
                            fontSize: '14px'
                        }}
                    >
                        {engineStatus === 'running' ? 'Stop Engine' : 'Start Engine'}
                    </button>
                </div>
            </div>

            {/* Active Jobs Section */}
            <Section title="Active Jobs" count={activeJobs.length}>
                {activeJobs.length === 0 ? (
                    <EmptyState message="No active jobs running." />
                ) : (
                    activeJobs.map(job => <JobCard key={job.id} job={job} type="active" />)
                )}
            </Section>

            {/* Done Today Section */}
            {doneTodayJobs.length > 0 && (
                <Section title="Done Today" count={doneTodayJobs.length}>
                    {doneTodayJobs.map(job => <JobCard key={job.id} job={job} type="done" />)}
                </Section>
            )}

            {/* History Section (Toggle) */}
            {historyJobs.length > 0 && (
                <div style={{ marginTop: '30px', borderTop: '1px solid #444', paddingTop: '20px' }}>
                    <div
                        onClick={() => setShowHistory(!showHistory)}
                        style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', userSelect: 'none', color: '#aaa' }}
                    >
                        <span style={{ marginRight: '10px' }}>{showHistory ? '▼' : '▶'}</span>
                        <h3 style={{ margin: 0, fontSize: '1.2em' }}>History ({historyJobs.length})</h3>
                    </div>

                    {showHistory && (
                        <div style={{ marginTop: '15px' }}>
                            {historyJobs.map(job => <JobCard key={job.id} job={job} type="history" />)}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

// --- Subcomponents & Helpers ---

const Section = ({ title, count, children }) => (
    <div style={{ marginBottom: '30px' }}>
        <h3 style={{ borderBottom: '1px solid #444', paddingBottom: '10px', marginBottom: '15px', color: '#eee' }}>
            {title} <span style={{ fontSize: '0.8em', color: '#888', marginLeft: '10px' }}>({count})</span>
        </h3>
        <div>{children}</div>
    </div>
);

const EmptyState = ({ message }) => (
    <div style={{ padding: '20px', textAlign: 'center', color: '#666', border: '1px dashed #444', borderRadius: '8px' }}>
        {message}
    </div>
);

const JobCard = ({ job, type }) => {
    const filename = job.filepath.split('/').pop();
    const statusInfo = getStatusInfo(job);

    return (
        <div style={{
            backgroundColor: '#333',
            borderRadius: '8px',
            padding: '15px',
            marginBottom: '10px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            opacity: type === 'history' ? 0.7 : 1
        }}>
            <div>
                <div style={{ fontWeight: '500', fontSize: '1.1em', marginBottom: '4px', color: '#fff' }}>
                    {filename}
                </div>
                <div style={{ fontSize: '0.85em', color: '#aaa' }}>
                    {job.date.toLocaleDateString()} {job.date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    <span style={{ margin: '0 8px' }}>•</span>
                    {job.mode_id.replace('mode_', '').toUpperCase()}
                </div>
            </div>

            <div style={{ textAlign: 'right' }}>
                <div style={{
                    display: 'inline-block',
                    padding: '4px 12px',
                    borderRadius: '12px',
                    backgroundColor: statusInfo.bg,
                    color: statusInfo.color,
                    fontSize: '0.9em',
                    fontWeight: 'bold'
                }}>
                    {statusInfo.text}
                </div>
                {type === 'active' && job.pending_steps.length > 0 && (
                    <div style={{ fontSize: '0.8em', color: '#888', marginTop: '4px' }}>
                        Next: {job.pending_steps[0].split('_')[1] || 'Process'}
                    </div>
                )}
            </div>
        </div>
    );
};

// Logic Helpers

const parseJobDate = (jobId) => {
    // Format: job_<timestamp>_<name>
    try {
        const parts = jobId.split('_');
        if (parts.length > 1) {
            const ts = parseInt(parts[1], 10);
            return new Date(ts * 1000);
        }
    } catch (e) {
        console.error("Date parse error", e);
    }
    return new Date();
};

const getStatusInfo = (job) => {
    if (job.status === 'error') {
        return { text: 'Error', color: '#fff', bg: '#d32f2f' };
    }
    if (job.status === 'completed') {
        return { text: 'Done', color: '#fff', bg: '#43a047' };
    }

    // Processing / Active Logic
    const totalCompleted = job.completed_steps ? job.completed_steps.length : 0;
    // We assume there's always at least one step if it's active.
    // Step count is 1-based index (Completed + 1)
    const currentStep = totalCompleted + 1;

    return { text: `Step ${currentStep}`, color: '#fff', bg: '#1976d2' };
};

export default Dashboard;
