
import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const RoleGuard = ({ allowedRoles, children }) => {
    const { user } = useAuth();

    if (!user) {
        return <Navigate to="/login" replace />;
    }

    if (!allowedRoles.includes(user.role)) {
        return (
            <div className="container page-enter" style={{ textAlign: 'center', paddingTop: '4rem' }}>
                <div className="card" style={{ maxWidth: 440, margin: '0 auto', padding: '2.5rem' }}>
                    <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🔒</div>
                    <h2 style={{ border: 'none', paddingBottom: 0, marginBottom: '0.5rem' }}>Access Denied</h2>
                    <p className="text-muted" style={{ marginBottom: '1.5rem' }}>
                        You don't have permission to view this page.
                    </p>
                    <a href="/login" onClick={(e) => { e.preventDefault(); window.location.href = '/login'; }}>
                        <button>Go to Login</button>
                    </a>
                </div>
            </div>
        );
    }

    return children;
};

export default RoleGuard;
