
import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Navbar = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const getDashboardLink = () => {
        if (!user) return '/login';
        switch (user.role) {
            case 'admin': return '/admin';
            case 'mentor': case 'both': return '/mentor';
            case 'lecturer': return '/lecturer';
            default: return '/student';
        }
    };

    return (
        <nav style={{
            padding: '0.75rem 2rem',
            background: 'var(--surface)',
            borderBottom: '1px solid var(--border)',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            boxShadow: 'var(--shadow)',
            position: 'sticky',
            top: 0,
            zIndex: 100,
            backdropFilter: 'blur(10px)',
            background: 'rgba(255, 255, 255, 0.95)'
        }}>
            <Link to={getDashboardLink()} style={{ color: 'inherit', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ fontSize: '1.25rem' }}>🎓</span>
                <span style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--primary)', letterSpacing: '-0.02em' }}>
                    AcademicVibe
                </span>
            </Link>
            <div className="flex items-center gap-3">
                {user ? (
                    <>
                        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                            <strong style={{ color: 'var(--text-main)' }}>{user.username}</strong>
                            <span style={{ margin: '0 0.4rem', opacity: 0.4 }}>|</span>
                            <span className={`badge ${user.role === 'admin' ? 'badge-danger' :
                                    user.role === 'student' ? 'badge-primary' : 'badge-safe'
                                }`} style={{ textTransform: 'capitalize' }}>
                                {user.role}
                            </span>
                        </span>
                        <Link to="/change-password">
                            <button className="btn-secondary" style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}>
                                🔑 Password
                            </button>
                        </Link>
                        <button onClick={handleLogout} className="btn-danger" style={{ fontSize: '0.8rem', padding: '0.35rem 0.8rem' }}>
                            Logout
                        </button>
                    </>
                ) : (
                    <Link to="/login"><button>Login</button></Link>
                )}
            </div>
        </nav>
    );
};

export default Navbar;
