
import React from 'react';

const MentorDashboard = () => {
    return (
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
            <h1 style={{ marginBottom: '0.5rem', fontSize: '2rem' }}>Mentor Dashboard</h1>
            <p className="text-muted" style={{ marginBottom: '2rem' }}>Monitor and guide your assigned students.</p>

            <div className="card" style={{ overflow: 'hidden', padding: 0 }}>
                <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h2 style={{ margin: 0, border: 'none', padding: 0 }}>Mentee List</h2>
                    <input type="text" placeholder="Search student..." style={{ width: '250px' }} />
                </div>

                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                    <thead style={{ background: '#f8fafc' }}>
                        <tr style={{ textAlign: 'left' }}>
                            <th style={{ padding: '1rem', fontWeight: '600', color: 'var(--text-muted)', fontSize: '0.875rem' }}>Name</th>
                            <th style={{ padding: '1rem', fontWeight: '600', color: 'var(--text-muted)', fontSize: '0.875rem' }}>ID</th>
                            <th style={{ padding: '1rem', fontWeight: '600', color: 'var(--text-muted)', fontSize: '0.875rem' }}>Dept</th>
                            <th style={{ padding: '1rem', fontWeight: '600', color: 'var(--text-muted)', fontSize: '0.875rem' }}>Attendance</th>
                            <th style={{ padding: '1rem', fontWeight: '600', color: 'var(--text-muted)', fontSize: '0.875rem' }}>Status</th>
                            <th style={{ padding: '1rem', fontWeight: '600', color: 'var(--text-muted)', fontSize: '0.875rem' }}>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {[
                            { name: 'John Doe', id: 'S1023', dept: 'CS', att: '92%', status: 'Good' },
                            { name: 'Jane Smith', id: 'S1024', dept: 'IT', att: '76%', status: 'Low Attendance' },
                            { name: 'Robert Johnson', id: 'S1025', dept: 'CS', att: '45%', status: 'Critical' },
                            { name: 'Emily Davis', id: 'S1026', dept: 'IT', att: '88%', status: 'Good' },
                        ].map((student, i) => (
                            <tr key={i} style={{ borderBottom: '1px solid var(--border)' }}>
                                <td style={{ padding: '1rem' }}>
                                    <div style={{ fontWeight: '500' }}>{student.name}</div>
                                    <div className="text-sm text-muted">Year 3</div>
                                </td>
                                <td style={{ padding: '1rem', color: 'var(--text-muted)' }}>{student.id}</td>
                                <td style={{ padding: '1rem' }}>{student.dept}</td>
                                <td style={{ padding: '1rem', fontWeight: '500' }}>{student.att}</td>
                                <td style={{ padding: '1rem' }}>
                                    <span style={{
                                        padding: '0.25rem 0.75rem',
                                        borderRadius: '999px',
                                        fontSize: '0.75rem',
                                        fontWeight: '600',
                                        background: student.status === 'Good' ? '#dcfce7' : student.status === 'Low Attendance' ? '#fef9c3' : '#fee2e2',
                                        color: student.status === 'Good' ? '#166534' : student.status === 'Low Attendance' ? '#854d0e' : '#991b1b'
                                    }}>
                                        {student.status}
                                    </span>
                                </td>
                                <td style={{ padding: '1rem' }}>
                                    <button style={{ fontSize: '0.8rem', padding: '0.35rem 0.75rem' }}>Details</button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                <div style={{ padding: '1rem', textAlign: 'center', background: '#f8fafc', color: 'var(--text-muted)', fontSize: '0.875rem' }}>
                    Showing 4 of 12 assignments
                </div>
            </div>
        </div>
    );
};

export default MentorDashboard;
