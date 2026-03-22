
import api from './api';

const facultyService = {
    getDashboardStats: async () => {
        const response = await api.get('/faculty/dashboard');
        return response.data;
    },

    getMyStudents: async (params = {}) => {
        const response = await api.get('/faculty/my-students', { params });
        return response.data;
    },

    getMySubjects: async () => {
        const response = await api.get('/faculty/my-subjects');
        return response.data;
    },

    addRemark: async (remarkData) => {
        const response = await api.post('/faculty/remarks', remarkData);
        return response.data;
    },

    getRemarks: async (studentId) => {
        const response = await api.get(`/faculty/remarks/${studentId}`);
        return response.data;
    },

    markAttendance: async (records) => {
        const response = await api.post('/attendance/mark', { records });
        return response.data;
    },

    addMarks: async (marks) => {
        const response = await api.post('/marks/', { marks });
        return response.data;
    },

    createAssignment: async (assignmentData) => {
        const response = await api.post('/assignments/', assignmentData);
        return response.data;
    },

    uploadMaterial: async (formData) => {
        const response = await api.post('/materials/', formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        return response.data;
    },

    getSubmissionsByAssignment: async (id) => {
        const response = await api.get(`/assignments/${id}/submissions`);
        return response.data;
    },

    gradeSubmission: async (id, grade) => {
        const response = await api.post(`/faculty/submissions/${id}/grade`, { grade });
        return response.data;
    },

    getRemarks: async (studentId) => {
        const response = await api.get(`/faculty/remarks/${studentId}`);
        return response.data;
    },

    getAssignmentDetail: async (id) => {
        const response = await api.get(`/assignments/${id}`);
        return response.data;
    },

    deleteAssignment: async (id) => {
        const response = await api.delete(`/assignments/${id}`);
        return response.data;
    },

    updateAssignment: async (id, data) => {
        const response = await api.put(`/assignments/${id}`, data);
        return response.data;
    },

    getAllAssignments: async () => {
        const response = await api.get('/assignments/');
        return response.data;
    }
};

export default facultyService;
