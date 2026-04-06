import api from './api';

const extracurricularService = {
    getMyCertificates: () => api.get('/extracurricular/me'),
    
    getStudentCertificates: (studentId) => api.get(`/extracurricular/student/${studentId}`),
    
    uploadCertificate: (formData) => {
        return api.post('/extracurricular/', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        });
    },
    
    deleteCertificate: (id) => api.delete(`/extracurricular/${id}`)
};

export default extracurricularService;
