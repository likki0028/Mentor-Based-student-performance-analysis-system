
import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import Navbar from '../components/Navbar';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import toast, { Toaster } from 'react-hot-toast';

const COLORS = ['#6366f1', '#f59e0b', '#22c55e', '#ef4444', '#8b5cf6', '#06b6d4'];

const StudentDetail = () => {
    const { user } = useAuth();
    const [searchParams] = useSearchParams();
    const studentId = searchParams.get('id');
    const [analytics, setAnalytics] = useState(null);
    const [remarks, setRemarks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [remarkText, setRemarkText] = useState('');
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                let sid = studentId;

                if (!sid) {
                    // If no ID provided, fetch current student's profile
                    const profileRes = await api.get('/students/me');
                    sid = profileRes.data.id;
                }

                const [analyticsRes, remarksRes] = await Promise.all([
                    api.get(`/analytics/student/${sid}`),
                    api.get(`/faculty/remarks/${sid}`).catch(() => ({ data: [] }))
                ]);

                setAnalytics(analyticsRes.data);
                setRemarks(remarksRes.data);
            } catch (err) {
                console.error('Failed to fetch student data:', err);
                toast.error('Failed to load student details');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [studentId]);

    const handleAddRemark = async () => {
        if (!remarkText.trim() || !analytics) return;
        setSubmitting(true);
        try {
            await api.post('/faculty/remarks', {
                student_id: analytics.student_id,
                message: remarkText
            });
            toast.success('Remark added successfully');
            setRemarkText('');
            // Refresh remarks
            const res = await api.get(`/faculty/remarks/${analytics.student_id}`);
            setRemarks(res.data);
        } catch (err) {
            toast.error('Failed to add remark');
        } finally {
            setSubmitting(false);
        }
    };

    if (loading) {
        return (
            <>
                <Navbar />
                <Toaster position="top-right" />
                <div className="container page-enter">
                    <div className="grid grid-3" style={{ marginTop: '2rem' }}>
                        {[1, 2, 3].map(i => <div key={i} className="skeleton skeleton-card"></div>)}
                    </div>
                    <div className="grid grid-2" style={{ marginTop: '1.5rem' }}>
                        {[1, 2].map(i => <div key={i} className="skeleton" style={{ height: 250 }}></div>)}
                    </div>
                </div>
            </>
        );
    }

    if (!analytics) {
        return (
            <>
                <Navbar />
                <div className="container">
                    <div className="card empty-state">
                        <div className="emoji">😕</div>
                        <p>Student data not found.</p>
                        <Link to="/"><button style={{ marginTop: '1rem' }}>Go Back</button></Link>
                    </div>
                </div>
            </>
        );
    }

    const riskBadge = analytics.risk_status === 'Safe' ? 'badge-safe'
        : analytics.risk_status === 'Warning' ? 'badge-warning' : 'badge-danger';

    // Prepare chart data
    const subjectChartData = analytics.subject_stats.map(s => ({
        name: s.subject_code || s.subject_name.substring(0, 8),
        attendance: s.attendance_percentage,
        marks: s.average_marks
    }));

    const pieData = [
        { name: 'Present', value: analytics.classes_attended },
        { name: 'Absent', value: analytics.total_classes - analytics.classes_attended }
    ];

    const isFacultyOrAdmin = user?.role !== 'student';

    return (
        <>
            <Navbar />
            <Toaster position="top-right" />
            <div className="container page-enter">
                {/* Header */}
                <div className="flex justify-between items-end" style={{ marginBottom: '2rem' }}>
                    <div>
                        <div className="flex items-center gap-3">
                            <h1 style={{ marginBottom: '0.25rem' }}>{analytics.name}</h1>
                            <span className={`badge ${riskBadge}`}>{analytics.risk_status}</span>
                        </div>
                        <p className="text-muted">
                            {analytics.enrollment_number} &nbsp;•&nbsp; Semester {analytics.current_semester}
                        </p>
                    </div>
                    <Link to={user?.role === 'student' ? '/student' : '/mentor'}>
                        <button className="btn-secondary">← Back to Dashboard</button>
                    </Link>
                </div>

                {/* Stats Row */}
                <div className="grid grid-4" style={{ marginBottom: '2rem' }}>
                    <div className="stat-card">
                        <p className="label">Attendance</p>
                        <p style={{ fontSize: '2rem', fontWeight: 800, color: analytics.attendance_percentage >= 75 ? '#22c55e' : '#ef4444' }}>
                            {analytics.attendance_percentage}%
                        </p>
                        <div className="progress-bar" style={{ marginTop: '0.5rem' }}>
                            <div className={`progress-fill ${analytics.attendance_percentage >= 75 ? 'success' : 'danger'}`}
                                style={{ width: `${Math.min(analytics.attendance_percentage, 100)}%` }}></div>
                        </div>
                    </div>
                    <div className="stat-card accent">
                        <p className="label">Avg Score</p>
                        <p style={{ fontSize: '2rem', fontWeight: 800, color: '#f59e0b' }}>
                            {analytics.average_marks}%
                        </p>
                        <p className="text-xs text-muted">{analytics.total_assessments} assessments</p>
                    </div>
                    <div className="stat-card success">
                        <p className="label">Classes Attended</p>
                        <p style={{ fontSize: '2rem', fontWeight: 800, color: '#6366f1' }}>
                            {analytics.classes_attended}/{analytics.total_classes}
                        </p>
                    </div>
                    <div className="stat-card danger">
                        <p className="label">Active Alerts</p>
                        <p style={{ fontSize: '2rem', fontWeight: 800, color: '#ef4444' }}>
                            {analytics.recent_alerts.filter(a => !a.is_read).length}
                        </p>
                    </div>
                </div>

                {/* Charts Row */}
                <div className="grid grid-2" style={{ marginBottom: '2rem' }}>
                    <div className="card">
                        <h2>Subject-wise Performance</h2>
                        <ResponsiveContainer width="100%" height={280}>
                            <BarChart data={subjectChartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                                <XAxis dataKey="name" fontSize={12} />
                                <YAxis fontSize={12} />
                                <Tooltip
                                    contentStyle={{ borderRadius: 8, border: '1px solid #e2e8f0' }}
                                />
                                <Bar dataKey="marks" fill="#6366f1" radius={[4, 4, 0, 0]} name="Avg Marks" />
                                <Bar dataKey="attendance" fill="#22c55e" radius={[4, 4, 0, 0]} name="Attendance %" />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>

                    <div className="card">
                        <h2>Attendance Overview</h2>
                        <ResponsiveContainer width="100%" height={280}>
                            <PieChart>
                                <Pie data={pieData} cx="50%" cy="50%" innerRadius={70} outerRadius={100}
                                    paddingAngle={5} dataKey="value" label={({ name, value }) => `${name}: ${value}`}>
                                    {pieData.map((_, i) => (
                                        <Cell key={i} fill={i === 0 ? '#22c55e' : '#ef4444'} />
                                    ))}
                                </Pie>
                                <Tooltip />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Subject Details Table */}
                <div className="card" style={{ marginBottom: '2rem', padding: 0, overflow: 'hidden' }}>
                    <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--border)' }}>
                        <h2 style={{ margin: 0, border: 'none', paddingBottom: 0 }}>Subject-wise Breakdown</h2>
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th>Subject</th>
                                <th>Attendance</th>
                                <th>Avg Marks</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {analytics.subject_stats.map((sub, i) => {
                                const status = sub.attendance_percentage < 75 || sub.average_marks < 40
                                    ? 'At Risk' : sub.attendance_percentage < 85 || sub.average_marks < 60
                                        ? 'Warning' : 'Safe';
                                const badge = status === 'Safe' ? 'badge-safe' : status === 'Warning' ? 'badge-warning' : 'badge-danger';
                                return (
                                    <tr key={i}>
                                        <td>
                                            <div style={{ fontWeight: 600 }}>{sub.subject_name}</div>
                                            <div className="text-xs text-muted">{sub.subject_code}</div>
                                        </td>
                                        <td>
                                            <div className="flex items-center gap-2">
                                                <span style={{ fontWeight: 600 }}>{sub.attendance_percentage}%</span>
                                                <span className="text-xs text-muted">({sub.classes_attended}/{sub.total_classes})</span>
                                            </div>
                                        </td>
                                        <td style={{ fontWeight: 600 }}>{sub.average_marks}%</td>
                                        <td><span className={`badge ${badge}`}>{status}</span></td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>

                {/* Alerts & Remarks */}
                <div className="grid grid-2">
                    {/* Alerts */}
                    <div className="card">
                        <h2>Recent Alerts</h2>
                        {analytics.recent_alerts.length === 0 ? (
                            <p className="text-muted text-sm">No alerts — great job! 🎉</p>
                        ) : (
                            <div className="flex flex-col gap-2">
                                {analytics.recent_alerts.map((alert, i) => (
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
                        )}
                    </div>

                    {/* Remarks */}
                    <div className="card">
                        <h2>Mentor Remarks</h2>
                        {isFacultyOrAdmin && (
                            <div style={{ marginBottom: '1rem' }}>
                                <textarea
                                    placeholder="Add a remark about this student..."
                                    value={remarkText}
                                    onChange={(e) => setRemarkText(e.target.value)}
                                    style={{ marginBottom: '0.5rem' }}
                                />
                                <button onClick={handleAddRemark} disabled={submitting || !remarkText.trim()}>
                                    {submitting ? 'Adding...' : 'Add Remark'}
                                </button>
                            </div>
                        )}
                        {remarks.length === 0 ? (
                            <p className="text-muted text-sm">No remarks yet.</p>
                        ) : (
                            <div className="flex flex-col gap-2">
                                {remarks.map((r, i) => (
                                    <div key={i} style={{
                                        padding: '0.75rem',
                                        borderRadius: 'var(--radius-sm)',
                                        background: 'var(--primary-light)',
                                        borderLeft: '3px solid var(--primary)'
                                    }}>
                                        <p className="text-sm">{r.message}</p>
                                        <p className="text-xs text-muted" style={{ marginTop: '0.25rem' }}>
                                            {new Date(r.created_at).toLocaleDateString()}
                                        </p>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </>
    );
};

export default StudentDetail;
