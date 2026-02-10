
import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Navbar = () => {
    const { user, logout } = useAuth();

    return (

        <nav style={{ padding: '1rem 2rem', background: 'var(--surface)', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', boxShadow: '0 1px 2px rgba(0,0,0,0.05)' }}>
            <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: 'var(--primary)' }}>
                <Link to="/" style={{ color: 'inherit' }}>AcademicVibe</Link>
            </div>
            <div className="flex items-center gap-2">
                {user ? (
                    <>
                        <span style={{ marginRight: '1rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                            Logged in as <strong style={{ textTransform: 'capitalize', color: 'var(--text-main)' }}>{user.role}</strong>
                        </span>
                        <button onClick={logout} style={{ background: 'var(--secondary)', fontSize: '0.8rem' }}>Logout</button>
                    </>
                ) : (
                    <Link to="/login"><button>Login</button></Link>
                )}
            </div>
        </nav>
    );

};

export default Navbar;
