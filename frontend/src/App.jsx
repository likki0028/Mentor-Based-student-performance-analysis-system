
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import RoleGuard from './components/RoleGuard';

import Login from './pages/Login';
import AdminDashboard from './pages/AdminDashboard';
import MentorDashboard from './pages/MentorDashboard';
import LecturerDashboard from './pages/LecturerDashboard';
import StudentDashboard from './pages/StudentDashboard';
import StudentDetail from './pages/StudentDetail';
import ChangePassword from './pages/ChangePassword';

function App() {
    return (
        <AuthProvider>
            <Router>
                <Routes>
                    <Route path="/login" element={<Login />} />

                    <Route element={<ProtectedRoute />}>
                        <Route path="/change-password" element={<ChangePassword />} />

                        <Route path="/admin" element={
                            <RoleGuard allowedRoles={['admin']}>
                                <AdminDashboard />
                            </RoleGuard>
                        } />

                        <Route path="/mentor" element={
                            <RoleGuard allowedRoles={['mentor', 'both']}>
                                <MentorDashboard />
                            </RoleGuard>
                        } />

                        <Route path="/lecturer" element={
                            <RoleGuard allowedRoles={['lecturer', 'both']}>
                                <LecturerDashboard />
                            </RoleGuard>
                        } />

                        <Route path="/student" element={
                            <RoleGuard allowedRoles={['student']}>
                                <StudentDashboard />
                            </RoleGuard>
                        } />

                        <Route path="/student/detail" element={
                            <RoleGuard allowedRoles={['student', 'mentor', 'both', 'admin']}>
                                <StudentDetail />
                            </RoleGuard>
                        } />

                        <Route path="/" element={<Navigate to="/student" replace />} />
                    </Route>
                </Routes>
            </Router>
        </AuthProvider>
    );
}

export default App;
