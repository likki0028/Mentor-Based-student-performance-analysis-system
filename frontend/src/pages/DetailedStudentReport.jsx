import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import api from '../services/api';
import toast from 'react-hot-toast';

const CategoryAccordion = ({ title, students, color, emoji, isOpen, onToggle }) => {
    const navigate = useNavigate();
    
    return (
        <div className="card" style={{ padding: 0, overflow: 'hidden', marginBottom: '1rem', borderLeft: `4px solid ${color}` }}>
            <div 
                style={{ 
                    padding: '1rem 1.5rem', 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center', 
                    cursor: 'pointer',
                    background: isOpen ? '#f8fafc' : 'white'
                }}
                onClick={onToggle}
            >
                <div className="flex items-center gap-3">
                    <span style={{ fontSize: '1.25rem' }}>{emoji}</span>
                    <h2 style={{ margin: 0, border: 'none', padding: 0, fontSize: '1.1rem' }}>
                        {title} 
                        <span className="text-muted" style={{ fontWeight: 400, marginLeft: '0.75rem', fontSize: '0.9rem' }}>
                            ({students.length} Students)
                        </span>
                    </h2>
                </div>
                <div style={{ transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m6 9 6 6 6-6"/></svg>
                </div>
            </div>
            
            {isOpen && (
                <div style={{ padding: '0 1.5rem 1.5rem', background: '#f8fafc' }}>
                    {students.length === 0 ? (
                        <p className="text-center text-muted" style={{ padding: '1rem 0', margin: 0, fontSize: '0.9rem' }}>
                            No students in this category.
                        </p>
                    ) : (
                        <div style={{ overflowX: 'auto' }}>
                            <table style={{ background: 'white', borderRadius: '8px', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}>
                                <thead>
                                    <tr>
                                        <th style={{ fontSize: '0.75rem', padding: '0.5rem 1rem' }}>Name</th>
                                        <th style={{ fontSize: '0.75rem', padding: '0.5rem 1rem' }}>Roll No</th>
                                        <th style={{ fontSize: '0.75rem', padding: '0.5rem 1rem' }}>Attendance</th>
                                        <th style={{ fontSize: '0.75rem', padding: '0.5rem 1rem' }}>Avg Marks</th>
                                        <th style={{ fontSize: '0.75rem', padding: '0.5rem 1rem' }}>CGPA</th>
                                        <th style={{ fontSize: '0.75rem', padding: '0.5rem 1rem' }}>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {students.map((s, i) => (
                                        <tr key={i}>
                                            <td style={{ fontWeight: 600, fontSize: '0.85rem' }}>{s.name}</td>
                                            <td className="text-muted" style={{ fontSize: '0.8rem' }}>{s.enrollment_number}</td>
                                            <td style={{ fontSize: '0.85rem' }}>
                                                <span style={{ color: s.attendance_percentage < 75 ? '#ef4444' : '#22c55e', fontWeight: 600 }}>
                                                    {s.attendance_percentage}%
                                                </span>
                                            </td>
                                            <td style={{ fontSize: '0.85rem' }}>{s.average_marks}%</td>
                                            <td style={{ fontSize: '0.85rem' }}>
                                                <span style={{ 
                                                    fontWeight: 700, 
                                                    color: s.cgpa >= 8 ? '#16a34a' : s.cgpa >= 6 ? '#ca8a04' : s.cgpa > 0 ? '#dc2626' : 'var(--text-muted)'
                                                }}>
                                                    {s.cgpa > 0 ? s.cgpa.toFixed(2) : '—'}
                                                </span>
                                            </td>
                                            <td>
                                                <button 
                                                    style={{ fontSize: '0.7rem', padding: '0.2rem 0.6rem' }}
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        navigate(`/student/detail?id=${s.id}`);
                                                    }}
                                                >
                                                    View
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

const DetailedStudentReport = () => {
    const [students, setStudents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [openCategory, setOpenCategory] = useState('At Risk');

    useEffect(() => {
        const fetchStudents = async () => {
            try {
                setLoading(true);
                const res = await api.get('/faculty/my-students');
                setStudents(res.data);
            } catch (err) {
                console.error("Error fetching mentees:", err);
                toast.error("Failed to load student data");
            } finally {
                setLoading(false);
            }
        };
        fetchStudents();
    }, []);

    const atRisk = students.filter(s => s.risk_status === 'At Risk');
    const warning = students.filter(s => s.risk_status === 'Warning');
    const safe = students.filter(s => s.risk_status === 'Safe');

    return (
        <>
            <Navbar />
            <div className="container page-enter">
                <div style={{ marginBottom: '2.5rem' }}>
                    <h1>Detailed Student Report</h1>
                    <p className="text-muted">Comprehensive analysis and performance metrics for all mentees.</p>
                </div>
                
                {loading ? (
                    <div className="flex justify-center" style={{ padding: '4rem' }}>
                        <div className="skeleton" style={{ width: '100%', height: '300px' }}></div>
                    </div>
                ) : (
                    <div className="flex flex-col gap-2">
                        <CategoryAccordion 
                            title="At Risk Students" 
                            students={atRisk} 
                            color="#ef4444" 
                            emoji="🔴" 
                            isOpen={openCategory === 'At Risk'}
                            onToggle={() => setOpenCategory(openCategory === 'At Risk' ? null : 'At Risk')}
                        />
                        <CategoryAccordion 
                            title="Warning Students" 
                            students={warning} 
                            color="#f59e0b" 
                            emoji="🟡" 
                            isOpen={openCategory === 'Warning'}
                            onToggle={() => setOpenCategory(openCategory === 'Warning' ? null : 'Warning')}
                        />
                        <CategoryAccordion 
                            title="Safe & Performance Stable" 
                            students={safe} 
                            color="#22c55e" 
                            emoji="🟢" 
                            isOpen={openCategory === 'Safe'}
                            onToggle={() => setOpenCategory(openCategory === 'Safe' ? null : 'Safe')}
                        />
                    </div>
                )}
            </div>
        </>
    );
};

export default DetailedStudentReport;
