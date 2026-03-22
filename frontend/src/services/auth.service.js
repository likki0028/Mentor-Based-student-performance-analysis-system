
import api from './api';

const authService = {
    login: async (username, password) => {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);
        const response = await api.post('/auth/login', formData);
        return response.data;
    },

    register: async (userData) => {
        const response = await api.post('/auth/register', userData);
        return response.data;
    },

    assignMentor: async (studentId, mentorId) => {
        const response = await api.post('/admin/assign-mentor', {
            student_id: studentId,
            mentor_id: mentorId
        });
        return response.data;
    },

    changePassword: async (userId, currentPassword, newPassword) => {
        const response = await api.post('/auth/change-password', null, {
            params: { current_password: currentPassword, new_password: newPassword }
        });
        return response.data;
    },

    logout: () => {
        localStorage.removeItem('token');
        localStorage.removeItem('role');
        localStorage.removeItem('username');
        if (window.location.pathname !== '/login') {
            window.location.href = '/login';
        }
    },

    getUsers: async () => {
        const response = await api.get('/admin/users');
        return response.data;
    },

    deleteUser: async (id) => {
        const response = await api.delete(`/admin/users/${id}`);
        return response.data;
    }
};

export default authService;
