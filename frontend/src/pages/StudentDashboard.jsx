
import React from 'react';
import { Link } from 'react-router-dom';

const StudentDashboard = () => {
    return (
        <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
            <div className="flex justify-between items-end" style={{ marginBottom: '2rem' }}>
                <div>
                    <h1 style={{ marginBottom: '0.5rem', fontSize: '2rem' }}>Welcome, Student</h1>
                    <p className="text-muted">Here's your academic overview for this semester.</p>
                </div>
                <Link to="/student/detail">
                    <button>View Full Profile</button>
                </Link>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
                <div className="card" style={{ borderLeft: '4px solid var(--primary)' }}>
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-muted text-sm font-bold uppercase">Attendance</p>
                            <p style={{ fontSize: '2.5rem', fontWeight: 'bold', margin: '0.5rem 0', color: 'var(--text-main)' }}>85%</p>
                        </div>
                        <span style={{ background: '#dbeafe', color: '#1e40af', padding: '0.25rem 0.75rem', borderRadius: '999px', fontSize: '0.875rem' }}>Good</span>
                    </div>
                    <div style={{ width: '100%', height: '8px', background: '#e2e8f0', borderRadius: '4px', marginTop: '1rem', overflow: 'hidden' }}>
                        <div style={{ width: '85%', height: '100%', background: 'var(--primary)', borderRadius: '4px' }}></div>
                    </div>
                    <p className="text-sm text-muted" style={{ marginTop: '0.5rem' }}>17/20 Classes Attended</p>
                </div>

                <div className="card" style={{ borderLeft: '4px solid var(--accent)' }}>
                    <div className="flex justify-between items-start">
                        <div>
                            <p className="text-muted text-sm font-bold uppercase">CGPA</p>
                            <p style={{ fontSize: '2.5rem', fontWeight: 'bold', margin: '0.5rem 0', color: 'var(--text-main)' }}>3.8</p>
                        </div>
                        <span style={{ background: '#fef3c7', color: '#92400e', padding: '0.25rem 0.75rem', borderRadius: '999px', fontSize: '0.875rem' }}>High</span>
                    </div>
                    <div style={{ width: '100%', height: '8px', background: '#e2e8f0', borderRadius: '4px', marginTop: '1rem', overflow: 'hidden' }}>
                        <div style={{ width: '90%', height: '100%', background: 'var(--accent)', borderRadius: '4px' }}></div>
                    </div>
                    <p className="text-sm text-muted" style={{ marginTop: '0.5rem' }}>Top 5% of class</p>
                </div>
            </div>

            <div className="card">
                <div className="flex justify-between items-center" style={{ marginBottom: '1.5rem', borderBottom: '1px solid var(--border)', paddingBottom: '1rem' }}>
                    <h2 style={{ fontSize: '1.25rem', borderBottom: 'none', margin: 0, padding: 0 }}>Recent Alerts & Notifications</h2>
                    <span style={{ background: '#fee2e2', color: '#991b1b', padding: '0.25rem 0.75rem', borderRadius: '4px', fontSize: '0.75rem', fontWeight: 'bold' }}>2 New</span>
                </div>

                <div style={{ display: 'grid', gap: '1rem' }}>
                    <div className="flex items-start gap-2" style={{ padding: '1rem', background: '#f0f9ff', borderLeft: '4px solid #0ea5e9', borderRadius: '4px' }}>
                        <div style={{ flex: 1 }}>
                            <p style={{ fontWeight: '600', color: '#0369a1', marginBottom: '0.25rem' }}>Mid-Term Exam Schedule Released</p>
                            <p className="text-sm text-muted">The schedule for the upcoming mid-term examinations has been published. Check your calendar.</p>
                            <p style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.5rem' }}>2 hours ago</p>
                        </div>
                    </div>

                    <div className="flex items-start gap-2" style={{ padding: '1rem', background: '#fff7ed', borderLeft: '4px solid #f97316', borderRadius: '4px' }}>
                        <div style={{ flex: 1 }}>
                            <p style={{ fontWeight: '600', color: '#c2410c', marginBottom: '0.25rem' }}>Assignment Due Soon</p>
                            <p className="text-sm text-muted">"Data Structures Implementation" is due in 2 days. Submit before 11:59 PM.</p>
                            <p style={{ fontSize: '0.75rem', color: '#64748b', marginTop: '0.5rem' }}>Yesterday</p>
                        </div>
                    </div>
                </div>
            </div>

            <h2 style={{ fontSize: '1.25rem', marginTop: '2rem', marginBottom: '1rem' }}>Your Subjects</h2>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem' }}>
                {['Advanced Mathematics', 'Computer Networks', 'Database Systems', 'Software Engineering'].map((subject, i) => (
                    <div key={i} className="card" style={{ padding: '1rem', marginBottom: 0, border: '1px solid var(--border)', boxShadow: 'none', background: 'white' }}>
                        <div style={{ height: '40px', width: '40px', background: '#f1f5f9', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: '1rem', fontWeight: 'bold', color: 'var(--primary)' }}>
                            {subject.substring(0, 2)}
                        </div>
                        <p style={{ fontWeight: '600' }}>{subject}</p>
                        <p className="text-sm text-muted">Faculty: Dr. Smith</p>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default StudentDashboard;
