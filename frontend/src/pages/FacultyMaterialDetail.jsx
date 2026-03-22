import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import api, { API_BASE_URL } from '../services/api';
import toast from 'react-hot-toast';

const FacultyMaterialDetail = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [material, setMaterial] = useState(null);
    const [loading, setLoading] = useState(true);
    const [editMode, setEditMode] = useState(false);
    const [editForm, setEditForm] = useState({ title: '', description: '' });
    const [editSubmitting, setEditSubmitting] = useState(false);
    const [deleting, setDeleting] = useState(false);
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

    // File management
    const [materialFiles, setMaterialFiles] = useState([]);
    const [fileUploading, setFileUploading] = useState(false);
    const [fileToRemove, setFileToRemove] = useState(null);
    const [fileRemoving, setFileRemoving] = useState(false);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [matRes, filesRes] = await Promise.all([
                api.get(`/materials/${id}`),
                api.get(`/materials/${id}/files`)
            ]);
            setMaterial(matRes.data);
            setMaterialFiles(filesRes.data);
            setEditForm({
                title: matRes.data.title || '',
                description: matRes.data.description || ''
            });
        } catch (err) {
            console.error('Failed to load material:', err);
            toast.error('Failed to load material details');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchData(); }, [id]);

    const handleEdit = async (e) => {
        e.preventDefault();
        setEditSubmitting(true);
        try {
            await api.put(`/materials/${id}`, editForm);
            toast.success('Material updated');
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
            await api.delete(`/materials/${id}`);
            toast.success('Material deleted');
            navigate(-1);
        } catch (err) {
            toast.error('Failed to delete material');
            setDeleting(false);
            setShowDeleteConfirm(false);
        }
    };

    const handleFileUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        setFileUploading(true);
        try {
            const formData = new FormData();
            formData.append('file', file);
            await api.post(`/materials/${id}/attach-file`, formData);
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
            await api.delete(`/materials/${id}/remove-file/${fileToRemove.id}`);
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
                    <div className="skeleton" style={{ height: 300, borderRadius: 12 }}></div>
                </div>
            </>
        );
    }

    if (!material) {
        return (
            <>
                <Navbar />
                <div className="container text-center" style={{ marginTop: '5rem' }}>
                    <h2>Material not found</h2>
                    <button className="btn-primary" onClick={() => navigate(-1)}>Go Back</button>
                </div>
            </>
        );
    }

    const getFileInfo = (url) => {
        const ext = url ? url.split('.').pop().toLowerCase() : '';
        const map = {
            pdf: { icon: '📕', label: 'PDF Document', color: '#ef4444' },
            doc: { icon: '📘', label: 'Word Document', color: '#2563eb' },
            docx: { icon: '📘', label: 'Word Document', color: '#2563eb' },
            ppt: { icon: '📙', label: 'PowerPoint', color: '#f59e0b' },
            pptx: { icon: '📙', label: 'PowerPoint', color: '#f59e0b' },
            xls: { icon: '📗', label: 'Excel', color: '#22c55e' },
            xlsx: { icon: '📗', label: 'Excel', color: '#22c55e' },
            png: { icon: '🖼️', label: 'Image', color: '#8b5cf6' },
            jpg: { icon: '🖼️', label: 'Image', color: '#8b5cf6' },
            jpeg: { icon: '🖼️', label: 'Image', color: '#8b5cf6' },
            zip: { icon: '📦', label: 'Archive', color: '#6b7280' },
        };
        return map[ext] || { icon: '📄', label: 'File', color: 'var(--primary)' };
    };

    const mainFileInfo = getFileInfo(material.file_url);

    return (
        <>
            <Navbar />
            <div className="container page-enter" style={{ maxWidth: 1000 }}>
                {/* Breadcrumb */}
                <div className="flex items-center gap-2 text-muted text-sm" style={{ marginBottom: '1.5rem' }}>
                    <Link to="/lecturer" className="hover-link">Dashboard</Link>
                    <span>/</span>
                    <span className="text-main">Material Detail</span>
                </div>

                {/* Header Card */}
                <div className="card" style={{
                    padding: '2rem 2.5rem',
                    marginBottom: '1.5rem',
                    background: 'linear-gradient(135deg, #065f46 0%, #047857 50%, #059669 100%)',
                    color: 'white',
                    border: 'none',
                    position: 'relative',
                    overflow: 'hidden'
                }}>
                    <div style={{ position: 'absolute', top: -20, right: -20, fontSize: '8rem', opacity: 0.06, pointerEvents: 'none' }}>📁</div>
                    <div className="flex justify-between items-start">
                        <div style={{ flex: 1 }}>
                            <h1 style={{ color: 'white', fontSize: '1.75rem', marginBottom: '0.5rem' }}>{material.title}</h1>
                            <p style={{ opacity: 0.85, fontSize: '0.95rem', lineHeight: 1.6, maxWidth: 600 }}>
                                {material.description || 'No description provided.'}
                            </p>
                            <div className="flex items-center gap-4" style={{ marginTop: '1rem' }}>
                                <span style={{
                                    background: 'rgba(255,255,255,0.2)',
                                    color: 'white',
                                    padding: '0.3rem 0.8rem',
                                    borderRadius: '20px',
                                    fontSize: '0.8rem',
                                    fontWeight: 600
                                }}>
                                    {mainFileInfo.icon} {materialFiles.length} file{materialFiles.length !== 1 ? 's' : ''} attached
                                </span>
                                {material.uploaded_at && (
                                    <span style={{ opacity: 0.8, fontSize: '0.85rem' }}>
                                        Created: {new Date(material.uploaded_at).toLocaleDateString('en-IN', { dateStyle: 'medium' })}
                                    </span>
                                )}
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
                </div>

                {/* Attachments Section */}
                <div className="card" style={{ padding: '1.25rem 1.5rem', marginBottom: '1.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
                        <h3 style={{ margin: 0, fontSize: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>📎 Attachments ({materialFiles.length})</h3>
                        <label
                            className="btn-primary"
                            style={{ fontSize: '0.8rem', padding: '0.4rem 1rem', cursor: 'pointer', margin: 0, borderRadius: '8px' }}
                        >
                            {fileUploading ? 'Uploading...' : '+ Add File'}
                            <input type="file" accept=".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.png,.jpg,.jpeg,.zip,.txt,.csv" style={{ display: 'none' }} onChange={handleFileUpload} disabled={fileUploading} />
                        </label>
                    </div>

                    {materialFiles.length > 0 ? (
                        <div className="flex flex-col gap-2">
                            {materialFiles.map(f => {
                                const fi = getFileInfo(f.file_url);
                                return (
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
                                                background: `${fi.color}15`,
                                                color: fi.color,
                                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                fontSize: '1.1rem'
                                            }}>{fi.icon}</div>
                                            <div>
                                                <p className="font-semibold text-sm" style={{ margin: 0 }}>{f.filename}</p>
                                                <p className="text-xs text-muted" style={{ margin: 0 }}>{fi.label}{f.uploaded_at ? ` • ${new Date(f.uploaded_at).toLocaleDateString()}` : ''}</p>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <a
                                                href={`${API_BASE_URL}${f.file_url}`}
                                                target="_blank"
                                                rel="noreferrer"
                                                className="btn-secondary"
                                                style={{ textDecoration: 'none', fontSize: '0.75rem', padding: '0.3rem 0.7rem' }}
                                            >👁️ View</a>
                                            <a
                                                href={`${API_BASE_URL}${f.file_url}`}
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
                                );
                            })}
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
                            <input type="file" accept=".pdf,.doc,.docx,.ppt,.pptx,.xls,.xlsx,.png,.jpg,.jpeg,.zip,.txt,.csv" style={{ display: 'none' }} onChange={handleFileUpload} disabled={fileUploading} />
                        </label>
                    )}
                </div>

                {/* Details Card */}
                <div className="card" style={{ padding: '1.5rem' }}>
                    <h3 style={{ margin: '0 0 1rem 0', fontSize: '1.1rem' }}>📋 Details</h3>
                    <div className="grid" style={{ gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                        <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: '10px' }}>
                            <p className="text-xs text-muted" style={{ margin: '0 0 0.25rem' }}>Subject ID</p>
                            <p className="font-semibold text-sm" style={{ margin: 0 }}>{material.subject_id}</p>
                        </div>
                        <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: '10px' }}>
                            <p className="text-xs text-muted" style={{ margin: '0 0 0.25rem' }}>Section ID</p>
                            <p className="font-semibold text-sm" style={{ margin: 0 }}>{material.section_id}</p>
                        </div>
                        <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: '10px' }}>
                            <p className="text-xs text-muted" style={{ margin: '0 0 0.25rem' }}>Total Files</p>
                            <p className="font-semibold text-sm" style={{ margin: 0 }}>{materialFiles.length} file{materialFiles.length !== 1 ? 's' : ''}</p>
                        </div>
                        <div style={{ padding: '1rem', background: 'var(--bg-secondary)', borderRadius: '10px' }}>
                            <p className="text-xs text-muted" style={{ margin: '0 0 0.25rem' }}>Uploaded</p>
                            <p className="font-semibold text-sm" style={{ margin: 0 }}>{material.uploaded_at ? new Date(material.uploaded_at).toLocaleDateString('en-IN', { dateStyle: 'medium' }) : '—'}</p>
                        </div>
                    </div>
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
                        <h2 style={{ marginTop: 0 }}>Edit Material</h2>
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
                        <h2 style={{ marginTop: 0, marginBottom: '0.5rem' }}>Delete Material?</h2>
                        <p className="text-muted" style={{ marginBottom: '1.5rem' }}>
                            Are you sure you want to delete <strong>"{material?.title}"</strong>? All attached files will also be deleted. This cannot be undone.
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

export default FacultyMaterialDetail;
