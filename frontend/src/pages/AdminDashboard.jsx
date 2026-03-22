
import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import authService from '../services/auth.service';
import analyticsService from '../services/analytics.service';
import academicService from '../services/academic.service';
import api from '../services/api';
import Navbar from '../components/Navbar';
import toast, { Toaster } from 'react-hot-toast';

const AdminDashboard = () => {
    const { user } = useAuth();
    const [stats, setStats] = useState(null);
    const [users, setUsers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(null); // 'user' | 'mentor' | null
    const [filter, setFilter] = useState('');
    const [roleFilter, setRoleFilter] = useState('');

    // Form state
    const [formData, setFormData] = useState({
        username: '', email: '', password: '', role: 'student',
        student_id: '', mentor_id: ''
    });

    const fetchData = async () => {
        try {
            setLoading(true);
            const [statsRes, usersRes] = await Promise.all([
                api.get('/admin/stats'),
                api.get('/admin/users')
            ]);
            setStats(statsRes.data);
            setUsers(usersRes.data);
        } catch (err) {
            toast.error('Failed to load admin data');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => { fetchData(); }, []);

    const handleCreateUser = async () => {
        try {
            await api.post('/admin/create-user', {
                username: formData.username,
                email: formData.email || null,
                password: formData.password,
                role: formData.role
            });
            toast.success(`User "${formData.username}" created!`);
            setShowModal(null);
            setFormData({ username: '', email: '', password: '', role: 'student', student_id: '', mentor_id: '' });
            fetchData();
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Failed to create user');
        }
    };

    const handleAssignMentor = async () => {
        try {
            await api.post('/admin/assign-mentor', {
                student_id: parseInt(formData.student_id),
                mentor_id: parseInt(formData.mentor_id)
            });
            toast.success('Mentor assigned!');
            setShowModal(null);
            fetchData();
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Failed to assign mentor');
        }
    };

    const handleDeleteUser = async (userId, username) => {
        if (!window.confirm(`Delete user "${username}"? This cannot be undone.`)) return;
        try {
            await api.delete(`/admin/users/${userId}`);
            toast.success(`User "${username}" deleted`);
            fetchData();
        } catch (err) {
            toast.error(err.response?.data?.detail || 'Failed to delete user');
        }
    };

    const filteredUsers = users.filter(u => {
        const matchesSearch = u.username.toLowerCase().includes(filter.toLowerCase()) ||
            (u.email || '').toLowerCase().includes(filter.toLowerCase());
        const matchesRole = !roleFilter || u.role === roleFilter;
        return matchesSearch && matchesRole;
    });

    const students = users.filter(u => u.role === 'student');
    const mentors = users.filter(u => ['mentor', 'both'].includes(u.role));

    if (loading) {
        return (
            <>
                <Navbar />
                
                <div className="container page-enter">
                    <div className="grid grid-4" style={{ marginTop: '2rem' }}>
                        {[1, 2, 3, 4].map(i => <div key={i} className="skeleton skeleton-card"></div>)}
                    </div>
                </div>
            </>
        );
    }

    return (
        <>
            <Navbar />
            
            <div className="container page-enter">
                <div className="flex justify-between items-end" style={{ marginBottom: '2rem' }}>
                    <div>
                        <h1>Administration Console</h1>
                        <p className="text-muted">Manage users, assignments, and system configuration.</p>
                    </div>
                </div>

                {/* Stats */}
                {stats && (
                    <div className="grid grid-4" style={{ marginBottom: '2rem' }}>
                        <div className="stat-card">
                            <p className="label">Total Students</p>
                            <p style={{ fontSize: '2.25rem', fontWeight: 800, color: 'var(--primary)' }}>{stats.total_students}</p>
                        </div>
                        <div className="stat-card accent">
                            <p className="label">Total Faculty</p>
                            <p style={{ fontSize: '2.25rem', fontWeight: 800, color: '#f59e0b' }}>{stats.total_faculty}</p>
                        </div>
                        <div className="stat-card success">
                            <p className="label">Total Users</p>
                            <p style={{ fontSize: '2.25rem', fontWeight: 800, color: '#22c55e' }}>{stats.total_users}</p>
                        </div>
                        <div className="stat-card danger">
                            <p className="label">Subjects</p>
                            <p style={{ fontSize: '2.25rem', fontWeight: 800, color: '#ef4444' }}>{stats.total_subjects}</p>
                        </div>
                    </div>
                )}

                {/* Action Buttons */}
                <div className="flex gap-3" style={{ marginBottom: '1.5rem' }}>
                    <button onClick={() => setShowModal('user')}>+ Add User</button>
                    <button className="btn-accent" onClick={() => setShowModal('mentor')}>🔗 Assign Mentor</button>
                    <button className="btn-success" onClick={async () => {
                        try {
                            const data = await analyticsService.generateAlerts();
                            toast.success(data.message);
                        } catch (e) { toast.error('Failed'); }
                    }}>⚡ Generate Alerts</button>
                </div>

                {/* Users Table */}
                <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
                    <div style={{ padding: '1.25rem 1.5rem', borderBottom: '1px solid var(--border)' }}
                        className="flex justify-between items-center">
                        <h2 style={{ margin: 0, border: 'none', paddingBottom: 0 }}>User Management</h2>
                        <div className="flex gap-2">
                            <input type="text" placeholder="Search users..." style={{ width: 200 }}
                                value={filter} onChange={(e) => setFilter(e.target.value)} />
                            <select style={{ width: 140 }} value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)}>
                                <option value="">All Roles</option>
                                <option value="student">Student</option>
                                <option value="mentor">Mentor</option>
                                <option value="lecturer">Lecturer</option>
                                <option value="admin">Admin</option>
                            </select>
                        </div>
                    </div>
                    <table>
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Username</th>
                                <th>Email</th>
                                <th>Role</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredUsers.map(u => (
                                <tr key={u.id}>
                                    <td className="text-muted">#{u.id}</td>
                                    <td style={{ fontWeight: 600 }}>{u.username}</td>
                                    <td className="text-muted">{u.email || '—'}</td>
                                    <td>
                                        <span className={`badge ${u.role === 'admin' ? 'badge-danger' : u.role === 'student' ? 'badge-primary' : 'badge-safe'}`}>
                                            {u.role}
                                        </span>
                                    </td>
                                    <td>
                                        <span className={`badge ${u.is_active ? 'badge-safe' : 'badge-danger'}`}>
                                            {u.is_active ? 'Active' : 'Inactive'}
                                        </span>
                                    </td>
                                    <td>
                                        {u.role !== 'admin' && (
                                            <button className="btn-danger" style={{ fontSize: '0.75rem', padding: '0.3rem 0.6rem' }}
                                                onClick={() => handleDeleteUser(u.id, u.username)}>Delete</button>
                                        )}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    <div style={{ padding: '0.75rem 1.5rem', background: '#f8fafc', textAlign: 'center' }}
                        className="text-sm text-muted">
                        Showing {filteredUsers.length} of {users.length} users
                    </div>
                </div>
            </div>

            {/* Create User Modal */}
            {showModal === 'user' && (
                <div className="modal-overlay" onClick={() => setShowModal(null)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <h2>Create New User</h2>
                        <div className="form-group">
                            <label>Username</label>
                            <input type="text" placeholder="Enter username" value={formData.username}
                                onChange={(e) => setFormData({ ...formData, username: e.target.value })} />
                        </div>
                        <div className="form-group">
                            <label>Email (optional)</label>
                            <input type="email" placeholder="Enter email" value={formData.email}
                                onChange={(e) => setFormData({ ...formData, email: e.target.value })} />
                        </div>
                        <div className="form-group">
                            <label>Password</label>
                            <input type="password" placeholder="Enter password" value={formData.password}
                                onChange={(e) => setFormData({ ...formData, password: e.target.value })} />
                        </div>
                        <div className="form-group">
                            <label>Role</label>
                            <select value={formData.role} onChange={(e) => setFormData({ ...formData, role: e.target.value })}>
                                <option value="student">Student</option>
                                <option value="mentor">Mentor</option>
                                <option value="lecturer">Lecturer</option>
                                <option value="admin">Admin</option>
                            </select>
                        </div>
                        <div className="flex gap-2" style={{ marginTop: '1.5rem' }}>
                            <button onClick={handleCreateUser}
                                disabled={!formData.username || !formData.password}>Create User</button>
                            <button className="btn-secondary" onClick={() => setShowModal(null)}>Cancel</button>
                        </div>
                    </div>
                </div>
            )}

            {/* Assign Mentor Modal */}
            {showModal === 'mentor' && (
                <div className="modal-overlay" onClick={() => setShowModal(null)}>
                    <div className="modal" onClick={e => e.stopPropagation()}>
                        <h2>Assign Mentor to Student</h2>
                        <div className="form-group">
                            <label>Select Student</label>
                            <select value={formData.student_id}
                                onChange={(e) => setFormData({ ...formData, student_id: e.target.value })}>
                                <option value="">Choose a student...</option>
                                {students.map(s => (
                                    <option key={s.id} value={s.id}>
                                        {s.username} (Roll No: {s.enrollment_number || `ID: ${s.id}`})
                                    </option>
                                ))}
                            </select>
                        </div>
                        <div className="form-group">
                            <label>Select Mentor</label>
                            <select value={formData.mentor_id}
                                onChange={(e) => setFormData({ ...formData, mentor_id: e.target.value })}>
                                <option value="">Choose a mentor...</option>
                                {mentors.map(m => (
                                    <option key={m.id} value={m.id}>
                                        {m.username} ({m.employee_id || `ID: ${m.id}`})
                                    </option>
                                ))}
                            </select>
                        </div>
                        <div className="flex gap-2" style={{ marginTop: '1.5rem' }}>
                            <button onClick={handleAssignMentor}
                                disabled={!formData.student_id || !formData.mentor_id}>Assign</button>
                            <button className="btn-secondary" onClick={() => setShowModal(null)}>Cancel</button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

export default AdminDashboard;
