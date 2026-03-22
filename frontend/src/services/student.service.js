
import api from './api';

const studentService = {
    getProfile: async () => {
        const response = await api.get('/students/me');
        return response.data;
    },

    getStudentById: async (id) => {
        const response = await api.get(`/students/${id}`);
        return response.data;
    },

    getAttendance: async (id) => {
        const response = await api.get(`/students/${id}/attendance`);
        return response.data;
    },

    getMarks: async (id) => {
        const response = await api.get(`/students/${id}/marks`);
        return response.data;
    },

    getMaterialsBySubject: async (subjectId) => {
        const response = await api.get(`/materials/subject/${subjectId}`);
        return response.data;
    },

    getAssignmentsBySubject: async (subjectId) => {
        const response = await api.get(`/assignments?subject_id=${subjectId}`);
        return response.data;
    },

    uploadAssignment: async (assignmentId, formData) => {
        const response = await api.post(`/assignments/upload/${assignmentId}`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        return response.data;
    }
};

export default studentService;
