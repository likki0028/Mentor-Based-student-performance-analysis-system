
import React from 'react';

const LecturerDashboard = () => {
    return (
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
            <h1 style={{ marginBottom: '0.5rem', fontSize: '2rem' }}>Lecturer Dashboard</h1>
            <p className="text-muted" style={{ marginBottom: '2rem' }}>Manage your classes, assignments, and student grades.</p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 300px', gap: '2rem' }}>
                {/* Left Column: Classes */}
                <div>
                    <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>Active Classes</h2>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        {[
                            { name: 'Advanced Python', section: 'Section A', students: 45, time: 'Mon, Wed 10:00 AM' },
                            { name: 'Data Structures', section: 'Section B', students: 38, time: 'Tue, Thu 02:00 PM' },
                            { name: 'Machine Learning', section: 'Section A', students: 52, time: 'Fri 09:00 AM' }
                        ].map((cls, i) => (
                            <div key={i} className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 0, borderLeft: `4px solid ${i === 0 ? 'var(--primary)' : 'var(--secondary)'}` }}>
                                <div>
                                    <h3 style={{ margin: 0, fontSize: '1.2rem' }}>{cls.name}</h3>
                                    <p className="text-muted text-sm">{cls.section} • {cls.students} Students</p>
                                    <p className="text-sm" style={{ marginTop: '0.5rem', color: 'var(--text-main)', fontWeight: '500' }}>{cls.time}</p>
                                </div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                    <button style={{ fontSize: '0.875rem', padding: '0.4rem 0.8rem' }}>View Class</button>
                                    <button style={{ fontSize: '0.875rem', padding: '0.4rem 0.8rem', background: 'white', border: '1px solid var(--border)', color: 'var(--text-main)' }}>Attendance</button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Right Column: Quick Actions & Upcoming */}
                <div>
                    <div className="card">
                        <h2>Quick Actions</h2>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                            <button className="flex items-center gap-2" style={{ justifyContent: 'center' }}>
                                <span>+</span> Create Assignment
                            </button>
                            <button className="flex items-center gap-2" style={{ justifyContent: 'center', background: 'var(--accent)' }}>
                                <span>+</span> Schedule Quiz
                            </button>
                            <button className="flex items-center gap-2" style={{ justifyContent: 'center', background: 'var(--secondary)' }}>
                                <span>↑</span> Upload Marks
                            </button>
                        </div>
                    </div>

                    <div className="card">
                        <h2>Upcoming Deadlines</h2>
                        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                            <li style={{ padding: '0.75rem 0', borderBottom: '1px solid var(--border)' }}>
                                <p style={{ fontWeight: '600', fontSize: '0.9rem' }}>Assignment 3 Grading</p>
                                <p className="text-sm text-muted">Data Structures - Due Tomorrow</p>
                            </li>
                            <li style={{ padding: '0.75rem 0' }}>
                                <p style={{ fontWeight: '600', fontSize: '0.9rem' }}>Submit Mid-term Reports</p>
                                <p className="text-sm text-muted">All Sections - Due Friday</p>
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default LecturerDashboard;
