
import React from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import NotificationBell from './NotificationBell';

const Navbar = () => {
    const { user, logout } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const getDashboardLink = () => {
        if (!user) return '/login';
        switch (user.role) {
            case 'admin': return '/admin';
            case 'mentor': return '/mentor';
            case 'both': {
                // Context-aware: link to whichever dashboard user is currently on
                if (location.pathname.startsWith('/lecturer')) return '/lecturer';
                return '/mentor';
            }
            case 'lecturer': return '/lecturer';
            default: return '/student';
        }
    };

    // For "both" users: determine if they're on mentor or lecturer side
    const isOnLecturerSide = user?.role === 'both' && (
        location.pathname.startsWith('/lecturer')
    );
    const isOnMentorSide = user?.role === 'both' && (
        location.pathname.startsWith('/mentor') || location.pathname.startsWith('/student/detail')
    );

    const navLinks = [];
    if (user) {
        navLinks.push({ to: getDashboardLink(), label: 'Dashboard' });
        if (user.role === 'student') {
            navLinks.push({ to: '/student/detail', label: 'My Profile' });
        }
    }

    const isActive = (path) => location.pathname === path;

    return (
        <nav style={{
            padding: '0.75rem 2rem',
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
            <div className="flex items-center gap-4">
                <Link to={getDashboardLink()} style={{ color: 'inherit', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontSize: '1.25rem' }}>🎓</span>
                    <span style={{ fontSize: '1.15rem', fontWeight: 700, color: 'var(--primary)', letterSpacing: '-0.02em' }}>
                        MSPA System
                    </span>
                </Link>
                {navLinks.map((link, i) => (
                    <Link key={i} to={link.to} style={{
                        fontSize: '0.85rem',
                        fontWeight: isActive(link.to) ? 700 : 500,
                        color: isActive(link.to) ? 'var(--primary)' : 'var(--text-muted)',
                        borderBottom: isActive(link.to) ? '2px solid var(--primary)' : '2px solid transparent',
                        paddingBottom: '0.15rem',
                        transition: 'all 0.2s ease'
                    }}>
                        {link.label}
                    </Link>
                ))}
            </div>
            <div className="flex items-center gap-3">
                {user ? (
                    <>
                        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                            <strong style={{ color: 'var(--text-main)' }}>{user.username}</strong>
                            <span style={{ margin: '0 0.4rem', opacity: 0.4 }}>|</span>
                            <span className={`badge ${user.role === 'admin' ? 'badge-danger' :
                                    user.role === 'student' ? 'badge-primary' : 'badge-safe'
                                }`} style={{ textTransform: 'capitalize' }}>
                                {user.role === 'both' ? (isOnLecturerSide ? 'Lecturer' : 'Mentor') : user.role}
                            </span>
                        </span>
                        {/* Switch dashboard button for dual-role users */}
                        {user.role === 'both' && (
                            <button
                                onClick={() => navigate(isOnLecturerSide ? '/mentor' : '/lecturer')}
                                style={{
                                    fontSize: '0.72rem', padding: '0.3rem 0.7rem', borderRadius: 20,
                                    background: isOnLecturerSide ? '#dcfce7' : '#e0e7ff',
                                    color: isOnLecturerSide ? '#166534' : '#3730a3',
                                    border: 'none', cursor: 'pointer',
                                    fontWeight: 600, transition: 'all 0.2s',
                                    display: 'flex', alignItems: 'center', gap: '0.3rem'
                                }}
                            >
                                🔄 {isOnLecturerSide ? 'Mentor' : 'Lecturer'}
                            </button>
                        )}
                        <NotificationBell />
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

