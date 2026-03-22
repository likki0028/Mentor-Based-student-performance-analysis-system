import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import api from '../services/api';
import toast from 'react-hot-toast';

const MaterialDetail = () => {
    const { id } = useParams();
    const [material, setMaterial] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchMaterial = async () => {
            try {
                setLoading(true);
                const res = await api.get(`/materials/${id}`);
                setMaterial(res.data);
            } catch (err) {
                console.error('Failed to fetch material:', err);
                toast.error('Failed to load material details');
            } finally {
                setLoading(false);
            }
        };
        fetchMaterial();
    }, [id]);

    if (loading) {
        return (
            <>
                <Navbar />
                <div className="container page-enter">
                    <div className="skeleton" style={{ height: 300, borderRadius: 8 }}></div>
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
                    <Link to="/student"><button className="btn-primary">Back to Dashboard</button></Link>
                </div>
            </>
        );
    }

    const fileName = material.file_url.split('/').pop().split('_').slice(2).join('_') || 'Material File';

    return (
        <>
            <Navbar />
            <div className="container page-enter" style={{ maxWidth: 800 }}>
                <div className="flex items-center gap-2 text-muted text-sm" style={{ marginBottom: '1.5rem' }}>
                    <Link to="/student" className="hover-link">Dashboard</Link>
                    <span>/</span>
                    <Link to={`/student/subject/${material.subject_id}`} className="hover-link">Classroom</Link>
                    <span>/</span>
                    <span className="text-main">Material</span>
                </div>

                <div className="card" style={{ padding: '2.5rem' }}>
                    <div className="flex items-center gap-4" style={{ marginBottom: '2rem' }}>
                        <div style={{ 
                            width: 50, height: 50, borderRadius: '50%', 
                            background: 'var(--success)', color: 'white', 
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            fontSize: '1.5rem'
                        }}>📁</div>
                        <div>
                            <h1 style={{ fontSize: '2rem', marginBottom: '0.25rem' }}>{material.title}</h1>
                            <p className="text-sm text-muted">Posted on {new Date().toLocaleDateString()}</p>
                        </div>
                    </div>

                    <div style={{ borderTop: '1px solid var(--border)', paddingTop: '1.5rem', marginBottom: '2.5rem' }}>
                        <p style={{ lineHeight: 1.7, color: 'var(--text-main)', whiteSpace: 'pre-wrap' }}>
                            {material.description || 'No description provided for this material.'}
                        </p>
                    </div>

                    <div className="card" style={{ 
                        background: 'var(--bg-secondary)', 
                        border: '1px solid var(--border)',
                        padding: '1rem',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center'
                    }}>
                        <div className="flex items-center gap-3">
                            <span style={{ fontSize: '1.5rem' }}>📄</span>
                            <div>
                                <p style={{ fontWeight: 600, fontSize: '0.9rem' }}>{fileName}</p>
                                <p className="text-xs text-muted">PDF Document</p>
                            </div>
                        </div>
                        <a 
                            href={`http://localhost:8000${material.file_url}`} 
                            target="_blank" 
                            rel="noreferrer"
                            className="btn-primary"
                            style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}
                        >
                            View / Download
                        </a>
                    </div>
                </div>
            </div>
        </>
    );
};

export default MaterialDetail;
