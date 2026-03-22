
import api from './api';

const academicService = {
    getSections: async () => {
        const response = await api.get('/admin/sections');
        return response.data;
    },

    getSubjects: async () => {
        const response = await api.get('/admin/subjects');
        return response.data;
    },

    getAssignments: async (subjectId = null) => {
        const url = subjectId ? `/assignments?subject_id=${subjectId}` : '/assignments/';
        const response = await api.get(url);
        return response.data;
    },

    getMaterials: async (subjectId, sectionId = null) => {
        const url = sectionId 
            ? `/materials/subject/${subjectId}?section_id=${sectionId}` 
            : `/materials/subject/${subjectId}`;
        const response = await api.get(url);
        return response.data;
    }
};

export default academicService;
