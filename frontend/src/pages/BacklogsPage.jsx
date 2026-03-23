import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import Navbar from '../components/Navbar';

const BacklogsPage = () => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [students, setStudents] = useState([]);
    const [loading, setLoading] = useState(true);
    const [expandedId, setExpandedId] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const res = await api.get('/faculty/my-students');
                const withBacklogs = (res.data || [])
                    .filter(s => (s.backlogs || 0) > 0)
                    .sort((a, b) => (b.backlogs || 0) - (a.backlogs || 0));
                setStudents(withBacklogs);
            } catch (err) {
                console.error('Failed to fetch students:', err);
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
                    <div className="skeleton" style={{ height: 200, marginTop: '2rem' }}></div>
                    <div className="skeleton" style={{ height: 400, marginTop: '1rem' }}></div>
                </div>
            </>
        );
    }

    return (
        <>
            <Navbar />
            <div className="container page-enter">
                {/* Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                    <div>
                        <h1 style={{ marginBottom: '0.25rem' }}>📋 Active Backlogs</h1>
                        <span style={{ color: '#64748b', fontSize: '0.9rem' }}>
                            {students.length} student{students.length !== 1 ? 's' : ''} with pending backlogs
                        </span>
                    </div>
                    <button className="btn-secondary" onClick={() => navigate('/mentor')} style={{ background: '#fff', color: '#475569', border: '1px solid #e2e8f0' }}>
                        ← Back to Dashboard
                    </button>
                </div>

                {students.length === 0 ? (
                    <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
                        <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🎉</div>
                        <h2 style={{ border: 'none' }}>No Active Backlogs</h2>
                        <p style={{ color: '#64748b' }}>All your mentees have cleared their subjects. Great work!</p>
                    </div>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        {students.map(s => {
                            const isOpen = expandedId === s.id;
                            const severity = s.backlogs >= 5 ? 'danger' : s.backlogs >= 3 ? 'warning' : 'info';
                            const colors = {
                                danger: { bg: '#fef2f2', border: '#fca5a5', badge: '#dc2626', badgeBg: 'rgba(220,38,38,0.1)' },
                                warning: { bg: '#fffbeb', border: '#fcd34d', badge: '#f59e0b', badgeBg: 'rgba(245,158,11,0.1)' },
                                info: { bg: '#f5f3ff', border: '#c4b5fd', badge: '#6366f1', badgeBg: 'rgba(99,102,241,0.1)' },
                            }[severity];

                            return (
                                <div key={s.id} style={{
                                    background: '#fff',
                                    borderRadius: 12,
                                    border: '1px solid #e2e8f0',
                                    overflow: 'hidden',
                                    boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
                                }}>
                                    {/* Student Header Row */}
                                    <div
                                        onClick={() => setExpandedId(isOpen ? null : s.id)}
                                        style={{
                                            display: 'flex',
                                            alignItems: 'center',
                                            padding: '1rem 1.25rem',
                                            cursor: 'pointer',
                                            background: isOpen ? colors.bg : '#fff',
                                            borderLeft: `4px solid ${colors.badge}`,
                                            transition: 'background 0.2s',
                                        }}
                                    >
                                        {/* Backlog Count Badge */}
                                        <div style={{
                                            width: 48, height: 48, borderRadius: 12,
                                            background: colors.badgeBg,
                                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                                            color: colors.badge, fontWeight: 800, fontSize: '1.25rem',
                                            marginRight: '1rem', flexShrink: 0,
                                        }}>
                                            {s.backlogs}
                                        </div>

                                        {/* Student Info */}
                                        <div style={{ flex: 1 }}>
                                            <div style={{ fontWeight: 700, fontSize: '1rem', color: '#1e293b' }}>
                                                {s.enrollment_number}
                                            </div>
                                            <div style={{ fontSize: '0.85rem', color: '#64748b', marginTop: 2 }}>
                                                {s.name}
                                            </div>
                                        </div>

                                        {/* CGPA */}
                                        <div style={{ textAlign: 'center', marginRight: '1.5rem' }}>
                                            <div style={{ fontSize: '0.7rem', color: '#94a3b8', textTransform: 'uppercase', fontWeight: 600 }}>CGPA</div>
                                            <div style={{
                                                fontWeight: 800, fontSize: '1.1rem',
                                                color: s.cgpa < 5 ? '#dc2626' : s.cgpa < 7 ? '#f59e0b' : '#22c55e',
                                            }}>{s.cgpa?.toFixed(2)}</div>
                                        </div>

                                        {/* Risk Badge */}
                                        <div style={{
                                            padding: '0.25rem 0.75rem', borderRadius: 20, fontSize: '0.75rem', fontWeight: 700,
                                            background: s.risk_status === 'At Risk' ? 'rgba(239,68,68,0.1)' : s.risk_status === 'Warning' ? 'rgba(245,158,11,0.1)' : 'rgba(34,197,94,0.1)',
                                            color: s.risk_status === 'At Risk' ? '#dc2626' : s.risk_status === 'Warning' ? '#f59e0b' : '#22c55e',
                                            marginRight: '1rem',
                                        }}>
                                            {s.risk_status}
                                        </div>

                                        {/* Chevron */}
                                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
                                            stroke="#94a3b8" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
                                            style={{ transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s', flexShrink: 0 }}
                                        >
                                            <path d="m6 9 6 6 6-6"/>
                                        </svg>
                                    </div>

                                    {/* Expanded: Backlog Subjects Table */}
                                    {isOpen && (
                                        <div style={{ borderTop: '1px solid #e2e8f0', padding: '1rem 1.25rem', background: '#fafbfc' }}>
                                            <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#475569', marginBottom: '0.75rem' }}>
                                                📚 Backlog Subjects ({(s.backlog_subjects || []).length})
                                            </div>
                                            {(s.backlog_subjects || []).length > 0 ? (
                                                <table style={{ width: '100%', margin: 0 }}>
                                                    <thead>
                                                        <tr>
                                                            <th style={{ textAlign: 'left', padding: '0.6rem 0.75rem' }}>Subject</th>
                                                            <th style={{ textAlign: 'center', padding: '0.6rem 0.75rem' }}>Semester</th>
                                                            <th style={{ textAlign: 'center', padding: '0.6rem 0.75rem' }}>Credits</th>
                                                            <th style={{ textAlign: 'center', padding: '0.6rem 0.75rem' }}>Score</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {s.backlog_subjects.map((bs, i) => (
                                                            <tr key={i}>
                                                                <td style={{ padding: '0.6rem 0.75rem' }}>
                                                                    <span style={{ fontWeight: 600 }}>{bs.subject_code}</span>
                                                                    <span style={{ marginLeft: 8, color: '#64748b', fontSize: '0.85rem' }}>{bs.subject_name}</span>
                                                                </td>
                                                                <td style={{ textAlign: 'center', padding: '0.6rem 0.75rem', fontWeight: 600 }}>
                                                                    Sem {bs.semester}
                                                                </td>
                                                                <td style={{ textAlign: 'center', padding: '0.6rem 0.75rem', fontWeight: 600 }}>
                                                                    {bs.credits}
                                                                </td>
                                                                <td style={{ textAlign: 'center', padding: '0.6rem 0.75rem' }}>
                                                                    <span style={{
                                                                        fontWeight: 700, color: '#dc2626',
                                                                        background: 'rgba(239,68,68,0.1)',
                                                                        padding: '2px 10px', borderRadius: 12, fontSize: '0.85rem',
                                                                    }}>
                                                                        {bs.percentage}%
                                                                    </span>
                                                                </td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            ) : (
                                                <div style={{ textAlign: 'center', padding: '1rem', color: '#94a3b8' }}>
                                                    No specific subject data available for this student.
                                                </div>
                                            )}
                                            <div style={{ marginTop: '0.75rem', textAlign: 'right' }}>
                                                <button
                                                    onClick={() => navigate(`/student/detail?id=${s.id}`)}
                                                    style={{ fontSize: '0.8rem', padding: '0.4rem 1rem' }}
                                                >
                                                    View Full Profile →
                                                </button>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </>
    );
};

export default BacklogsPage;
