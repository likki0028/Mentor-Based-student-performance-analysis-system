
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import toast, { Toaster } from 'react-hot-toast';

const Login = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [loading, setLoading] = useState(false);
    const [showRoleChooser, setShowRoleChooser] = useState(false);
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
                if (role === 'both') {
                    setShowRoleChooser(true);
                } else if (role === 'admin') navigate('/admin');
                else if (role === 'mentor') navigate('/mentor');
                else if (role === 'lecturer') navigate('/lecturer');
                else navigate('/student');
            }, 500);
        } catch (error) {
            toast.error('Invalid username or password');
        } finally {
            setLoading(false);
        }
    };

    // Role chooser for dual-role users
    if (showRoleChooser) {
        return (
            <div style={{
                minHeight: '100vh',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                padding: '1rem'
            }}>
                <div style={{ width: '100%', maxWidth: 500, animation: 'slideUp 0.5s ease' }}>
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
                        <h1 style={{ color: 'white', fontSize: '1.5rem', marginBottom: '0.25rem' }}>
                            Welcome, {username}!
                        </h1>
                        <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: '0.9rem' }}>
                            Choose which dashboard to open
                        </p>
                    </div>
                    <div style={{ display: 'flex', gap: '1rem' }}>
                        <div
                            onClick={() => navigate('/mentor')}
                            style={{
                                flex: 1, padding: '2rem 1.5rem', borderRadius: 16,
                                background: 'white', cursor: 'pointer',
                                textAlign: 'center',
                                boxShadow: '0 10px 40px rgba(0,0,0,0.15)',
                                transition: 'transform 0.2s, box-shadow 0.2s',
                                border: '2px solid transparent'
                            }}
                            onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-4px)'; e.currentTarget.style.borderColor = '#22c55e'; }}
                            onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.borderColor = 'transparent'; }}
                        >
                            <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>👨‍🏫</div>
                            <h3 style={{ color: '#22c55e', fontSize: '1.1rem', marginBottom: '0.4rem' }}>Mentor Dashboard</h3>
                            <p style={{ color: '#64748b', fontSize: '0.8rem', margin: 0 }}>
                                View mentees, track attendance, monitor student performance
                            </p>
                        </div>
                        <div
                            onClick={() => navigate('/lecturer')}
                            style={{
                                flex: 1, padding: '2rem 1.5rem', borderRadius: 16,
                                background: 'white', cursor: 'pointer',
                                textAlign: 'center',
                                boxShadow: '0 10px 40px rgba(0,0,0,0.15)',
                                transition: 'transform 0.2s, box-shadow 0.2s',
                                border: '2px solid transparent'
                            }}
                            onMouseEnter={e => { e.currentTarget.style.transform = 'translateY(-4px)'; e.currentTarget.style.borderColor = '#6366f1'; }}
                            onMouseLeave={e => { e.currentTarget.style.transform = 'translateY(0)'; e.currentTarget.style.borderColor = 'transparent'; }}
                        >
                            <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }}>📚</div>
                            <h3 style={{ color: '#6366f1', fontSize: '1.1rem', marginBottom: '0.4rem' }}>Lecturer Dashboard</h3>
                            <p style={{ color: '#64748b', fontSize: '0.8rem', margin: 0 }}>
                                Manage classrooms, upload marks, assign & grade work
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div style={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            padding: '1rem'
        }}>
            
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
                        MSPA System
                    </h1>
                    <p style={{ color: 'rgba(255,255,255,0.75)', fontSize: '0.9rem' }}>
                        Mentor-Based Student Performance Analysis System
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


                </div>
            </div>
        </div>
    );
};

export default Login;
