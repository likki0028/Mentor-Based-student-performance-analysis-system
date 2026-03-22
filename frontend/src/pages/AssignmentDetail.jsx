import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import api, { API_BASE_URL } from '../services/api';
import toast from 'react-hot-toast';

const AssignmentDetail = () => {
    const { id } = useParams();
    const [assignment, setAssignment] = useState(null);
    const [status, setStatus] = useState(null);
    const [loading, setLoading] = useState(true);
    const [uploading, setUploading] = useState(false);
    const [file, setFile] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const [asmRes, statusRes] = await Promise.all([
                    api.get(`/assignments/${id}`),
                    api.get(`/assignments/${id}/status`)
                ]);
                setAssignment(asmRes.data);
                setStatus(statusRes.data);
            } catch (err) {
                console.error('Failed to fetch assignment:', err);
                toast.error('Failed to load assignment details');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [id]);

    const handleFileChange = (e) => {
        if (e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!file) {
            toast.error('Please select a file first');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            setUploading(true);
            const res = await api.post(`/assignments/upload/${id}`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            toast.success('Assignment submitted successfully!');
            setStatus({ status: 'submitted', submission: res.data });
        } catch (err) {
            console.error('Upload failed:', err);
            toast.error(err.response?.data?.detail || 'Upload failed');
        } finally {
            setUploading(false);
        }
    };

    if (loading) {
        return (
            <>
                <Navbar />
                <div className="container page-enter">
                    <div className="skeleton" style={{ height: 400, borderRadius: 8 }}></div>
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
                    <Link to="/student"><button className="btn-primary">Back to Dashboard</button></Link>
                </div>
            </>
        );
    }

    const dueDate = new Date(assignment.due_date);
    const isPastDue = dueDate < new Date() && status?.status !== 'submitted';
    const isSubmitted = status?.status === 'submitted';

    return (
        <>
            <Navbar />
            <div className="container page-enter" style={{ maxWidth: 1000 }}>
                <div className="flex items-center gap-2 text-muted text-sm" style={{ marginBottom: '1.5rem' }}>
                    <Link to="/student" className="hover-link">Dashboard</Link>
                    <span>/</span>
                    <Link to={`/student/subject/${assignment.subject_id}`} className="hover-link">Classroom</Link>
                    <span>/</span>
                    <span className="text-main">Assignment</span>
                </div>

                <div className="grid" style={{ gridTemplateColumns: '1fr 300px', gap: '1.5rem', alignItems: 'start' }}>
                    {/* Left: Content */}
                    <div className="card" style={{ padding: '2.5rem' }}>
                        <div className="flex items-center gap-4" style={{ marginBottom: '2rem' }}>
                            <div style={{ 
                                width: 50, height: 50, borderRadius: '50%', 
                                background: 'var(--primary)', color: 'white', 
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                fontSize: '1.5rem'
                            }}>📝</div>
                            <div>
                                <h1 style={{ fontSize: '2rem', marginBottom: '0.25rem' }}>{assignment.title}</h1>
                                <p className="text-sm font-semibold" style={{ color: isPastDue ? 'var(--danger)' : 'var(--text-muted)' }}>
                                    Due {dueDate.toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                                </p>
                            </div>
                        </div>

                        <div style={{ borderTop: '1px solid var(--border)', paddingTop: '1.5rem' }}>
                            <p style={{ lineHeight: 1.7, color: 'var(--text-main)', whiteSpace: 'pre-wrap', fontSize: '1rem' }}>
                                {assignment.description || 'No instructions provided for this assignment.'}
                            </p>
                        </div>
                        
                        {assignment.file_url && (
                            <div style={{ borderTop: '1px solid var(--border)', paddingTop: '1.5rem', marginTop: '1.5rem' }}>
                                <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem' }}>Reference Material</h3>
                                <a href={`${API_BASE_URL}${assignment.file_url}`} target="_blank" rel="noreferrer" className="card" style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '1rem', textDecoration: 'none', color: 'inherit', border: '1px solid var(--border)' }}>
                                    <div style={{ padding: '0.75rem', background: 'var(--primary-light)', color: 'var(--primary)', borderRadius: '8px', fontSize: '1.25rem' }}>
                                        📄
                                    </div>
                                    <div>
                                        <p className="font-semibold">{assignment.file_url.split('/').pop() || 'Attachment'}</p>
                                        <p className="text-xs text-muted" style={{ marginTop: '0.2rem' }}>Click to view</p>
                                    </div>
                                </a>
                            </div>
                        )}
                    </div>

                    {/* Right: Submission Box */}
                    <div className="flex flex-col gap-4">
                        <div className="card" style={{ padding: '1.5rem' }}>
                            <div className="flex justify-between items-center" style={{ marginBottom: '1.5rem' }}>
                                <h3 style={{ fontSize: '1.1rem', margin: 0 }}>Your work</h3>
                                <span className={`badge ${isSubmitted ? 'badge-safe' : isPastDue ? 'badge-danger' : 'badge-warning'}`} style={{ fontSize: '0.7rem' }}>
                                    {isSubmitted ? 'Turned in' : isPastDue ? 'Missing' : 'Assigned'}
                                </span>
                            </div>

                            {isSubmitted ? (
                                <div className="flex flex-col gap-3">
                                    <div className="card" style={{ padding: '0.75rem', border: '1px solid var(--border)', background: 'var(--bg-secondary)', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                        <span style={{ fontSize: '1.25rem' }}>📄</span>
                                        <div style={{ overflow: 'hidden' }}>
                                            <p className="text-xs font-semibold truncate">Submission.pdf</p>
                                            <a href={`${API_BASE_URL}/${status.submission.file_url}`} target="_blank" rel="noreferrer" className="text-xs hover-link" style={{ color: 'var(--primary)' }}>View file</a>
                                        </div>
                                    </div>
                                    <p className="text-xs text-muted" style={{ textAlign: 'center' }}>
                                        Submitted on {new Date(status.submission.submission_date).toLocaleDateString()}
                                    </p>
                                </div>
                            ) : isPastDue ? (
                                <div className="text-center" style={{ padding: '1rem 0' }}>
                                    <p className="text-sm text-muted">The deadline for this assignment has passed. Submissions are closed.</p>
                                </div>
                            ) : (
                                <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                                    <div style={{ 
                                        border: '2px dashed var(--border)', 
                                        borderRadius: 'var(--radius-sm)', 
                                        padding: '2rem 1rem',
                                        textAlign: 'center',
                                        cursor: 'pointer',
                                        position: 'relative'
                                    }}>
                                        <input 
                                            type="file" 
                                            accept=".pdf" 
                                            onChange={handleFileChange}
                                            style={{ 
                                                position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', 
                                                opacity: 0, cursor: 'pointer' 
                                            }}
                                        />
                                        <div style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>➕</div>
                                        <p className="text-xs font-semibold">{file ? file.name : 'Add or create'}</p>
                                        <p className="text-xs text-muted">PDF only</p>
                                    </div>
                                    <button 
                                        type="submit" 
                                        className="btn-primary w-full" 
                                        disabled={uploading || !file}
                                        style={{ marginTop: '0.5rem' }}
                                    >
                                        {uploading ? 'Turning in...' : 'Turn in'}
                                    </button>
                                </form>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </>
    );
};

export default AssignmentDetail;
