
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import Navbar from '../components/Navbar';
import toast, { Toaster } from 'react-hot-toast';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, PieChart, Pie } from 'recharts';

const MentorDashboard = () => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [stats, setStats] = useState(null);
    const [students, setStudents] = useState([]);
    const [search, setSearch] = useState('');
    const [loading, setLoading] = useState(true);
    const [showRemark, setShowRemark] = useState(null);
    const [remarkText, setRemarkText] = useState('');
    const [classPerf, setClassPerf] = useState([]);
    const [assignmentStats, setAssignmentStats] = useState([]);
    const [expandedAssignment, setExpandedAssignment] = useState(null);
    const [expandedSubject, setExpandedSubject] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const [dashRes, studentsRes, perfRes] = await Promise.allSettled([
                    api.get('/faculty/dashboard'),
                    api.get('/faculty/my-students'),
                    api.get('/faculty/class-performance')
                ]);
                if (dashRes.status === 'fulfilled') setStats(dashRes.value.data);
                if (studentsRes.status === 'fulfilled') setStudents(studentsRes.value.data);
                if (perfRes.status === 'fulfilled') setClassPerf(perfRes.value.data || []);
                // Fetch assignment submission stats
                try {
                    const asgRes = await api.get('/faculty/mentor-assignment-stats');
                    setAssignmentStats(asgRes.data || []);
                } catch { setAssignmentStats([]); }
            } catch (err) {
                console.error("Error in Mentor Dashboard fetchData:", err);
                toast.error('Failed to load mentor data');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const filteredStudents = students.filter(s =>
        (s.name || "").toLowerCase().includes(search.toLowerCase()) ||
        (s.enrollment_number || "").toLowerCase().includes(search.toLowerCase())
    );

    const handleAddRemark = async (studentId) => {
        if (!remarkText.trim()) return;
        try {
            await api.post('/faculty/remarks', { student_id: studentId, message: remarkText });
            toast.success('Remark added!');
            setShowRemark(null);
            setRemarkText('');
        } catch (err) {
            toast.error('Failed to add remark');
        }
    };

    const handleAcknowledge = async (alertId, studentId) => {
        try {
            await api.post(`/alerts/read/${alertId}`);
            navigate(`/student/detail?id=${studentId}`);
        } catch (err) {
            console.error('Failed to acknowledge alert', err);
            navigate(`/student/detail?id=${studentId}`);
        }
    };

    // --- Computed data for new widgets ---
    const riskCounts = { safe: 0, warning: 0, critical: 0 };
    students.forEach(s => {
        const r = (s.risk_status || '').toLowerCase();
        if (r === 'at risk') riskCounts.critical++;
        else if (r === 'warning') riskCounts.warning++;
        else riskCounts.safe++;
    });

    const donutData = [
        { name: 'Safe', value: riskCounts.safe, color: '#22c55e' },
        { name: 'Warning', value: riskCounts.warning, color: '#f59e0b' },
        { name: 'At Risk', value: riskCounts.critical, color: '#ef4444' },
    ].filter(d => d.value > 0);

    const attentionStudents = students
        .filter(s => s.attendance_percentage < 75 || s.average_marks < 40)
        .sort((a, b) => a.attendance_percentage - b.attendance_percentage)
        .slice(0, 6);

    const topPerformers = [...students]
        .sort((a, b) => b.average_marks - a.average_marks)
        .slice(0, 3);

    if (loading) {
        return (
            <>
                <Navbar />
                <div className="container page-enter">
                    <div className="grid grid-2" style={{ marginTop: '2rem' }}>
                        {[1, 2].map(i => <div key={i} className="skeleton skeleton-card"></div>)}
                    </div>
                    <div className="skeleton" style={{ height: 300, marginTop: '1.5rem' }}></div>
                </div>
            </>
        );
    }

    return (
        <>
            <Navbar />
            <div className="container page-enter">
                <div style={{ marginBottom: '2rem' }}>
                    <h1>Mentor Dashboard</h1>
                    <p className="text-muted" style={{ marginBottom: '0.25rem' }}>Monitor and guide your assigned students.</p>
                    {stats && (stats.section_name || stats.year) && (
                        <p style={{ fontSize: '0.9rem', color: '#475569', fontWeight: 500 }}>
                            {stats.year && <span>📅 {stats.year}{stats.year === 1 ? 'st' : stats.year === 2 ? 'nd' : stats.year === 3 ? 'rd' : 'th'} Year</span>}
                            {stats.year && <span style={{ margin: '0 0.5rem', color: '#cbd5e1' }}>•</span>}
                            <span>🎓 CSE</span>
                            {stats.section_name && <span style={{ margin: '0 0.5rem', color: '#cbd5e1' }}>•</span>}
                            {stats.section_name && <span>🏫 {stats.section_name}</span>}
                            {stats.current_semester && <span style={{ margin: '0 0.5rem', color: '#cbd5e1' }}>•</span>}
                            {stats.current_semester && <span>📖 Semester {stats.current_semester}</span>}
                        </p>
                    )}
                </div>

                {/* Stats Row */}
                {stats && (
                    <div className="grid grid-2" style={{ marginBottom: '2rem' }}>
                        <div className="stat-card">
                            <p className="label">Total Students</p>
                            <p style={{ fontSize: '2.25rem', fontWeight: 800, color: 'var(--primary)' }}>{stats.total_students}</p>
                        </div>
                        <div className="stat-card danger">
                            <p className="label">At Risk</p>
                            <p style={{ fontSize: '2.25rem', fontWeight: 800, color: '#ef4444' }}>{stats.at_risk_count}</p>
                        </div>
                    </div>
                )}

                {/* Donut Chart + Top Performers side by side */}
                {students.length > 0 && (
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '2rem' }}>

                        {/* Mentee Status Donut Chart */}
                        <div className="card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                            <h2 style={{ border: 'none', paddingBottom: 0, marginBottom: '0.5rem', alignSelf: 'flex-start' }}>🎯 Mentee Risk Overview</h2>
                            <p className="text-muted" style={{ fontSize: '0.8rem', alignSelf: 'flex-start', marginBottom: '1rem' }}>Student distribution by risk status</p>
                            <div style={{ position: 'relative', width: 220, height: 220 }}>
                                <ResponsiveContainer width="100%" height="100%">
                                    <PieChart>
                                        <Pie
                                            data={donutData}
                                            cx="50%"
                                            cy="50%"
                                            innerRadius={60}
                                            outerRadius={95}
                                            paddingAngle={4}
                                            dataKey="value"
                                            stroke="none"
                                        >
                                            {donutData.map((entry, i) => (
                                                <Cell key={i} fill={entry.color} />
                                            ))}
                                        </Pie>
                                        <Tooltip
                                            formatter={(value, name) => [`${value} students`, name]}
                                            contentStyle={{ borderRadius: 8, fontSize: '0.85rem', border: '1px solid #e2e8f0' }}
                                        />
                                    </PieChart>
                                </ResponsiveContainer>
                                <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', textAlign: 'center' }}>
                                    <p style={{ fontSize: '1.75rem', fontWeight: 800, margin: 0, lineHeight: 1 }}>{students.length}</p>
                                    <p style={{ fontSize: '0.7rem', color: '#94a3b8', margin: 0 }}>Total</p>
                                </div>
                            </div>
                            <div style={{ display: 'flex', gap: '1.25rem', marginTop: '1rem', fontSize: '0.85rem' }}>
                                <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}><div style={{ width: 10, height: 10, borderRadius: '50%', background: '#22c55e' }}></div> Safe <strong>({riskCounts.safe})</strong></span>
                                <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}><div style={{ width: 10, height: 10, borderRadius: '50%', background: '#f59e0b' }}></div> Warning <strong>({riskCounts.warning})</strong></span>
                                <span style={{ display: 'flex', alignItems: 'center', gap: 6 }}><div style={{ width: 10, height: 10, borderRadius: '50%', background: '#ef4444' }}></div> At Risk <strong>({riskCounts.critical})</strong></span>
                            </div>
                        </div>

                        {/* Top Performers */}
                        <div className="card" style={{ padding: '1.5rem' }}>
                            <h2 style={{ border: 'none', paddingBottom: 0, marginBottom: '0.5rem' }}>🏆 Top Performers</h2>
                            <p className="text-muted" style={{ fontSize: '0.8rem', marginBottom: '1.25rem' }}>Highest average marks among your mentees</p>
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                {topPerformers.map((s, i) => {
                                    const medals = ['🥇', '🥈', '🥉'];
                                    const bgColors = ['#fefce8', '#f8fafc', '#fff7ed'];
                                    const borderColors = ['#eab308', '#cbd5e1', '#f97316'];
                                    return (
                                        <div
                                            key={s.id}
                                            onClick={() => navigate(`/student/detail?id=${s.id}`)}
                                            style={{
                                                display: 'flex', alignItems: 'center', gap: '1rem',
                                                padding: '0.85rem 1rem', borderRadius: 12,
                                                background: bgColors[i], border: `1.5px solid ${borderColors[i]}`,
                                                cursor: 'pointer', transition: 'transform 0.15s ease',
                                            }}
                                            onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.02)'}
                                            onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
                                        >
                                            <span style={{ fontSize: '1.75rem' }}>{medals[i]}</span>
                                            <div style={{ flex: 1 }}>
                                                <p style={{ margin: 0, fontWeight: 700, fontSize: '0.95rem' }}>{s.name}</p>
                                                <p style={{ margin: 0, fontSize: '0.75rem', color: '#64748b' }}>{s.enrollment_number}</p>
                                            </div>
                                            <div style={{ textAlign: 'right' }}>
                                                <p style={{ margin: 0, fontWeight: 800, fontSize: '1.2rem', color: '#6366f1' }}>{s.average_marks?.toFixed(1)}%</p>
                                                <p style={{ margin: 0, fontSize: '0.7rem', color: '#64748b' }}>Avg Marks</p>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                            {topPerformers.length === 0 && (
                                <p className="text-muted" style={{ textAlign: 'center', padding: '2rem 0' }}>No student data available.</p>
                            )}
                        </div>
                    </div>
                )}

                {/* Class Performance Chart */}
                {classPerf.length > 0 && (
                    <div className="card" style={{ marginBottom: '2rem', padding: '1.5rem' }}>
                        <h2 style={{ border: 'none', paddingBottom: 0, marginBottom: '1rem' }}>📊 Class Performance by Subject</h2>
                        <p className="text-muted" style={{ marginBottom: '0.5rem', fontSize: '0.85rem' }}>Average marks (%) of your mentees — Current Semester</p>
                        <div className="flex gap-4" style={{ marginBottom: '1rem', fontSize: '0.8rem' }}>
                            <span className="flex items-center gap-1"><div style={{ width: 12, height: 12, borderRadius: 3, background: '#6366f1' }}></div> Theory</span>
                            <span className="flex items-center gap-1"><div style={{ width: 12, height: 12, borderRadius: 3, background: '#f59e0b' }}></div> Lab</span>
                            <span className="flex items-center gap-1"><div style={{ width: 12, height: 12, borderRadius: 3, background: '#94a3b8' }}></div> Non-Credit</span>
                        </div>
                        <ResponsiveContainer width="100%" height={350}>
                            <BarChart data={classPerf} margin={{ top: 10, right: 30, left: 0, bottom: 60 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                                <XAxis dataKey="subject_name" angle={-45} textAnchor="end" tick={{ fontSize: 10, fill: '#64748b' }} interval={0} height={100} />
                                <YAxis domain={[0, 100]} tick={{ fontSize: 12, fill: '#64748b' }} label={{ value: 'Avg %', angle: -90, position: 'insideLeft', style: { fontSize: 12, fill: '#94a3b8' } }} />
                                <Tooltip formatter={(value, name) => [`${value}%`, 'Class Average']} labelFormatter={(label) => label} contentStyle={{ borderRadius: 8, border: '1px solid #e2e8f0', fontSize: '0.85rem' }} />
                                <Bar dataKey="average" radius={[6, 6, 0, 0]} maxBarSize={50}>
                                    {classPerf.map((entry, index) => {
                                        let color = '#6366f1';
                                        const type = (entry.subject_type || '').toUpperCase();
                                        if (entry.credits === 0) { color = '#94a3b8'; }
                                        else if (type === 'LAB') { color = '#f59e0b'; }
                                        return <Cell key={index} fill={color} />;
                                    })}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                )}

                {/* Requires Attention Panel */}
                {attentionStudents.length > 0 && (
                    <div className="card" style={{ marginBottom: '2rem', padding: '1.5rem' }}>
                        <h2 style={{ border: 'none', paddingBottom: 0, marginBottom: '0.5rem' }}>⚠️ Requires Attention</h2>
                        <p className="text-muted" style={{ fontSize: '0.8rem', marginBottom: '1rem' }}>Students with attendance below 75% or average marks below 40%</p>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '0.75rem' }}>
                            {attentionStudents.map(s => {
                                const lowAtt = s.attendance_percentage < 75;
                                const lowMarks = s.average_marks < 40;
                                return (
                                    <div
                                        key={s.id}
                                        onClick={() => navigate(`/student/detail?id=${s.id}`)}
                                        style={{
                                            display: 'flex', alignItems: 'center', gap: '0.75rem',
                                            padding: '0.85rem 1rem', borderRadius: 12,
                                            background: lowAtt && lowMarks ? '#fef2f2' : lowAtt ? '#fffbeb' : '#fef2f2',
                                            border: `1.5px solid ${lowAtt && lowMarks ? '#fca5a5' : lowAtt ? '#fcd34d' : '#fca5a5'}`,
                                            cursor: 'pointer', transition: 'transform 0.15s ease',
                                        }}
                                        onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-2px)'}
                                        onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}
                                    >
                                        <div style={{
                                            width: 38, height: 38, borderRadius: '50%',
                                            background: lowAtt && lowMarks ? '#ef4444' : lowAtt ? '#f59e0b' : '#ef4444',
                                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                                            color: '#fff', fontWeight: 800, fontSize: '0.8rem', flexShrink: 0
                                        }}>
                                            {(s.name || '?')[0].toUpperCase()}
                                        </div>
                                        <div style={{ flex: 1, minWidth: 0 }}>
                                            <p style={{ margin: 0, fontWeight: 700, fontSize: '0.9rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{s.name}</p>
                                            <div style={{ display: 'flex', gap: '0.75rem', fontSize: '0.75rem', marginTop: 2 }}>
                                                {lowAtt && <span style={{ color: '#b45309' }}>📉 Attendance: <strong>{s.attendance_percentage?.toFixed(1)}%</strong></span>}
                                                {lowMarks && <span style={{ color: '#dc2626' }}>📕 Marks: <strong>{s.average_marks?.toFixed(1)}%</strong></span>}
                                            </div>
                                        </div>
                                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 18l6-6-6-6"/></svg>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}

                {/* Active Assignments Section - Grouped by Subject */}
                {assignmentStats.length > 0 && (() => {
                    // Group assignments by subject
                    const subjectMap = {};
                    assignmentStats.forEach(a => {
                        const key = `${a.subject_name}__${a.subject_code}`;
                        if (!subjectMap[key]) subjectMap[key] = { subject_name: a.subject_name, subject_code: a.subject_code, section_name: a.section_name, assignments: [] };
                        subjectMap[key].assignments.push(a);
                    });
                    const subjectGroups = Object.values(subjectMap);
                    const now = new Date();

                    return (
                        <div style={{ marginBottom: '2rem' }}>
                            <h2 style={{ border: 'none', paddingBottom: 0, marginBottom: '0.5rem' }}>📝 Active Assignments</h2>
                            <p className="text-muted" style={{ fontSize: '0.8rem', marginBottom: '1.25rem' }}>Submission status for your mentees — grouped by subject</p>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
                                {subjectGroups.map((sg, idx) => {
                                    const totalAssignments = sg.assignments.length;
                                    const overdue = sg.assignments.filter(a => a.due_date && new Date(a.due_date) < now).length;
                                    const isSelected = expandedSubject === sg.subject_code;
                                    const subColors = ['#6366f1', '#8b5cf6', '#0ea5e9', '#14b8a6', '#f59e0b', '#ec4899'];
                                    const color = subColors[idx % subColors.length];
                                    return (
                                        <div
                                            key={sg.subject_code}
                                            onClick={() => setExpandedSubject(isSelected ? null : sg.subject_code)}
                                            className="card"
                                            style={{
                                                padding: '1.25rem 1.5rem', cursor: 'pointer',
                                                borderLeft: `4px solid ${color}`,
                                                background: isSelected ? `${color}08` : 'var(--bg-card)',
                                                transition: 'all 0.2s ease', position: 'relative',
                                                boxShadow: isSelected ? `0 0 0 1px ${color}40` : undefined
                                            }}
                                            onMouseEnter={e => { if (!isSelected) e.currentTarget.style.transform = 'translateY(-2px)'; }}
                                            onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; }}
                                        >
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                                                <div style={{
                                                    width: 40, height: 40, borderRadius: 10,
                                                    background: `${color}15`, color: color,
                                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                    fontSize: '1.1rem', fontWeight: 800
                                                }}>📚</div>
                                                <div style={{ flex: 1 }}>
                                                    <p style={{ margin: 0, fontWeight: 700, fontSize: '0.95rem' }}>{sg.subject_name}</p>
                                                    <p className="text-xs text-muted" style={{ margin: '2px 0 0' }}>{sg.subject_code}{sg.section_name ? ` • ${sg.section_name}` : ''}</p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-3" style={{ fontSize: '0.8rem' }}>
                                                <span style={{ fontWeight: 600, color }}>{totalAssignments} assignment{totalAssignments !== 1 ? 's' : ''}</span>
                                                {overdue > 0 && <span style={{ color: '#ef4444', fontWeight: 600 }}>⏰ {overdue} overdue</span>}
                                            </div>
                                            {isSelected && (
                                                <div style={{ position: 'absolute', top: 12, right: 12, fontSize: '0.7rem', color, fontWeight: 700 }}>▲ Collapse</div>
                                            )}
                                        </div>
                                    );
                                })}
                            </div>

                            {/* Expanded Subject Assignments */}
                            {subjectGroups.map(sg => {
                                if (expandedSubject !== sg.subject_code) return null;
                                const overdueList = sg.assignments.filter(a => a.due_date && new Date(a.due_date) < now);
                                const upcomingList = sg.assignments.filter(a => !a.due_date || new Date(a.due_date) >= now);

                                const renderAssignment = (a) => {
                                    const pct = a.total_students > 0 ? Math.round((a.submitted_count / a.total_students) * 100) : 0;
                                    const isExp = expandedAssignment === a.id;
                                    const barColor = pct === 100 ? '#22c55e' : pct >= 50 ? '#f59e0b' : '#ef4444';
                                    return (
                                        <div key={a.id} style={{ border: '1px solid var(--border)', borderRadius: 12, overflow: 'hidden' }}>
                                            <div style={{ padding: '1rem 1.25rem' }}>
                                                <div className="flex items-center" style={{ justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                                    <div>
                                                        <p style={{ margin: 0, fontWeight: 700, fontSize: '0.95rem' }}>{a.title}</p>
                                                        <p className="text-xs text-muted" style={{ margin: '2px 0 0' }}>{a.section_name || ''}</p>
                                                    </div>
                                                    {a.due_date && (
                                                        <span className="text-xs" style={{ whiteSpace: 'nowrap', color: new Date(a.due_date) < now ? '#ef4444' : '#64748b', fontWeight: 600 }}>
                                                            📅 {new Date(a.due_date) < now ? 'Due: ' : 'Due: '}{new Date(a.due_date).toLocaleDateString('en-IN', { dateStyle: 'medium' })}
                                                        </span>
                                                    )}
                                                </div>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                                                    <div style={{ flex: 1, height: 10, borderRadius: 5, background: '#f1f5f9', overflow: 'hidden' }}>
                                                        <div style={{ width: `${pct}%`, height: '100%', borderRadius: 5, background: barColor, transition: 'width 0.5s ease' }}></div>
                                                    </div>
                                                    <span style={{ fontSize: '0.8rem', fontWeight: 700, color: barColor, minWidth: 36, textAlign: 'right' }}>{pct}%</span>
                                                </div>
                                                <div className="flex items-center" style={{ justifyContent: 'space-between' }}>
                                                    <div className="flex gap-4" style={{ fontSize: '0.8rem' }}>
                                                        <span style={{ color: '#22c55e', fontWeight: 600 }}>✓ {a.submitted_count} submitted</span>
                                                        <span style={{ color: a.pending_count > 0 ? '#ef4444' : '#94a3b8', fontWeight: 600 }}>✗ {a.pending_count} pending</span>
                                                        <span className="text-muted">/ {a.total_students} total</span>
                                                    </div>
                                                    {a.pending_count > 0 && (
                                                        <button
                                                            onClick={() => setExpandedAssignment(isExp ? null : a.id)}
                                                            style={{
                                                                background: 'none', border: '1px solid var(--border)', borderRadius: 8,
                                                                padding: '0.3rem 0.8rem', cursor: 'pointer', fontSize: '0.75rem',
                                                                fontWeight: 600, color: '#ef4444', display: 'flex', alignItems: 'center', gap: 4
                                                            }}
                                                        >
                                                            {isExp ? '▲ Hide' : '▼ Not Submitted'} ({a.pending_count})
                                                        </button>
                                                    )}
                                                </div>
                                            </div>
                                            {isExp && a.not_submitted && a.not_submitted.length > 0 && (
                                                <div style={{ borderTop: '1px solid var(--border)', background: '#fef2f2', padding: '0.75rem 1.25rem' }}>
                                                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '0.5rem' }}>
                                                        {a.not_submitted.map(s => (
                                                            <div
                                                                key={s.student_id}
                                                                onClick={() => navigate(`/student/detail?id=${s.student_id}`)}
                                                                style={{
                                                                    display: 'flex', alignItems: 'center', gap: '0.6rem',
                                                                    padding: '0.5rem 0.75rem', borderRadius: 8,
                                                                    background: '#fff', border: '1px solid #fca5a5',
                                                                    cursor: 'pointer', transition: 'transform 0.15s ease'
                                                                }}
                                                                onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.02)'}
                                                                onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
                                                            >
                                                                <div style={{
                                                                    width: 28, height: 28, borderRadius: '50%',
                                                                    background: '#fecaca', color: '#dc2626',
                                                                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                                    fontWeight: 800, fontSize: '0.7rem', flexShrink: 0
                                                                }}>{(s.name || '?')[0].toUpperCase()}</div>
                                                                <div style={{ minWidth: 0 }}>
                                                                    <p style={{ margin: 0, fontWeight: 600, fontSize: '0.8rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{s.name}</p>
                                                                    <p style={{ margin: 0, fontSize: '0.7rem', color: '#94a3b8' }}>{s.enrollment_number}</p>
                                                                </div>
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    );
                                };

                                return (
                                    <div key={sg.subject_code} className="card" style={{ padding: '1.5rem', marginBottom: '1rem' }}>
                                        <h3 style={{ margin: '0 0 1rem', fontSize: '1.05rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                            📚 {sg.subject_name} <span className="text-muted" style={{ fontWeight: 400, fontSize: '0.85rem' }}>({sg.subject_code})</span>
                                        </h3>

                                        {/* Overdue Assignments */}
                                        {overdueList.length > 0 && (
                                            <div style={{ marginBottom: upcomingList.length > 0 ? '1.25rem' : 0 }}>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                                                    <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#ef4444', background: '#fef2f2', padding: '0.2rem 0.7rem', borderRadius: 20 }}>⏰ Overdue ({overdueList.length})</span>
                                                </div>
                                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                                    {overdueList.map(renderAssignment)}
                                                </div>
                                            </div>
                                        )}

                                        {/* Upcoming Assignments */}
                                        {upcomingList.length > 0 && (
                                            <div>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                                                    <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#2563eb', background: '#eff6ff', padding: '0.2rem 0.7rem', borderRadius: 20 }}>📋 Upcoming ({upcomingList.length})</span>
                                                </div>
                                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                                    {upcomingList.map(renderAssignment)}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    );
                })()}

                {/* Detailed Student Report CTA */}
                <div className="card accent" style={{ cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '1.5rem 2rem', borderLeft: '4px solid var(--accent)', marginBottom: '2rem' }} onClick={() => navigate('/mentor/detailed-reports')}>
                    <div>
                        <h2 style={{ border: 'none', padding: 0, margin: 0, fontSize: '1.25rem' }}>📊 Detailed Student Report</h2>
                        <p className="text-muted" style={{ margin: '0.5rem 0 0', fontSize: '0.9rem' }}>Access in-depth academic analysis, attendance trends, and behavioral risk factors for your mentees.</p>
                    </div>
                    <div className="flex items-center gap-2">
                        <span style={{ fontWeight: 600, color: 'var(--accent)' }}>Open Analysis</span>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" style={{ color: 'var(--accent)' }}><path d="M5 12h14m-7-7 7 7-7 7"/></svg>
                    </div>
                </div>

                {/* Quick Actions */}
                <div className="flex gap-3" style={{ marginBottom: '1.5rem' }}>
                    <button className="btn-success" onClick={async () => {
                        try {
                            const res = await api.post('/alerts/generate');
                            toast.success(res.data.message);
                        } catch (e) { toast.error('Failed to generate alerts'); }
                    }}>⚡ Generate Alerts</button>
                </div>
            </div>

            {/* Add Remark Modal */}
            {showRemark && (
                <div className="modal-overlay" onClick={() => setShowRemark(null)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <h2>Add Remark</h2>
                        <div className="form-group">
                            <label>Remark Message</label>
                            <textarea placeholder="Write your remark..." value={remarkText}
                                onChange={(e) => setRemarkText(e.target.value)} />
                        </div>
                        <div className="flex gap-2">
                            <button onClick={() => handleAddRemark(showRemark)} disabled={!remarkText.trim()}>
                                Submit Remark
                            </button>
                            <button className="btn-secondary" onClick={() => setShowRemark(null)}>Cancel</button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

export default MentorDashboard;
