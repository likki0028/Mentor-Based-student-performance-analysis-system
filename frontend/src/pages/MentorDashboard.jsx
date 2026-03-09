
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import Navbar from '../components/Navbar';
import toast, { Toaster } from 'react-hot-toast';

const MentorDashboard = () => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [stats, setStats] = useState(null);
    const [students, setStudents] = useState([]);
    const [search, setSearch] = useState('');
    const [loading, setLoading] = useState(true);
    const [showRemark, setShowRemark] = useState(null);
    const [remarkText, setRemarkText] = useState('');

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const [dashRes, studentsRes] = await Promise.all([
                    api.get('/faculty/dashboard'),
                    api.get('/faculty/my-students')
                ]);
                setStats(dashRes.data);
                setStudents(studentsRes.data);
            } catch (err) {
                toast.error('Failed to load mentor data');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const filteredStudents = students.filter(s =>
        s.name.toLowerCase().includes(search.toLowerCase()) ||
        s.enrollment_number.toLowerCase().includes(search.toLowerCase())
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

    if (loading) {
        return (
            <>
                <Navbar />
                <Toaster position="top-right" />
                <div className="container page-enter">
                    <div className="grid grid-3" style={{ marginTop: '2rem' }}>
                        {[1, 2, 3].map(i => <div key={i} className="skeleton skeleton-card"></div>)}
                    </div>
                    <div className="skeleton" style={{ height: 300, marginTop: '1.5rem' }}></div>
                </div>
            </>
        );
    }

    return (
        <>
            <Navbar />
            <Toaster position="top-right" />
            <div className="container page-enter">
                <div style={{ marginBottom: '2rem' }}>
                    <h1>Mentor Dashboard</h1>
                    <p className="text-muted">Monitor and guide your assigned students.</p>
                </div>

                {/* Stats Row */}
                {stats && (
                    <div className="grid grid-3" style={{ marginBottom: '2rem' }}>
                        <div className="stat-card">
                            <p className="label">Total Students</p>
                            <p style={{ fontSize: '2.25rem', fontWeight: 800, color: 'var(--primary)' }}>{stats.total_students}</p>
                        </div>
                        <div className="stat-card danger">
                            <p className="label">At Risk</p>
                            <p style={{ fontSize: '2.25rem', fontWeight: 800, color: '#ef4444' }}>{stats.at_risk_count}</p>
                        </div>
                        <div className="stat-card accent">
                            <p className="label">Pending Tasks</p>
                            <p style={{ fontSize: '2.25rem', fontWeight: 800, color: '#f59e0b' }}>{stats.pending_tasks}</p>
                        </div>
                    </div>
                )}

                {/* Alerts */}
                {stats?.recent_alerts?.length > 0 && (
                    <div className="card" style={{ marginBottom: '2rem', borderLeft: '4px solid #f59e0b' }}>
                        <h2 style={{ border: 'none', paddingBottom: 0, marginBottom: '0.75rem' }}>⚠️ Recent Alerts</h2>
                        {stats.recent_alerts.map((alert, i) => (
                            <p key={i} className="text-sm" style={{ padding: '0.35rem 0', color: '#c2410c' }}>• {alert}</p>
                        ))}
                    </div>
                )}

                {/* Quick Actions */}
                <div className="flex gap-3" style={{ marginBottom: '1.5rem' }}>
                    <button className="btn-success" onClick={async () => {
                        try {
                            const res = await api.post('/alerts/generate');
                            toast.success(res.data.message);
                        } catch (e) { toast.error('Failed to generate alerts'); }
                    }}>⚡ Generate Alerts</button>
                </div>

                {/* Mentee Table */}
                <div className="card" style={{ overflow: 'hidden', padding: 0 }}>
                    <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--border)' }}
                        className="flex justify-between items-center">
                        <h2 style={{ margin: 0, border: 'none', paddingBottom: 0 }}>Mentee List</h2>
                        <input type="text" placeholder="Search student..." style={{ width: 250 }}
                            value={search} onChange={(e) => setSearch(e.target.value)} />
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>Enrollment</th>
                                <th>Semester</th>
                                <th>Attendance</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredStudents.map((student, i) => {
                                const badge = student.risk_status === 'Safe' ? 'badge-safe'
                                    : student.risk_status === 'At Risk' ? 'badge-danger' : 'badge-warning';
                                return (
                                    <tr key={i}>
                                        <td style={{ fontWeight: 600 }}>{student.name}</td>
                                        <td className="text-muted">{student.enrollment_number}</td>
                                        <td>{student.current_semester}</td>
                                        <td>
                                            <div className="flex items-center gap-2">
                                                <span style={{ fontWeight: 600 }}>{student.attendance_percentage}%</span>
                                                <div className="progress-bar" style={{ width: 80, height: 6 }}>
                                                    <div className={`progress-fill ${student.attendance_percentage >= 75 ? 'success' : 'danger'}`}
                                                        style={{ width: `${Math.min(student.attendance_percentage, 100)}%` }}></div>
                                                </div>
                                            </div>
                                        </td>
                                        <td><span className={`badge ${badge}`}>{student.risk_status}</span></td>
                                        <td>
                                            <div className="flex gap-2">
                                                <button style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}
                                                    onClick={() => navigate(`/student/detail?id=${student.id}`)}>
                                                    View
                                                </button>
                                                <button className="btn-accent" style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}
                                                    onClick={() => setShowRemark(student.id)}>
                                                    Remark
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })}
                            {filteredStudents.length === 0 && (
                                <tr>
                                    <td colSpan="6" className="text-center text-muted" style={{ padding: '2rem' }}>
                                        No students found.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                    <div style={{ padding: '0.75rem 1.5rem', background: '#f8fafc', textAlign: 'center' }}
                        className="text-sm text-muted">
                        Showing {filteredStudents.length} of {students.length} students
                    </div>
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
