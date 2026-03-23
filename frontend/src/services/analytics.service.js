
import api from './api';

const analyticsService = {
    getStudentAnalytics: async (id) => {
        const response = await api.get(`/analytics/student/${id}?t=${Date.now()}`);
        return response.data;
    },

    predictRisk: async (id) => {
        const response = await api.get(`/analytics/predict/${id}`);
        return response.data;
    },

    predictGPA: async (id) => {
        const response = await api.get(`/analytics/predict-gpa/${id}`);
        return response.data;
    },

    generateAlerts: async () => {
        const response = await api.post('/alerts/generate');
        return response.data;
    },

    getAdminStats: async () => {
        const response = await api.get('/admin/stats');
        return response.data;
    }
};

export default analyticsService;
