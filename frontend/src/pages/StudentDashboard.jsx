
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import Navbar from '../components/Navbar';
import toast, { Toaster } from 'react-hot-toast';

const StudentDashboard = () => {
    const { user } = useAuth();
    const [profile, setProfile] = useState(null);
    const [marks, setMarks] = useState([]);
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const profileRes = await api.get('/students/me');
                setProfile(profileRes.data);

                const [marksRes, alertsRes] = await Promise.all([
                    api.get(`/students/${profileRes.data.id}/marks`),
                    api.get('/alerts/').catch(() => ({ data: [] }))
                ]);
                setMarks(marksRes.data);
                setAlerts(alertsRes.data);
            } catch (err) {
                console.error('Failed to fetch student data:', err);
                setError(err.response?.data?.detail || 'Failed to load data');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    if (loading) {
        return (
            <>
                <Navbar />
                <div className="container page-enter">
                    <div className="grid grid-2" style={{ marginTop: '2rem' }}>
                        {[1, 2].map(i => <div key={i} className="skeleton skeleton-card"></div>)}
                    </div>
                    <div className="skeleton" style={{ height: 200, marginTop: '1.5rem' }}></div>
                </div>
            </>
        );
    }

    if (error) {
        return (
            <>
                <Navbar />
                <div className="container">
                    <div className="card" style={{ textAlign: 'center', borderLeft: '4px solid var(--danger)' }}>
                        <p style={{ color: 'var(--danger)', fontWeight: 600 }}>Error: {error}</p>
                    </div>
                </div>
            </>
        );
    }

    const attendancePct = profile?.attendance_percentage || 0;
    const attendanceLabel = attendancePct >= 85 ? 'Good' : attendancePct >= 70 ? 'Average' : 'Low';
    const attendanceBadge = attendancePct >= 85 ? 'badge-safe' : attendancePct >= 70 ? 'badge-warning' : 'badge-danger';

    const avgMarks = marks.length > 0 ? (marks.reduce((sum, m) => sum + (m.score / m.total) * 100, 0) / marks.length).toFixed(1) : 0;
    const marksBadge = avgMarks >= 80 ? 'badge-safe' : avgMarks >= 60 ? 'badge-warning' : 'badge-danger';

    // Group marks by subject
    const subjectMap = {};
    marks.forEach(m => {
        const name = m.subject_name || `Subject ${m.subject_id}`;
        if (!subjectMap[name]) subjectMap[name] = [];
        subjectMap[name].push(m);
    });

    const unreadAlerts = alerts.filter(a => !a.is_read);

    return (
        <>
            <Navbar />
            <Toaster position="top-right" />
            <div className="container page-enter">
                {/* Header */}
                <div className="flex justify-between items-end" style={{ marginBottom: '2rem' }}>
                    <div>
                        <h1 style={{ marginBottom: '0.25rem', fontSize: '2rem' }}>
                            Welcome, {user?.username || profile?.name || 'Student'} 👋
                        </h1>
                        <p className="text-muted">
                            Enrollment: <strong>{profile?.enrollment_number}</strong> &nbsp;•&nbsp; Semester {profile?.current_semester}
                        </p>
                    </div>
                    <Link to="/student/detail">
                        <button>View Full Profile →</button>
                    </Link>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-3" style={{ marginBottom: '2rem' }}>
                    <div className="stat-card">
                        <div className="flex justify-between items-start">
                            <div>
                                <p className="label">Attendance</p>
                                <p style={{ fontSize: '2.5rem', fontWeight: 800, color: attendancePct >= 75 ? '#22c55e' : '#ef4444' }}>
                                    {attendancePct}%
                                </p>
                            </div>
                            <span className={`badge ${attendanceBadge}`}>{attendanceLabel}</span>
                        </div>
                        <div className="progress-bar" style={{ marginTop: '0.75rem' }}>
                            <div className={`progress-fill ${attendancePct >= 75 ? 'success' : 'danger'}`}
                                style={{ width: `${Math.min(attendancePct, 100)}%` }}></div>
                        </div>
                    </div>

                    <div className="stat-card accent">
                        <div className="flex justify-between items-start">
                            <div>
                                <p className="label">Avg. Score</p>
                                <p style={{ fontSize: '2.5rem', fontWeight: 800, color: '#f59e0b' }}>{avgMarks}%</p>
                            </div>
                            <span className={`badge ${marksBadge}`}>
                                {avgMarks >= 80 ? 'Excellent' : avgMarks >= 60 ? 'Good' : 'Needs Work'}
                            </span>
                        </div>
                        <div className="progress-bar" style={{ marginTop: '0.75rem' }}>
                            <div className="progress-fill accent" style={{ width: `${Math.min(avgMarks, 100)}%` }}></div>
                        </div>
                        <p className="text-xs text-muted" style={{ marginTop: '0.5rem' }}>
                            {marks.length} assessments across {Object.keys(subjectMap).length} subjects
                        </p>
                    </div>

                    <div className="stat-card danger">
                        <p className="label">Active Alerts</p>
                        <p style={{ fontSize: '2.5rem', fontWeight: 800, color: unreadAlerts.length > 0 ? '#ef4444' : '#22c55e' }}>
                            {unreadAlerts.length}
                        </p>
                        <p className="text-xs text-muted" style={{ marginTop: '0.5rem' }}>
                            {unreadAlerts.length === 0 ? 'All clear! 🎉' : 'Action required'}
                        </p>
                    </div>
                </div>

                {/* Alerts Section */}
                {unreadAlerts.length > 0 && (
                    <div className="card" style={{ marginBottom: '2rem', borderLeft: '4px solid var(--danger)' }}>
                        <h2 style={{ border: 'none', paddingBottom: 0, marginBottom: '0.75rem' }}>⚠️ Your Alerts</h2>
                        <div className="flex flex-col gap-2">
                            {unreadAlerts.map((alert, i) => (
                                <div key={i} style={{
                                    padding: '0.75rem',
                                    borderRadius: 'var(--radius-sm)',
                                    background: alert.type === 'Low Attendance' ? 'var(--warning-light)' : 'var(--danger-light)',
                                    borderLeft: `3px solid ${alert.type === 'Low Attendance' ? '#f59e0b' : '#ef4444'}`
                                }}>
                                    <p className="text-sm font-semibold">{alert.type}</p>
                                    <p className="text-xs text-muted">{alert.message}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Subject Grid */}
                <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>Your Subjects</h2>
                <div className="grid grid-auto">
                    {Object.entries(subjectMap).map(([subjectName, subMarks], i) => {
                        const avg = (subMarks.reduce((s, m) => s + m.score, 0) / subMarks.length).toFixed(0);
                        const scoreColor = avg >= 80 ? '#22c55e' : avg >= 60 ? '#f59e0b' : '#ef4444';
                        return (
                            <div key={i} className="card" style={{ padding: '1.25rem', marginBottom: 0, cursor: 'default' }}>
                                <div style={{
                                    height: 44, width: 44, borderRadius: 'var(--radius-sm)',
                                    background: 'var(--primary-light)', display: 'flex',
                                    alignItems: 'center', justifyContent: 'center',
                                    marginBottom: '1rem', fontWeight: 700, color: 'var(--primary)',
                                    fontSize: '0.875rem'
                                }}>
                                    {subjectName.substring(0, 2).toUpperCase()}
                                </div>
                                <p style={{ fontWeight: 600 }}>{subjectName}</p>
                                <p className="text-sm" style={{ color: scoreColor, fontWeight: 700, marginTop: '0.25rem' }}>
                                    Score: {avg}/100
                                </p>
                                <p className="text-xs text-muted">
                                    {subMarks.length} assessment{subMarks.length > 1 ? 's' : ''}
                                </p>
                            </div>
                        );
                    })}
                    {Object.keys(subjectMap).length === 0 && (
                        <div className="empty-state">
                            <div className="emoji">📚</div>
                            <p>No subjects found yet.</p>
                        </div>
                    )}
                </div>
            </div>
        </>
    );
};

export default StudentDashboard;
