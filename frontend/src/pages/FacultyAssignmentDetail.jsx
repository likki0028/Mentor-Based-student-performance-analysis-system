import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import api from '../services/api';
import toast from 'react-hot-toast';

const FacultyAssignmentDetail = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [assignment, setAssignment] = useState(null);
    const [submissions, setSubmissions] = useState([]);
    const [totalStudents, setTotalStudents] = useState(0);
    const [loading, setLoading] = useState(true);
    const [editMode, setEditMode] = useState(false);
    const [editForm, setEditForm] = useState({ title: '', description: '', due_date: '' });
    const [editSubmitting, setEditSubmitting] = useState(false);
    const [gradingId, setGradingId] = useState(null);
    const [gradeValue, setGradeValue] = useState('');
    const [deleting, setDeleting] = useState(false);
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [asmRes, subRes, filesRes] = await Promise.all([
                api.get(`/assignments/${id}`),
                api.get(`/assignments/${id}/submissions`),
                api.get(`/assignments/${id}/files`)
            ]);
            setAssignment(asmRes.data);
            setSubmissions(subRes.data);
            setAssignmentFiles(filesRes.data);
            setEditForm({
                title: asmRes.data.title || '',
                description: asmRes.data.description || '',
                due_date: asmRes.data.due_date ? asmRes.data.due_date.slice(0, 16) : ''
            });

            if (asmRes.data.section_id) {
                try {
                    const studentsRes = await api.get('/faculty/my-students', {
                        params: { section_id: asmRes.data.section_id }
                    });
                    setTotalStudents(studentsRes.data.length);
                } catch { setTotalStudents(0); }
            }
        } catch (err) {
            console.error('Failed to load assignment:', err);
            toast.error('Failed to load assignment details');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchData(); }, [id]);

    const handleValidate = async (submissionId, isValid) => {
        try {
            await api.post(`/assignments/validate/${submissionId}`, { valid: isValid });
            toast.success(isValid ? 'Marked as Valid ✅' : 'Marked as Invalid ❌');
            fetchData();
        } catch (err) {
            toast.error('Failed to validate submission');
        }
    };

    const handleEdit = async (e) => {
        e.preventDefault();
        setEditSubmitting(true);
        try {
            await api.put(`/assignments/${id}`, editForm);
            toast.success('Assignment updated');
            setEditMode(false);
            fetchData();
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Failed to update');
        } finally {
            setEditSubmitting(false);
        }
    };

    const handleDelete = async () => {
        setDeleting(true);
        try {
            await api.delete(`/assignments/${id}`);
            toast.success('Assignment deleted');
            navigate(-1);
        } catch (err) {
            toast.error('Failed to delete assignment');
            setDeleting(false);
            setShowDeleteConfirm(false);
        }
    };

    // --- File management ---
    const [assignmentFiles, setAssignmentFiles] = useState([]);
    const [fileUploading, setFileUploading] = useState(false);
    const [fileToRemove, setFileToRemove] = useState(null);
    const [fileRemoving, setFileRemoving] = useState(false);

    const handleFileUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        setFileUploading(true);
        try {
            const formData = new FormData();
            formData.append('file', file);
            await api.post(`/assignments/${id}/attach-file`, formData);
            toast.success('File uploaded');
            fetchData();
        } catch (err) {
            toast.error('Failed to upload file');
        } finally {
            setFileUploading(false);
            e.target.value = '';
        }
    };

    const handleFileRemove = async () => {
        if (!fileToRemove) return;
        setFileRemoving(true);
        try {
            await api.delete(`/assignments/${id}/remove-file/${fileToRemove.id}`);
            toast.success('File removed');
            setFileToRemove(null);
            fetchData();
        } catch (err) {
            toast.error('Failed to remove file');
        } finally {
            setFileRemoving(false);
        }
    };

    if (loading) {
        return (
            <>
                <Navbar />
                <div className="container page-enter">
                    <div className="skeleton" style={{ height: 200, borderRadius: 12, marginBottom: '1.5rem' }}></div>
                    <div className="skeleton" style={{ height: 400, borderRadius: 12 }}></div>
                </div>
            </>
        );
    }

    if (!assignment) {
        return (
            <>
                <Navbar />
                <div className="container text-center" style={{ marginTop: '5rem' }}>
                    <h2>Assignment not found</h2>
                    <button className="btn-primary" onClick={() => navigate(-1)}>Go Back</button>
                </div>
            </>
        );
    }

    const dueDate = new Date(assignment.due_date);
    const isPastDue = dueDate < new Date();
    const submittedCount = submissions.length;
    const gradedCount = submissions.filter(s => s.grade !== null && s.grade !== undefined).length;
    const avgGrade = gradedCount > 0
        ? (submissions.filter(s => s.grade !== null).reduce((sum, s) => sum + s.grade, 0) / gradedCount).toFixed(1)
        : '—';
    const onTimeCount = submissions.filter(s => new Date(s.submission_date) <= dueDate).length;

    return (
        <>
            <Navbar />
            <div className="container page-enter" style={{ maxWidth: 1100 }}>
                {/* Breadcrumb */}
                <div className="flex items-center gap-2 text-muted text-sm" style={{ marginBottom: '1.5rem' }}>
                    <Link to="/lecturer" className="hover-link">Dashboard</Link>
                    <span>/</span>
                    <span className="text-main">Assignment Detail</span>
                </div>

                {/* Header Card */}
                <div className="card" style={{
                    padding: '2rem 2.5rem',
                    marginBottom: '1.5rem',
                    background: 'linear-gradient(135deg, #1e293b 0%, #334155 100%)',
                    color: 'white',
                    border: 'none',
                    position: 'relative',
                    overflow: 'hidden'
                }}>
                    <div style={{ position: 'absolute', top: -20, right: -20, fontSize: '8rem', opacity: 0.06, pointerEvents: 'none' }}>📝</div>
                    <div className="flex justify-between items-start">
                        <div style={{ flex: 1 }}>
                            <h1 style={{ color: 'white', fontSize: '1.75rem', marginBottom: '0.5rem' }}>{assignment.title}</h1>
                            <p style={{ opacity: 0.85, fontSize: '0.95rem', lineHeight: 1.6, maxWidth: 600 }}>
                                {assignment.description || 'No description provided.'}
                            </p>
                            <div className="flex items-center gap-4" style={{ marginTop: '1rem' }}>
                                <span style={{
                                    background: isPastDue ? 'rgba(239,68,68,0.2)' : 'rgba(34,197,94,0.2)',
                                    color: isPastDue ? '#fca5a5' : '#86efac',
                                    padding: '0.3rem 0.8rem',
                                    borderRadius: '20px',
                                    fontSize: '0.8rem',
                                    fontWeight: 600
                                }}>
                                    {isPastDue ? '⏰ Past Due' : '📅 Active'}
                                </span>
                                <span style={{ opacity: 0.8, fontSize: '0.85rem' }}>
                                    Due: {dueDate.toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}
                                </span>
                            </div>
                        </div>
                        <div className="flex gap-2">
                            <button
                                className="btn-secondary"
                                style={{ fontSize: '0.8rem', padding: '0.4rem 0.9rem', background: 'rgba(255,255,255,0.15)', color: 'white', border: '1px solid rgba(255,255,255,0.25)' }}
                                onClick={() => setEditMode(true)}
                            >
                                ✏️ Edit
                            </button>
                            <button
                                className="btn-danger"
                                style={{ fontSize: '0.8rem', padding: '0.4rem 0.9rem' }}
                                onClick={() => setShowDeleteConfirm(true)}
                                disabled={deleting}
                            >
                                {deleting ? 'Deleting...' : '🗑️ Delete'}
                            </button>
                        </div>
                    </div>

                    {assignmentFiles.length > 0 && (
                        <div className="flex items-center gap-3" style={{ marginTop: '1rem' }}>
                            <span style={{ opacity: 0.8, fontSize: '0.85rem' }}>📎 {assignmentFiles.length} file{assignmentFiles.length > 1 ? 's' : ''} attached</span>
                        </div>
                    )}
                </div>

                {/* Attached Documents Section */}
                <div className="card" style={{ padding: '1.25rem 1.5rem', marginBottom: '1.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
                        <h3 style={{ margin: 0, fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>📎 Attachments ({assignmentFiles.length})</h3>
                        <label
                            className="btn-primary"
                            style={{ fontSize: '0.8rem', padding: '0.4rem 1rem', cursor: 'pointer', margin: 0, borderRadius: '8px' }}
                        >
                            {fileUploading ? 'Uploading...' : '+ Add File'}
                            <input type="file" accept=".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.png,.jpg,.jpeg,.zip" style={{ display: 'none' }} onChange={handleFileUpload} disabled={fileUploading} />
                        </label>
                    </div>

                    {assignmentFiles.length > 0 ? (
                        <div className="flex flex-col gap-2">
                            {assignmentFiles.map(f => (
                                <div key={f.id} style={{
                                    display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                                    padding: '0.75rem 1rem',
                                    background: 'var(--bg-secondary)',
                                    borderRadius: '10px',
                                    border: '1px solid var(--border)'
                                }}>
                                    <div className="flex items-center gap-3">
                                        <div style={{
                                            width: 38, height: 38,
                                            borderRadius: '8px',
                                            background: 'var(--primary-light)',
                                            color: 'var(--primary)',
                                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                                            fontSize: '1.1rem'
                                        }}>📄</div>
                                        <div>
                                            <p className="font-semibold text-sm" style={{ margin: 0 }}>{f.filename}</p>
                                            <p className="text-xs text-muted" style={{ margin: 0 }}>{f.uploaded_at ? new Date(f.uploaded_at).toLocaleDateString() : ''}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <a
                                            href={`http://localhost:8000${f.file_url}`}
                                            target="_blank"
                                            rel="noreferrer"
                                            className="btn-secondary"
                                            style={{ textDecoration: 'none', fontSize: '0.75rem', padding: '0.3rem 0.7rem' }}
                                        >👁️ View</a>
                                        <a
                                            href={`http://localhost:8000${f.file_url}`}
                                            download={f.filename}
                                            className="btn-secondary"
                                            style={{ textDecoration: 'none', fontSize: '0.75rem', padding: '0.3rem 0.7rem' }}
                                        >📥 Download</a>
                                        <button
                                            className="btn-danger"
                                            style={{ fontSize: '0.75rem', padding: '0.3rem 0.7rem' }}
                                            onClick={() => setFileToRemove(f)}
                                        >🗑️</button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <label style={{
                            display: 'flex',
                            flexDirection: 'column',
                            alignItems: 'center',
                            justifyContent: 'center',
                            padding: '2rem 1rem',
                            border: '2px dashed var(--border)',
                            borderRadius: '12px',
                            cursor: 'pointer',
                            background: 'var(--bg-secondary)',
                        }}>
                            <div style={{ fontSize: '2rem', marginBottom: '0.5rem', opacity: 0.4 }}>📁</div>
                            <p className="text-muted" style={{ margin: 0, fontWeight: 600 }}>Click to upload a file</p>
                            <p className="text-xs text-muted" style={{ margin: '0.25rem 0 0' }}>PDF, DOC, PPT, Images, ZIP and more</p>
                            <input type="file" accept=".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.png,.jpg,.jpeg,.zip" style={{ display: 'none' }} onChange={handleFileUpload} disabled={fileUploading} />
                        </label>
                    )}
                </div>

                {/* Stats Row */}
                <div className="grid grid-4" style={{ gap: '1rem', marginBottom: '1.5rem' }}>
                    {[
                        { label: 'Submissions', value: `${submittedCount}${totalStudents ? ` / ${totalStudents}` : ''}`, icon: '📤', color: 'var(--primary)' },
                        { label: 'Graded', value: `${gradedCount} / ${submittedCount}`, icon: '✅', color: 'var(--success)' },
                        { label: 'Avg Grade', value: avgGrade, icon: '📊', color: '#f59e0b' },
                        { label: 'On Time', value: `${onTimeCount} / ${submittedCount}`, icon: '⏱️', color: '#8b5cf6' }
                    ].map((stat, i) => (
                        <div key={i} className="card" style={{ padding: '1.25rem', textAlign: 'center' }}>
                            <div style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>{stat.icon}</div>
                            <div style={{ fontSize: '1.5rem', fontWeight: 800, color: stat.color }}>{stat.value}</div>
                            <div className="text-xs text-muted" style={{ marginTop: '0.25rem' }}>{stat.label}</div>
                        </div>
                    ))}
                </div>

                {/* Submissions Table */}
                <div className="card" style={{ padding: '1.5rem' }}>
                    <h2 style={{ marginTop: 0, marginBottom: '1.25rem', fontSize: '1.2rem' }}>📋 Submissions</h2>

                    {submissions.length === 0 ? (
                        <div className="text-center" style={{ padding: '3rem 1rem' }}>
                            <div style={{ fontSize: '3rem', marginBottom: '0.5rem', opacity: 0.3 }}>📬</div>
                            <p className="text-muted">No submissions yet.</p>
                        </div>
                    ) : (
                        <div style={{ overflowX: 'auto' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                <thead>
                                    <tr style={{ borderBottom: '2px solid var(--border)', textAlign: 'left' }}>
                                        <th style={{ padding: '0.75rem 1rem', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Student</th>
                                        <th style={{ padding: '0.75rem 1rem', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Enrollment</th>
                                        <th style={{ padding: '0.75rem 1rem', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Submitted</th>
                                        <th style={{ padding: '0.75rem 1rem', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Status</th>
                                        <th style={{ padding: '0.75rem 1rem', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>File</th>
                                        <th style={{ padding: '0.75rem 1rem', fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Validation</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {submissions.map(sub => {
                                        const isLate = new Date(sub.submission_date) > dueDate;
                                        return (
                                            <tr key={sub.id} style={{ borderBottom: '1px solid var(--border)' }}>
                                                <td style={{ padding: '0.85rem 1rem' }}>
                                                    <div className="flex items-center gap-3">
                                                        <div style={{
                                                            width: 34, height: 34, borderRadius: '50%',
                                                            background: 'var(--primary-light)', color: 'var(--primary)',
                                                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                            fontWeight: 700, fontSize: '0.8rem'
                                                        }}>
                                                            {(sub.student_name || '?').charAt(0).toUpperCase()}
                                                        </div>
                                                        <span className="font-semibold text-sm">{sub.student_name}</span>
                                                    </div>
                                                </td>
                                                <td style={{ padding: '0.85rem 1rem' }}>
                                                    <span className="text-sm text-muted">{sub.enrollment_number}</span>
                                                </td>
                                                <td style={{ padding: '0.85rem 1rem' }}>
                                                    <span className="text-sm">{new Date(sub.submission_date).toLocaleDateString()}</span>
                                                </td>
                                                <td style={{ padding: '0.85rem 1rem' }}>
                                                    <span className={`badge ${isLate ? 'badge-danger' : 'badge-safe'}`} style={{ fontSize: '0.7rem' }}>
                                                        {isLate ? 'Late' : 'On Time'}
                                                    </span>
                                                </td>
                                                <td style={{ padding: '0.85rem 1rem' }}>
                                                    {sub.file_url ? (
                                                        <a
                                                            href={`http://localhost:8000/${sub.file_url}`}
                                                            target="_blank"
                                                            rel="noreferrer"
                                                            style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--primary)' }}
                                                        >
                                                            📄 View
                                                        </a>
                                                    ) : (
                                                        <span className="text-xs text-muted">No file</span>
                                                    )}
                                                </td>
                                                <td style={{ padding: '0.85rem 1rem' }}>
                                                    {sub.validation_status === 'valid' ? (
                                                        <span className="badge badge-safe" style={{ fontSize: '0.75rem', fontWeight: 700 }}>✅ Valid</span>
                                                    ) : sub.validation_status === 'invalid' ? (
                                                        <span className="badge badge-danger" style={{ fontSize: '0.75rem', fontWeight: 700 }}>❌ Invalid</span>
                                                    ) : (
                                                        <div className="flex items-center gap-2">
                                                            <button
                                                                onClick={() => handleValidate(sub.id, true)}
                                                                style={{
                                                                    padding: '0.3rem 0.7rem', fontSize: '0.75rem', fontWeight: 700,
                                                                    background: '#22c55e', color: 'white', border: 'none',
                                                                    borderRadius: '6px', cursor: 'pointer'
                                                                }}
                                                            >✅ Valid</button>
                                                            <button
                                                                onClick={() => handleValidate(sub.id, false)}
                                                                style={{
                                                                    padding: '0.3rem 0.7rem', fontSize: '0.75rem', fontWeight: 700,
                                                                    background: '#ef4444', color: 'white', border: 'none',
                                                                    borderRadius: '6px', cursor: 'pointer'
                                                                }}
                                                            >❌ Invalid</button>
                                                        </div>
                                                    )}
                                                </td>
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>

            {/* Edit Modal */}
            {editMode && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.5)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    zIndex: 1000
                }}>
                    <div className="card" style={{ width: '100%', maxWidth: 500, padding: '2rem' }}>
                        <h2 style={{ marginTop: 0 }}>Edit Assignment</h2>
                        <form onSubmit={handleEdit} className="flex flex-col gap-4">
                            <div>
                                <label className="block text-sm font-semibold mb-1">Title</label>
                                <input className="w-full" type="text" required value={editForm.title}
                                    onChange={e => setEditForm({ ...editForm, title: e.target.value })} />
                            </div>
                            <div>
                                <label className="block text-sm font-semibold mb-1">Description</label>
                                <textarea className="w-full" rows="3" value={editForm.description}
                                    onChange={e => setEditForm({ ...editForm, description: e.target.value })}></textarea>
                            </div>
                            <div>
                                <label className="block text-sm font-semibold mb-1">Due Date & Time</label>
                                <input className="w-full" type="datetime-local" required value={editForm.due_date}
                                    onChange={e => setEditForm({ ...editForm, due_date: e.target.value })} />
                            </div>
                            <div className="flex justify-end gap-3 mt-4">
                                <button type="button" className="btn-secondary" onClick={() => setEditMode(false)}>Cancel</button>
                                <button type="submit" className="btn-primary" disabled={editSubmitting}>
                                    {editSubmitting ? 'Saving...' : 'Save Changes'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Delete Confirmation Modal */}
            {showDeleteConfirm && (
                <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
                    <div className="card" style={{ width: '100%', maxWidth: '420px', padding: '2rem', textAlign: 'center' }}>
                        <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>🗑️</div>
                        <h2 style={{ marginTop: 0, marginBottom: '0.5rem' }}>Delete Assignment?</h2>
                        <p className="text-muted" style={{ marginBottom: '1.5rem' }}>
                            Are you sure you want to delete <strong>"{assignment?.title}"</strong>? All student submissions will also be deleted. This cannot be undone.
                        </p>
                        <div className="flex justify-center gap-3">
                            <button className="btn-secondary" onClick={() => setShowDeleteConfirm(false)} disabled={deleting}>Cancel</button>
                            <button className="btn-danger" onClick={handleDelete} disabled={deleting}>
                                {deleting ? 'Deleting...' : 'Delete'}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Remove File Confirmation Modal */}
            {fileToRemove && (
                <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}>
                    <div className="card" style={{ width: '100%', maxWidth: '420px', padding: '2rem', textAlign: 'center' }}>
                        <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>📄</div>
                        <h2 style={{ marginTop: 0, marginBottom: '0.5rem' }}>Remove File?</h2>
                        <p className="text-muted" style={{ marginBottom: '1.5rem' }}>
                            Are you sure you want to remove <strong>"{fileToRemove.filename}"</strong>? This cannot be undone.
                        </p>
                        <div className="flex justify-center gap-3">
                            <button className="btn-secondary" onClick={() => setFileToRemove(null)} disabled={fileRemoving}>Cancel</button>
                            <button className="btn-danger" onClick={handleFileRemove} disabled={fileRemoving}>
                                {fileRemoving ? 'Removing...' : 'Remove'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

export default FacultyAssignmentDetail;
