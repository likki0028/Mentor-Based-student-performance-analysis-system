
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import Navbar from '../components/Navbar';
import toast, { Toaster } from 'react-hot-toast';

const ChangePassword = () => {
    const { user } = useAuth();
    const navigate = useNavigate();
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (newPassword.length < 4) {
            toast.error('New password must be at least 4 characters');
            return;
        }
        if (newPassword !== confirmPassword) {
            toast.error('Passwords do not match');
            return;
        }

        setLoading(true);
        try {
            await api.post('/auth/change-password', null, {
                params: { current_password: currentPassword, new_password: newPassword }
            });
            toast.success('Password changed successfully!');
            setCurrentPassword('');
            setNewPassword('');
            setConfirmPassword('');
            setTimeout(() => navigate(-1), 1500);
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Failed to change password');
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            <Navbar />
            
            <div className="container page-enter" style={{ maxWidth: 500 }}>
                <div className="card" style={{ marginTop: '2rem' }}>
                    <h2 style={{ textAlign: 'center', border: 'none', paddingBottom: 0, marginBottom: '0.5rem' }}>
                        Change Password
                    </h2>
                    <p className="text-muted text-sm" style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
                        Logged in as <strong>{user?.username}</strong>
                    </p>

                    <form onSubmit={handleSubmit}>
                        <div className="form-group">
                            <label>Current Password</label>
                            <input type="password" placeholder="Enter current password"
                                value={currentPassword}
                                onChange={(e) => setCurrentPassword(e.target.value)} />
                        </div>
                        <div className="form-group">
                            <label>New Password</label>
                            <input type="password" placeholder="Enter new password"
                                value={newPassword}
                                onChange={(e) => setNewPassword(e.target.value)} />
                        </div>
                        <div className="form-group">
                            <label>Confirm New Password</label>
                            <input type="password" placeholder="Confirm new password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)} />
                            {confirmPassword && newPassword !== confirmPassword && (
                                <p style={{ color: 'var(--danger)', fontSize: '0.75rem', marginTop: '0.25rem' }}>
                                    Passwords do not match
                                </p>
                            )}
                        </div>
                        <button type="submit" className="w-full" disabled={loading || !currentPassword || !newPassword}
                            style={{ marginTop: '0.5rem' }}>
                            {loading ? 'Changing...' : 'Update Password'}
                        </button>
                    </form>
                </div>
            </div>
        </>
    );
};

export default ChangePassword;
