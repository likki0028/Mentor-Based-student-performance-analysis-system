
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import toast, { Toaster } from 'react-hot-toast';

const Login = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!username || !password) {
            toast.error('Please enter username and password');
            return;
        }
        setLoading(true);
        try {
            const role = await login(username, password);
            toast.success('Login successful!');
            setTimeout(() => {
                if (role === 'admin') navigate('/admin');
                else if (role === 'mentor' || role === 'both') navigate('/mentor');
                else if (role === 'lecturer') navigate('/lecturer');
                else navigate('/student');
            }, 500);
        } catch (error) {
            toast.error('Invalid username or password');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            padding: '1rem'
        }}>
            <Toaster position="top-right" />
            <div style={{
                width: '100%',
                maxWidth: 420,
                animation: 'slideUp 0.5s ease'
            }}>
                {/* Logo area */}
                <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                    <div style={{
                        width: 64, height: 64, borderRadius: 16,
                        background: 'rgba(255,255,255,0.2)',
                        backdropFilter: 'blur(10px)',
                        display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                        marginBottom: '1rem', fontSize: '1.75rem'
                    }}>
                        🎓
                    </div>
                    <h1 style={{ color: 'white', fontSize: '1.75rem', marginBottom: '0.25rem' }}>
                        AcademicVibe
                    </h1>
                    <p style={{ color: 'rgba(255,255,255,0.75)', fontSize: '0.9rem' }}>
                        Mentor-Based Student Performance System
                    </p>
                </div>

                {/* Card */}
                <div className="card" style={{
                    padding: '2rem',
                    boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
                    border: 'none'
                }}>
                    <h2 style={{ textAlign: 'center', border: 'none', paddingBottom: 0, marginBottom: '1.5rem', fontSize: '1.25rem' }}>
                        Welcome Back
                    </h2>
                    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        <div className="form-group" style={{ marginBottom: 0 }}>
                            <label>Username</label>
                            <input
                                type="text"
                                placeholder="Enter your username"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                autoFocus
                            />
                        </div>
                        <div className="form-group" style={{ marginBottom: 0 }}>
                            <label>Password</label>
                            <input
                                type="password"
                                placeholder="Enter your password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                            />
                        </div>
                        <button type="submit" disabled={loading} className="w-full" style={{ marginTop: '0.5rem', padding: '0.75rem' }}>
                            {loading ? 'Signing in...' : 'Sign In'}
                        </button>
                    </form>

                    <div style={{ marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px solid var(--border)', textAlign: 'center' }}>
                        <p className="text-sm text-muted" style={{ marginBottom: '0.5rem' }}>Demo Accounts:</p>
                        <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '0.5rem' }}>
                            {[
                                { user: 'admin', pass: 'admin123', color: '#ef4444' },
                                { user: 'mentor', pass: 'mentor123', color: '#22c55e' },
                                { user: 'lecturer', pass: 'lecturer123', color: '#f59e0b' },
                                { user: 'student', pass: 'student123', color: '#6366f1' }
                            ].map((demo, i) => (
                                <button key={i} className="btn-secondary"
                                    style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}
                                    onClick={() => { setUsername(demo.user); setPassword(demo.pass); }}
                                    type="button">
                                    <span style={{ color: demo.color, fontWeight: 700 }}>{demo.user}</span>
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Login;
