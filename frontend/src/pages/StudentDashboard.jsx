
import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import analyticsService from '../services/analytics.service';
import api from '../services/api';
import Navbar from '../components/Navbar';
import toast, { Toaster } from 'react-hot-toast';

const StudentDashboard = () => {
    const { user } = useAuth();
    const [profile, setProfile] = useState(null);
    const [analytics, setAnalytics] = useState(null);
    const [marks, setMarks] = useState([]);
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [upcomingAssignments, setUpcomingAssignments] = useState([]);
    const [attendanceRecords, setAttendanceRecords] = useState([]);
    const [riskPrediction, setRiskPrediction] = useState(null);
    const [attMode, setAttMode] = useState('till_now');
    const [attFrom, setAttFrom] = useState('');
    const [attTo, setAttTo] = useState('');

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const profileRes = await api.get('/students/me');
                setProfile(profileRes.data);
                const sid = profileRes.data.id;

                const [marksRes, alertsRes, analyticsRes] = await Promise.all([
                    api.get(`/students/${sid}/marks`),
                    api.get('/alerts/').catch(() => ({ data: [] })),
                    analyticsService.getStudentAnalytics(sid).then(d => ({ data: d })).catch(() => ({ data: null }))
                ]);
                setMarks(marksRes.data);
                setAlerts(alertsRes.data);
                setAnalytics(analyticsRes.data);

                // Fetch ML risk prediction
                try {
                    const riskRes = await analyticsService.predictRisk(sid);
                    setRiskPrediction(riskRes);
                } catch { setRiskPrediction(null); }

                // Fetch attendance records
                try {
                    const attRes = await api.get(`/students/${sid}/attendance`);
                    setAttendanceRecords(attRes.data || []);
                } catch { setAttendanceRecords([]); }

                // Fetch upcoming assignments
                try {
                    const assignRes = await api.get('/assignments/');
                    const upcoming = (assignRes.data || [])
                        .filter(a => a.due_date && new Date(a.due_date) > new Date())
                        .sort((a, b) => new Date(a.due_date) - new Date(b.due_date))
                        .slice(0, 5);
                    setUpcomingAssignments(upcoming);
                } catch { setUpcomingAssignments([]); }
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
                    <div className="grid grid-3" style={{ marginTop: '2rem' }}>
                        {[1, 2, 3].map(i => <div key={i} className="skeleton skeleton-card"></div>)}
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

    // Use CGPA from analytics (credit-weighted, consistent with full profile)
    const cgpa = analytics?.cgpa || "0.00";
    const cgpaNum = parseFloat(cgpa);
    const marksBadge = cgpaNum >= 8.0 ? 'badge-safe' : cgpaNum >= 6.0 ? 'badge-warning' : 'badge-danger';

    // Build subject list from analytics (includes labs even without marks)
    const currentSubjects = analytics?.current_semester_details?.subjects || [];

    // Also build subject map from marks for grade info
    const subjectMap = {};
    marks.forEach(m => {
        if (m.semester && profile?.current_semester) {
            if (Number(m.semester) !== Number(profile.current_semester)) return;
        }
        const name = m.subject_name || `Subject ${m.subject_id}`;
        if (!subjectMap[m.subject_id]) subjectMap[m.subject_id] = { name, items: [] };
        subjectMap[m.subject_id].items.push(m);
    });

    // Merge: use analytics subjects as base (includes labs), enrich with marks data
    const allSubjects = currentSubjects.length > 0
        ? currentSubjects.map(s => ({
            id: s.subject_id,
            name: s.subject_name,
            code: s.subject_code,
            type: s.subject_type,
            credits: s.credits,
            attendance: s.attendance_percentage || 0,
            marksItems: subjectMap[s.subject_id]?.items || [],
            avgGrade: subjectMap[s.subject_id]?.items?.length > 0
                ? (subjectMap[s.subject_id].items.reduce((sum, m) => sum + (m.score / m.total) * 100, 0) / subjectMap[s.subject_id].items.length).toFixed(0)
                : null
        }))
        : Object.entries(subjectMap).map(([id, data]) => ({
            id: Number(id),
            name: data.name,
            code: '',
            type: 'theory',
            credits: 0,
            attendance: 0,
            marksItems: data.items,
            avgGrade: (data.items.reduce((sum, m) => sum + (m.score / m.total) * 100, 0) / data.items.length).toFixed(0)
        }));

    const unreadAlerts = alerts.filter(a => !a.is_read);

    // Risk status colors and labels
    const riskColors = {
        'Safe': { bg: 'linear-gradient(135deg, #dcfce7 0%, #f0fdf4 100%)', border: '#86efac', color: '#166534', icon: '🛡️' },
        'Warning': { bg: 'linear-gradient(135deg, #fef3c7 0%, #fffbeb 100%)', border: '#fcd34d', color: '#92400e', icon: '⚠️' },
        'At Risk': { bg: 'linear-gradient(135deg, #fecaca 0%, #fef2f2 100%)', border: '#fca5a5', color: '#991b1b', icon: '🚨' }
    };
    const riskStyle = riskColors[riskPrediction?.risk_status] || riskColors['Safe'];

    return (
        <>
            <Navbar />
            
            <div className="container page-enter">
                {/* Header */}
                <div className="flex justify-between items-end" style={{ marginBottom: '2rem' }}>
                    <div>
                        <h1 style={{ marginBottom: '0.25rem', fontSize: '2rem' }}>
                            Welcome, {user?.username || profile?.name || 'Student'} 👋
                        </h1>
                        <p className="text-muted">
                            Roll No: <strong>{profile?.enrollment_number}</strong> &nbsp;•&nbsp; Semester {profile?.current_semester}
                        </p>
                    </div>
                    <Link to="/student/detail">
                        <button>View Full Profile →</button>
                    </Link>
                </div>

                {/* Stats Cards */}
                <div className="grid grid-3" style={{ marginBottom: '2rem' }}>
                    <div className="stat-card" style={{ padding: '1rem' }}>
                        <div className="flex justify-between items-start">
                            <div>
                                <p className="label">Attendance</p>
                                <p style={{ fontSize: '2rem', fontWeight: 800, color: attendancePct >= 75 ? '#22c55e' : '#ef4444' }}>
                                    {attendancePct}%
                                </p>
                            </div>
                            <span className={`badge ${attendanceBadge}`}>{attendanceLabel}</span>
                        </div>
                        <div style={{ marginTop: '0.5rem', background: 'var(--border)', borderRadius: '6px', height: '6px', overflow: 'hidden' }}>
                            <div style={{ width: `${attendancePct}%`, height: '100%', background: attendancePct >= 75 ? '#22c55e' : '#ef4444', borderRadius: '6px', transition: 'width 0.4s ease' }} />
                        </div>
                        {attendancePct < 75 && (
                            <p className="text-xs" style={{ marginTop: '0.25rem', color: '#ef4444', fontWeight: 600 }}>
                                ⚠️ attendance is less than 75 % please attend the classes regularly
                            </p>
                        )}
                    </div>

                    <div className="stat-card accent" style={{ padding: '1rem' }}>
                        <div className="flex justify-between items-start">
                            <div>
                                <p className="label">CGPA</p>
                                <p style={{ fontSize: '2rem', fontWeight: 800, color: '#f59e0b' }}>{cgpa}/10</p>
                            </div>
                            <span className={`badge ${marksBadge}`}>
                                {cgpaNum >= 8.0 ? 'Excellent' : cgpaNum >= 6.0 ? 'Good' : 'Needs Work'}
                            </span>
                        </div>
                    </div>

                    {/* ML Risk Classifier Card */}
                    <div className="stat-card" style={{
                        padding: '1rem',
                        background: riskStyle.bg,
                        border: `1px solid ${riskStyle.border}`
                    }}>
                        <div className="flex justify-between items-start">
                            <div>
                                <p className="label" style={{ color: riskStyle.color }}>🤖 Risk Status</p>
                                <p style={{ fontSize: '1.75rem', fontWeight: 800, color: riskStyle.color }}>
                                    {riskPrediction ? `${riskStyle.icon} ${riskPrediction.risk_status}` : 'Loading...'}
                                </p>
                            </div>
                            {riskPrediction && (
                                <span style={{
                                    fontSize: '0.6rem', fontWeight: 700, padding: '2px 8px',
                                    borderRadius: 10, background: riskStyle.border, color: riskStyle.color
                                }}>
                                    {(riskPrediction.confidence * 100).toFixed(0)}% confident
                                </span>
                            )}
                        </div>
                        {riskPrediction && (
                            <div style={{ marginTop: '0.4rem' }}>
                                <p className="text-xs" style={{ color: riskStyle.color, fontWeight: 500, lineHeight: 1.4 }}>
                                    {riskPrediction.recommendation}
                                </p>
                                <span style={{
                                    display: 'inline-block', marginTop: '0.3rem',
                                    fontSize: '0.55rem', color: riskStyle.color,
                                    background: 'rgba(255,255,255,0.5)', padding: '2px 6px', borderRadius: 8
                                }}>
                                    {riskPrediction.model_type}
                                </span>
                            </div>
                        )}
                    </div>
                </div>

                {/* Alerts Section (kept for any actual alerts) */}
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

                {/* Subject Grid (now includes labs + all subjects from analytics) */}
                <h2 style={{ fontSize: '1.25rem', marginBottom: '1.5rem' }}>Your Subjects</h2>
                <div className="grid grid-auto" style={{ gap: '1.5rem' }}>
                    {allSubjects.map((sub, i) => {
                        const GRADIENTS = [
                            'linear-gradient(135deg, #00796b 0%, #004d40 100%)',
                            'linear-gradient(135deg, #1967d2 0%, #174ea6 100%)',
                            'linear-gradient(135deg, #d93025 0%, #a50e0e 100%)',
                            'linear-gradient(135deg, #a142f4 0%, #512da8 100%)',
                            'linear-gradient(135deg, #f97316 0%, #ea580c 100%)'
                        ];
                        const gradient = GRADIENTS[i % GRADIENTS.length];
                        const typeLabel = (sub.type || '').toLowerCase();
                        const typeEmoji = typeLabel === 'lab' ? '🔬' : typeLabel === 'nptel' ? '📺' : typeLabel === 'non_credit' ? '📘' : '📖';
                        
                        return (
                            <Link to={`/student/subject/${sub.id}`} key={i} className="classroom-card">
                                <div className="classroom-header" style={{ background: gradient }}>
                                    <h3 title={sub.name}>{sub.name}</h3>
                                    <p>Section {profile?.section_name || 'A'} • {typeEmoji} {typeLabel || 'theory'}</p>
                                    <div className="classroom-avatar">
                                        {sub.name.substring(0, 1).toUpperCase()}
                                    </div>
                                </div>
                                <div className="classroom-body">
                                    <p className="text-sm" style={{ fontWeight: 600 }}>
                                        Attendance: <span style={{ color: sub.attendance >= 75 ? '#22c55e' : '#ef4444' }}>{sub.attendance}%</span>
                                    </p>
                                    <p className="text-xs text-muted" style={{ marginTop: '0.25rem' }}>
                                        {sub.credits > 0 ? `${sub.credits} credits` : ''} {(sub.type || 'theory').toUpperCase()}
                                    </p>
                                </div>
                                <div className="classroom-footer">
                                    <span title="Assignments">📝</span>
                                    <span title="Materials">📁</span>
                                </div>
                            </Link>
                        );
                    })}
                    {allSubjects.length === 0 && (
                        <div className="empty-state" style={{ gridColumn: '1 / -1' }}>
                            <div className="emoji">📚</div>
                            <p>No subjects found yet.</p>
                        </div>
                    )}
                </div>

                {/* Bottom row: Upcoming Deadlines + Recent Attendance */}
                <div className="grid grid-2" style={{ gap: '1.5rem', marginTop: '2rem' }}>
                    {/* Upcoming Deadlines */}
                    <div className="card" style={{ padding: '1.5rem' }}>
                        <h2 style={{ fontSize: '1.1rem', margin: '0 0 1rem', border: 'none', paddingBottom: 0 }}>⏰ Upcoming Deadlines</h2>
                        {upcomingAssignments.length === 0 ? (
                            <p className="text-muted text-center" style={{ padding: '1.5rem 0' }}>🎉 No upcoming deadlines!</p>
                        ) : (
                            <div className="flex flex-col gap-3">
                                {upcomingAssignments.map((a, i) => {
                                    const dueDate = new Date(a.due_date);
                                    const daysLeft = Math.ceil((dueDate - new Date()) / (1000 * 60 * 60 * 24));
                                    return (
                                        <div key={i} className="flex items-center gap-3" style={{ padding: '0.6rem 0', borderBottom: '1px solid var(--border)' }}>
                                            <div style={{ width: 36, height: 36, borderRadius: '8px', background: daysLeft <= 2 ? 'rgba(239,68,68,0.15)' : 'rgba(59,130,246,0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1rem', flexShrink: 0 }}>
                                                📝
                                            </div>
                                            <div className="flex-1">
                                                <p className="text-sm font-semibold" style={{ margin: 0 }}>{a.title}</p>
                                                <p className="text-xs text-muted" style={{ margin: 0 }}>{a.subject_name || 'Subject'}</p>
                                            </div>
                                            <span className="badge" style={{ fontSize: '0.65rem', fontWeight: 700, background: daysLeft <= 2 ? 'rgba(239,68,68,0.15)' : 'rgba(59,130,246,0.15)', color: daysLeft <= 2 ? '#ef4444' : '#3b82f6' }}>
                                                {daysLeft <= 0 ? 'Due today!' : `${daysLeft}d left`}
                                            </span>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>

                    {/* Attendance Report */}
                    <div className="card" style={{ padding: '1.5rem' }}>
                        <div className="flex items-center" style={{ justifyContent: 'space-between', marginBottom: '1rem' }}>
                            <h2 style={{ fontSize: '1.1rem', margin: 0, border: 'none', paddingBottom: 0 }}>📋 Attendance Report</h2>
                        </div>
                        {/* Mode Toggles */}
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
                            <div style={{ display: 'flex', borderRadius: 8, overflow: 'hidden', border: '1px solid var(--border)' }}>
                                <button
                                    onClick={() => setAttMode('till_now')}
                                    style={{
                                        padding: '0.4rem 1rem', border: 'none', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600,
                                        background: attMode === 'till_now' ? '#6366f1' : 'transparent',
                                        color: attMode === 'till_now' ? '#fff' : '#64748b'
                                    }}
                                >Till Now</button>
                                <button
                                    onClick={() => setAttMode('period')}
                                    style={{
                                        padding: '0.4rem 1rem', border: 'none', borderLeft: '1px solid var(--border)', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600,
                                        background: attMode === 'period' ? '#6366f1' : 'transparent',
                                        color: attMode === 'period' ? '#fff' : '#64748b'
                                    }}
                                >Period</button>
                            </div>
                            {attMode === 'period' && (
                                <>
                                    <div className="flex items-center gap-2" style={{ fontSize: '0.8rem' }}>
                                        <label style={{ fontWeight: 600, color: '#475569' }}>From:</label>
                                        <input type="date" value={attFrom} onChange={e => setAttFrom(e.target.value)} style={{ padding: '0.3rem 0.5rem', borderRadius: 6, border: '1px solid var(--border)', fontSize: '0.8rem' }} />
                                    </div>
                                    <div className="flex items-center gap-2" style={{ fontSize: '0.8rem' }}>
                                        <label style={{ fontWeight: 600, color: '#475569' }}>To:</label>
                                        <input type="date" value={attTo} onChange={e => setAttTo(e.target.value)} style={{ padding: '0.3rem 0.5rem', borderRadius: 6, border: '1px solid var(--border)', fontSize: '0.8rem' }} />
                                    </div>
                                </>
                            )}
                        </div>
                        {/* Table */}
                        {(() => {
                            let subjects;
                            if (attMode === 'till_now') {
                                subjects = (analytics?.current_semester_details?.subjects || []).map(sub => ({
                                    code: sub.subject_code || '',
                                    name: sub.subject_name || '',
                                    held: sub.total_classes || 0,
                                    attended: sub.classes_attended || 0,
                                    pct: sub.attendance_percentage || 0
                                }));
                            } else {
                                // Filter raw attendance records by date range
                                const fromDate = attFrom ? new Date(attFrom) : null;
                                const toDate = attTo ? new Date(attTo) : null;
                                const filtered = attendanceRecords.filter(r => {
                                    const d = new Date(r.date);
                                    if (fromDate && d < fromDate) return false;
                                    if (toDate && d > toDate) return false;
                                    return true;
                                });
                                // Group by subject
                                const subMap = {};
                                filtered.forEach(r => {
                                    const key = r.subject_name || r.subject_id || 'Unknown';
                                    if (!subMap[key]) subMap[key] = { name: r.subject_name || 'Unknown', code: '', held: 0, attended: 0 };
                                    subMap[key].held++;
                                    if (r.status) subMap[key].attended++;
                                });
                                // Try to get subject codes from analytics
                                const analyticsSubs = analytics?.current_semester_details?.subjects || [];
                                subjects = Object.values(subMap).map(s => {
                                    const match = analyticsSubs.find(as => as.subject_name === s.name);
                                    return {
                                        ...s,
                                        code: match?.subject_code || s.code,
                                        pct: s.held > 0 ? (s.attended / s.held * 100) : 0
                                    };
                                });
                            }
                            if (subjects.length === 0) return <p className="text-muted text-center" style={{ padding: '1.5rem 0' }}>{attMode === 'period' ? 'No records found for the selected period.' : 'No attendance records yet.'}</p>;
                            const totalHeld = subjects.reduce((s, sub) => s + sub.held, 0);
                            const totalAttended = subjects.reduce((s, sub) => s + sub.attended, 0);
                            const overallPct = totalHeld > 0 ? ((totalAttended / totalHeld) * 100).toFixed(2) : '0.00';
                            return (
                                <div style={{ overflowX: 'auto' }}>
                                    <table style={{ margin: 0, fontSize: '0.85rem', width: '100%' }}>
                                        <thead>
                                            <tr style={{ background: '#f8fafc' }}>
                                                <th style={{ textAlign: 'left', padding: '0.6rem 0.75rem', fontWeight: 700, fontSize: '0.75rem', color: '#475569', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Subject</th>
                                                <th style={{ textAlign: 'center', padding: '0.6rem 0.75rem', fontWeight: 700, fontSize: '0.75rem', color: '#475569', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Held</th>
                                                <th style={{ textAlign: 'center', padding: '0.6rem 0.75rem', fontWeight: 700, fontSize: '0.75rem', color: '#475569', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Attended</th>
                                                <th style={{ textAlign: 'center', padding: '0.6rem 0.75rem', fontWeight: 700, fontSize: '0.75rem', color: '#475569', textTransform: 'uppercase', letterSpacing: '0.5px' }}>%</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {subjects.map((sub, i) => {
                                                const pct = sub.pct;
                                                const pctColor = pct >= 75 ? '#22c55e' : pct >= 65 ? '#f59e0b' : '#ef4444';
                                                return (
                                                    <tr key={i} style={{ borderBottom: '1px solid #f1f5f9' }}>
                                                        <td style={{ padding: '0.6rem 0.75rem' }}>
                                                            <span style={{ fontWeight: 600 }}>{sub.code || sub.name?.substring(0, 6)}</span>
                                                            <span className="text-xs text-muted" style={{ marginLeft: 6 }}>{sub.name?.length > 20 ? sub.name.substring(0, 20) + '…' : sub.name}</span>
                                                        </td>
                                                        <td style={{ textAlign: 'center', padding: '0.6rem 0.75rem', fontWeight: 600 }}>{sub.held}</td>
                                                        <td style={{ textAlign: 'center', padding: '0.6rem 0.75rem', fontWeight: 600 }}>{sub.attended}</td>
                                                        <td style={{ textAlign: 'center', padding: '0.6rem 0.75rem' }}>
                                                            <span style={{
                                                                fontWeight: 700, color: pctColor,
                                                                background: pct >= 75 ? 'rgba(34,197,94,0.1)' : pct >= 65 ? 'rgba(245,158,11,0.1)' : 'rgba(239,68,68,0.1)',
                                                                padding: '2px 8px', borderRadius: 12, fontSize: '0.8rem'
                                                            }}>{pct.toFixed(2)}</span>
                                                        </td>
                                                    </tr>
                                                );
                                            })}
                                        </tbody>
                                        <tfoot>
                                            <tr style={{ background: '#f1f5f9', fontWeight: 700 }}>
                                                <td style={{ padding: '0.7rem 0.75rem', fontSize: '0.85rem' }}>TOTAL</td>
                                                <td style={{ textAlign: 'center', padding: '0.7rem 0.75rem' }}>{totalHeld}</td>
                                                <td style={{ textAlign: 'center', padding: '0.7rem 0.75rem' }}>{totalAttended}</td>
                                                <td style={{ textAlign: 'center', padding: '0.7rem 0.75rem' }}>
                                                    <span style={{
                                                        fontWeight: 800, fontSize: '0.85rem',
                                                        color: overallPct >= 75 ? '#22c55e' : overallPct >= 65 ? '#f59e0b' : '#ef4444'
                                                    }}>{overallPct}</span>
                                                </td>
                                            </tr>
                                        </tfoot>
                                    </table>
                                </div>
                            );
                        })()}
                    </div>
                </div>
            </div>
        </>
    );
};

export default StudentDashboard;
