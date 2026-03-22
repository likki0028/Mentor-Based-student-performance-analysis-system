
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import RoleGuard from './components/RoleGuard';
import { Toaster } from 'react-hot-toast';

import Login from './pages/Login';
import AdminDashboard from './pages/AdminDashboard';
import MentorDashboard from './pages/MentorDashboard';
import LecturerDashboard from './pages/LecturerDashboard';
import StudentDashboard from './pages/StudentDashboard';
import StudentDetail from './pages/StudentDetail';
import DetailedStudentReport from './pages/DetailedStudentReport';
import SubjectClassroom from './pages/SubjectClassroom';
import MaterialDetail from './pages/MaterialDetail';
import AssignmentDetail from './pages/AssignmentDetail';
import FacultyClassroom from './pages/FacultyClassroom';
import FacultyAssignmentDetail from './pages/FacultyAssignmentDetail';
import FacultyMaterialDetail from './pages/FacultyMaterialDetail';
import ChangePassword from './pages/ChangePassword';

// Redirect to the correct dashboard based on user role
const RoleRedirect = () => {
    const { user } = useAuth();
    console.log('RoleRedirect: user is', user);
    if (!user) return <Navigate to="/login" replace />;
    if (user.role === 'admin') return <Navigate to="/admin" replace />;
    if (user.role === 'mentor' || user.role === 'both') return <Navigate to="/mentor" replace />;
    if (user.role === 'lecturer') return <Navigate to="/lecturer" replace />;
    return <Navigate to="/student" replace />;
};

function App() {
    console.log('App Rendering');
    return (
        <AuthProvider>
            <Toaster position="top-right" />
            <Router>
                <Routes>
                    <Route path="/login" element={<Login />} />
                    <Route element={<ProtectedRoute />}>
                        <Route path="/change-password" element={<ChangePassword />} />
                        <Route path="/admin" element={<RoleGuard allowedRoles={['admin']}><AdminDashboard /></RoleGuard>} />
                        <Route path="/mentor" element={<RoleGuard allowedRoles={['mentor', 'both']}><MentorDashboard /></RoleGuard>} />
                        <Route path="/mentor/detailed-reports" element={<RoleGuard allowedRoles={['mentor', 'both']}><DetailedStudentReport /></RoleGuard>} />
                        <Route path="/lecturer" element={<RoleGuard allowedRoles={['lecturer', 'both']}><LecturerDashboard /></RoleGuard>} />
                        <Route path="/student" element={<RoleGuard allowedRoles={['student']}><StudentDashboard /></RoleGuard>} />
                        <Route path="/student/detail" element={<RoleGuard allowedRoles={['student', 'mentor', 'both', 'admin', 'lecturer']}><StudentDetail /></RoleGuard>} />
                        <Route path="/student/subject/:id" element={<RoleGuard allowedRoles={['student']}><SubjectClassroom /></RoleGuard>} />
                        <Route path="/student/material/:id" element={<RoleGuard allowedRoles={['student']}><MaterialDetail /></RoleGuard>} />
                        <Route path="/student/assignment/:id" element={<RoleGuard allowedRoles={['student']}><AssignmentDetail /></RoleGuard>} />
                        <Route path="/lecturer/classroom/:subjectId/:sectionId" element={<RoleGuard allowedRoles={['lecturer', 'both']}><FacultyClassroom /></RoleGuard>} />
                        <Route path="/lecturer/assignment/:id" element={<RoleGuard allowedRoles={['lecturer', 'both']}><FacultyAssignmentDetail /></RoleGuard>} />
                        <Route path="/lecturer/material/:id" element={<RoleGuard allowedRoles={['lecturer', 'both']}><FacultyMaterialDetail /></RoleGuard>} />
                        <Route path="/" element={<RoleRedirect />} />
                    </Route>
                </Routes>
            </Router>
        </AuthProvider>
    );
}

export default App;

