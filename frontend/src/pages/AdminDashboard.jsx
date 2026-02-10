
import React from 'react';

const AdminDashboard = () => {
    return (
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
            <h1 style={{ marginBottom: '2rem' }}>Administration Console</h1>

            {/* Stats Row */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1.5rem', marginBottom: '2rem' }}>
                {[
                    { label: 'Total Students', val: '1,240', color: '#2563eb' },
                    { label: 'Total Faculty', val: '86', color: '#7c3aed' },
                    { label: 'Active Courses', val: '42', color: '#059669' },
                    { label: 'System Alerts', val: '5', color: '#dc2626' }
                ].map((stat, i) => (
                    <div key={i} className="card" style={{ textAlign: 'center', padding: '1.5rem 1rem', marginBottom: 0 }}>
                        <p className="text-muted text-sm font-bold uppercase" style={{ marginBottom: '0.5rem' }}>{stat.label}</p>
                        <p style={{ fontSize: '2.5rem', fontWeight: 'bold', color: stat.color, margin: 0 }}>{stat.val}</p>
                    </div>
                ))}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '2rem' }}>
                <div className="card">
                    <h2>User Management</h2>
                    <p className="text-muted" style={{ marginBottom: '1.5rem' }}>Search, edit, or create new users in the system.</p>

                    <div className="flex gap-2" style={{ marginBottom: '1.5rem' }}>
                        <button>+ Add Student</button>
                        <button style={{ background: 'var(--accent)' }}>+ Add Faculty</button>
                        <button style={{ background: 'white', color: 'var(--text-main)', border: '1px solid var(--border)' }}>Import CSV</button>
                    </div>

                    <div style={{ border: '1px solid var(--border)', borderRadius: '4px' }}>
                        <div style={{ padding: '0.75rem', background: '#f8fafc', borderBottom: '1px solid var(--border)', fontWeight: '600', fontSize: '0.875rem' }}>Recent Registrations</div>
                        {['Alice Walker (Student)', 'Bob Martin (Lecturer)', 'Charlie Day (Student)'].map((u, i) => (
                            <div key={i} style={{ padding: '0.75rem', borderBottom: i < 2 ? '1px solid var(--border)' : 'none', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span>{u}</span>
                                <span className="text-sm text-muted">Just now</span>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="card">
                    <h2>System Health</h2>
                    <div style={{ marginTop: '1rem' }}>
                        <div className="flex justify-between" style={{ marginBottom: '0.5rem' }}>
                            <span>CPU Usage</span>
                            <span className="text-muted">12%</span>
                        </div>
                        <div style={{ width: '100%', height: '6px', background: '#e2e8f0', borderRadius: '3px', marginBottom: '1.5rem' }}>
                            <div style={{ width: '12%', height: '100%', background: '#22c55e', borderRadius: '3px' }}></div>
                        </div>

                        <div className="flex justify-between" style={{ marginBottom: '0.5rem' }}>
                            <span>Memory Usage</span>
                            <span className="text-muted">48%</span>
                        </div>
                        <div style={{ width: '100%', height: '6px', background: '#e2e8f0', borderRadius: '3px', marginBottom: '1.5rem' }}>
                            <div style={{ width: '48%', height: '100%', background: '#f59e0b', borderRadius: '3px' }}></div>
                        </div>

                        <div className="flex justify-between" style={{ marginBottom: '0.5rem' }}>
                            <span>Storage</span>
                            <span className="text-muted">75%</span>
                        </div>
                        <div style={{ width: '100%', height: '6px', background: '#e2e8f0', borderRadius: '3px' }}>
                            <div style={{ width: '75%', height: '100%', background: '#3b82f6', borderRadius: '3px' }}></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AdminDashboard;
