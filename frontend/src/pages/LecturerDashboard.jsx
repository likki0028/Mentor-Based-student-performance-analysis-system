
import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import Navbar from '../components/Navbar';
import toast, { Toaster } from 'react-hot-toast';

const LecturerDashboard = () => {
    const { user } = useAuth();
    const [students, setStudents] = useState([]);
    const [subjects, setSubjects] = useState([]);
    const [assignments, setAssignments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(null); // 'attendance' | 'marks' | 'assignment' | null

    // Form state
    const [attendanceForm, setAttendanceForm] = useState({
        subject_id: '', date: new Date().toISOString().split('T')[0], records: []
    });
    const [marksForm, setMarksForm] = useState({
        subject_id: '', assessment_type: 'internal', records: []
    });
    const [assignmentForm, setAssignmentForm] = useState({
        title: '', description: '', due_date: '', subject_id: ''
    });

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const [studentsRes, assignmentsRes] = await Promise.all([
                    api.get('/faculty/my-students'),
                    api.get('/assignments/')
                ]);
                setStudents(studentsRes.data);
                setAssignments(assignmentsRes.data);

                // Extract unique subjects from attendance report (or use another endpoint)
                try {
                    const reportRes = await api.get('/attendance/report');
                    const subjectSet = new Map();
                    reportRes.data.forEach(r => {
                        if (!subjectSet.has(r.subject_name)) {
                            subjectSet.set(r.subject_name, r.subject_name);
                        }
                    });
                } catch (e) { }
            } catch (err) {
                toast.error('Failed to load data');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const handleMarkAttendance = async () => {
        try {
            const records = attendanceForm.records.map(r => ({
                student_id: r.student_id,
                subject_id: parseInt(attendanceForm.subject_id),
                date: attendanceForm.date,
                status: r.status
            }));
            await api.post('/attendance/mark', { records });
            toast.success(`Attendance marked for ${records.length} students`);
            setShowModal(null);
        } catch (err) {
            toast.error('Failed to mark attendance');
        }
    };

    const handleAddMarks = async () => {
        try {
            const marks = marksForm.records
                .filter(r => r.score !== undefined && r.score !== '')
                .map(r => ({
                    student_id: r.student_id,
                    subject_id: parseInt(marksForm.subject_id),
                    assessment_type: marksForm.assessment_type,
                    score: parseInt(r.score),
                    total: 100
                }));
            await api.post('/marks/', { marks });
            toast.success(`Marks added for ${marks.length} students`);
            setShowModal(null);
        } catch (err) {
            toast.error('Failed to add marks');
        }
    };

    const handleCreateAssignment = async () => {
        try {
            await api.post('/assignments/', assignmentForm);
            toast.success('Assignment created!');
            setShowModal(null);
            setAssignmentForm({ title: '', description: '', due_date: '', subject_id: '' });
            // Refresh
            const res = await api.get('/assignments/');
            setAssignments(res.data);
        } catch (err) {
            toast.error('Failed to create assignment');
        }
    };

    const openAttendanceModal = () => {
        setAttendanceForm({
            subject_id: '1',
            date: new Date().toISOString().split('T')[0],
            records: students.map(s => ({ student_id: s.id, name: s.name, status: true }))
        });
        setShowModal('attendance');
    };

    const openMarksModal = () => {
        setMarksForm({
            subject_id: '1',
            assessment_type: 'internal',
            records: students.map(s => ({ student_id: s.id, name: s.name, score: '' }))
        });
        setShowModal('marks');
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
                    <h1>Lecturer Dashboard</h1>
                    <p className="text-muted">Manage classes, attendance, marks, and assignments.</p>
                </div>

                {/* Stats */}
                <div className="grid grid-3" style={{ marginBottom: '2rem' }}>
                    <div className="stat-card">
                        <p className="label">My Students</p>
                        <p style={{ fontSize: '2.25rem', fontWeight: 800, color: 'var(--primary)' }}>{students.length}</p>
                    </div>
                    <div className="stat-card accent">
                        <p className="label">Assignments</p>
                        <p style={{ fontSize: '2.25rem', fontWeight: 800, color: '#f59e0b' }}>{assignments.length}</p>
                    </div>
                    <div className="stat-card success">
                        <p className="label">Subject Areas</p>
                        <p style={{ fontSize: '2.25rem', fontWeight: 800, color: '#22c55e' }}>6</p>
                    </div>
                </div>

                {/* Quick Actions */}
                <div className="flex gap-3" style={{ marginBottom: '2rem' }}>
                    <button onClick={openAttendanceModal}>📋 Mark Attendance</button>
                    <button className="btn-accent" onClick={openMarksModal}>📊 Add Marks</button>
                    <button className="btn-success" onClick={() => setShowModal('assignment')}>📝 Create Assignment</button>
                </div>

                {/* Two column layout */}
                <div className="grid grid-2">
                    {/* Student List */}
                    <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                        <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--border)' }}>
                            <h2 style={{ margin: 0, border: 'none', paddingBottom: 0 }}>Student Roster</h2>
                        </div>
                        <table>
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Enrollment</th>
                                    <th>Sem</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {students.slice(0, 15).map(s => {
                                    const badge = s.risk_status === 'Safe' ? 'badge-safe'
                                        : s.risk_status === 'At Risk' ? 'badge-danger' : 'badge-warning';
                                    return (
                                        <tr key={s.id}>
                                            <td style={{ fontWeight: 600 }}>{s.name}</td>
                                            <td className="text-muted">{s.enrollment_number}</td>
                                            <td>{s.current_semester}</td>
                                            <td><span className={`badge ${badge}`}>{s.risk_status}</span></td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                        {students.length > 15 && (
                            <div style={{ padding: '0.75rem', textAlign: 'center' }} className="text-sm text-muted">
                                Showing 15 of {students.length} students
                            </div>
                        )}
                    </div>

                    {/* Assignments */}
                    <div className="card">
                        <h2>Active Assignments</h2>
                        {assignments.length === 0 ? (
                            <p className="text-muted text-sm">No assignments yet.</p>
                        ) : (
                            <div className="flex flex-col gap-3">
                                {assignments.slice(0, 8).map((a, i) => (
                                    <div key={i} style={{
                                        padding: '1rem',
                                        borderRadius: 'var(--radius-sm)',
                                        border: '1px solid var(--border)',
                                        background: 'var(--surface-hover)'
                                    }}>
                                        <div className="flex justify-between items-start">
                                            <div>
                                                <p style={{ fontWeight: 600 }}>{a.title}</p>
                                                <p className="text-xs text-muted">{a.description}</p>
                                            </div>
                                            <span className="badge badge-primary">{a.due_date}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Attendance Modal */}
            {showModal === 'attendance' && (
                <div className="modal-overlay" onClick={() => setShowModal(null)}>
                    <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 600, maxHeight: '80vh', overflow: 'auto' }}>
                        <h2>Mark Attendance</h2>
                        <div className="flex gap-3" style={{ marginBottom: '1rem' }}>
                            <div className="form-group" style={{ flex: 1 }}>
                                <label>Subject ID</label>
                                <input type="number" value={attendanceForm.subject_id}
                                    onChange={(e) => setAttendanceForm({ ...attendanceForm, subject_id: e.target.value })} />
                            </div>
                            <div className="form-group" style={{ flex: 1 }}>
                                <label>Date</label>
                                <input type="date" value={attendanceForm.date}
                                    onChange={(e) => setAttendanceForm({ ...attendanceForm, date: e.target.value })} />
                            </div>
                        </div>
                        <div style={{ maxHeight: 300, overflow: 'auto' }}>
                            {attendanceForm.records.map((r, i) => (
                                <div key={i} className="flex justify-between items-center"
                                    style={{ padding: '0.5rem 0', borderBottom: '1px solid var(--border)' }}>
                                    <span className="text-sm">{r.name}</span>
                                    <label className="flex items-center gap-2" style={{ cursor: 'pointer' }}>
                                        <input type="checkbox" checked={r.status}
                                            style={{ width: 'auto' }}
                                            onChange={(e) => {
                                                const updated = [...attendanceForm.records];
                                                updated[i].status = e.target.checked;
                                                setAttendanceForm({ ...attendanceForm, records: updated });
                                            }} />
                                        <span className="text-sm">{r.status ? 'Present' : 'Absent'}</span>
                                    </label>
                                </div>
                            ))}
                        </div>
                        <div className="flex gap-2" style={{ marginTop: '1.5rem' }}>
                            <button onClick={handleMarkAttendance}>Submit Attendance</button>
                            <button className="btn-secondary" onClick={() => setShowModal(null)}>Cancel</button>
                        </div>
                    </div>
                </div>
            )}

            {/* Marks Modal */}
            {showModal === 'marks' && (
                <div className="modal-overlay" onClick={() => setShowModal(null)}>
                    <div className="modal" onClick={e => e.stopPropagation()} style={{ maxWidth: 600, maxHeight: '80vh', overflow: 'auto' }}>
                        <h2>Add Marks</h2>
                        <div className="flex gap-3" style={{ marginBottom: '1rem' }}>
                            <div className="form-group" style={{ flex: 1 }}>
                                <label>Subject ID</label>
                                <input type="number" value={marksForm.subject_id}
                                    onChange={(e) => setMarksForm({ ...marksForm, subject_id: e.target.value })} />
                            </div>
                            <div className="form-group" style={{ flex: 1 }}>
                                <label>Assessment Type</label>
                                <select value={marksForm.assessment_type}
                                    onChange={(e) => setMarksForm({ ...marksForm, assessment_type: e.target.value })}>
                                    <option value="internal">Internal</option>
                                    <option value="mid_term">Mid-Term</option>
                                    <option value="end_term">End-Term</option>
                                </select>
                            </div>
                        </div>
                        <div style={{ maxHeight: 300, overflow: 'auto' }}>
                            {marksForm.records.map((r, i) => (
                                <div key={i} className="flex justify-between items-center"
                                    style={{ padding: '0.5rem 0', borderBottom: '1px solid var(--border)' }}>
                                    <span className="text-sm" style={{ minWidth: 120 }}>{r.name}</span>
                                    <input type="number" placeholder="Score" min="0" max="100"
                                        style={{ width: 100 }}
                                        value={r.score}
                                        onChange={(e) => {
                                            const updated = [...marksForm.records];
                                            updated[i].score = e.target.value;
                                            setMarksForm({ ...marksForm, records: updated });
                                        }} />
                                </div>
                            ))}
                        </div>
                        <div className="flex gap-2" style={{ marginTop: '1.5rem' }}>
                            <button onClick={handleAddMarks}>Submit Marks</button>
                            <button className="btn-secondary" onClick={() => setShowModal(null)}>Cancel</button>
                        </div>
                    </div>
                </div>
            )}

            {/* Assignment Modal */}
            {showModal === 'assignment' && (
                <div className="modal-overlay" onClick={() => setShowModal(null)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <h2>Create Assignment</h2>
                        <div className="form-group">
                            <label>Title</label>
                            <input type="text" placeholder="Assignment title" value={assignmentForm.title}
                                onChange={(e) => setAssignmentForm({ ...assignmentForm, title: e.target.value })} />
                        </div>
                        <div className="form-group">
                            <label>Description</label>
                            <textarea placeholder="Describe the assignment..." value={assignmentForm.description}
                                onChange={(e) => setAssignmentForm({ ...assignmentForm, description: e.target.value })} />
                        </div>
                        <div className="flex gap-3">
                            <div className="form-group" style={{ flex: 1 }}>
                                <label>Due Date</label>
                                <input type="date" value={assignmentForm.due_date}
                                    onChange={(e) => setAssignmentForm({ ...assignmentForm, due_date: e.target.value })} />
                            </div>
                            <div className="form-group" style={{ flex: 1 }}>
                                <label>Subject ID</label>
                                <input type="number" placeholder="e.g., 1" value={assignmentForm.subject_id}
                                    onChange={(e) => setAssignmentForm({ ...assignmentForm, subject_id: e.target.value })} />
                            </div>
                        </div>
                        <div className="flex gap-2" style={{ marginTop: '1rem' }}>
                            <button onClick={handleCreateAssignment}
                                disabled={!assignmentForm.title || !assignmentForm.due_date || !assignmentForm.subject_id}>
                                Create
                            </button>
                            <button className="btn-secondary" onClick={() => setShowModal(null)}>Cancel</button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

export default LecturerDashboard;
