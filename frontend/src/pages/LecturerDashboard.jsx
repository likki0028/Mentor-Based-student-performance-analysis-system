
import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import Navbar from '../components/Navbar';
import toast, { Toaster } from 'react-hot-toast';

const LecturerDashboard = () => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [classrooms, setClassrooms] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const clsRes = await api.get('/faculty/my-subjects');
                setClassrooms(clsRes.data);
            } catch (err) {
                toast.error('Failed to load dashboard data');
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
                </div>
            </>
        );
    }



    const gradientPalettes = [
        'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
        'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
        'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)',
        'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
        'linear-gradient(135deg, #10b981 0%, #059669 100%)',
        'linear-gradient(135deg, #ec4899 0%, #db2777 100%)',
    ];

    return (
        <>
            <Navbar />
            
            <div className="container page-enter">
                <div style={{ marginBottom: '2rem' }}>
                    <h1>Lecturer Dashboard</h1>
                    <p className="text-muted">Manage your teaching classrooms, assignments, and students.</p>
                </div>

                {/* Quick Stats */}
                <div className="grid grid-3" style={{ gap: '1rem', marginBottom: '2.5rem' }}>
                    {[
                        { label: 'Classrooms', value: classrooms.length, icon: '🏫', color: 'var(--primary)' },
                    ].map((stat, i) => (
                        <div key={i} className="card hover-lift" style={{ padding: '1.25rem', textAlign: 'center' }}>
                            <div style={{ fontSize: '1.5rem', marginBottom: '0.25rem' }}>{stat.icon}</div>
                            <div style={{ fontSize: '1.75rem', fontWeight: 800, color: stat.color }}>{stat.value}</div>
                            <div className="text-xs text-muted" style={{ marginTop: '0.2rem' }}>{stat.label}</div>
                        </div>
                    ))}
                </div>

                {/* My Classrooms Section */}
                <div style={{ marginBottom: '2.5rem' }}>
                    <h2 style={{ marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span>🏫</span> My Classrooms
                    </h2>
                    <div className="grid grid-3" style={{ gap: '1.25rem' }}>
                        {classrooms.map((cls, i) => (
                            <div 
                                key={i} 
                                className="card hover-lift cursor-pointer" 
                                style={{ 
                                    padding: '1.5rem', 
                                    background: gradientPalettes[i % gradientPalettes.length],
                                    color: 'white',
                                    border: 'none',
                                    minHeight: '160px',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    justifyContent: 'space-between',
                                    position: 'relative',
                                    overflow: 'hidden'
                                }}
                                onClick={() => navigate(`/lecturer/classroom/${cls.subject_id}/${cls.section_id}`)}
                            >
                                <div style={{ 
                                    position: 'absolute', top: '-10px', right: '-10px', 
                                    fontSize: '5rem', opacity: 0.1, pointerEvents: 'none' 
                                }}>📖</div>
                                <div>
                                    <h3 style={{ margin: 0, color: 'white', fontSize: '1.2rem' }}>{cls.subject_name}</h3>
                                    <p style={{ opacity: 0.8, fontSize: '0.8rem', fontWeight: 500 }}>{cls.subject_code}</p>
                                </div>
                                <div className="flex justify-between items-end">
                                    <span style={{ 
                                        background: 'rgba(255,255,255,0.2)', 
                                        padding: '0.25rem 0.75rem', 
                                        borderRadius: '20px', 
                                        fontSize: '0.75rem',
                                        fontWeight: 600
                                    }}>
                                        {cls.section_name}
                                    </span>
                                    <span style={{ fontSize: '0.75rem', opacity: 0.9 }}>Open Classroom →</span>
                                </div>
                            </div>
                        ))}
                        {classrooms.length === 0 && (
                            <div className="card col-span-3 text-center py-8" style={{ background: 'var(--bg-secondary)', border: '1px dashed var(--border)' }}>
                                <p className="text-muted">No classrooms assigned yet.</p>
                                <p className="text-xs text-muted">Post materials or assignments to create a classroom.</p>
                            </div>
                        )}
                    </div>
                </div>


            </div>
        </>
    );
};

export default LecturerDashboard;
