
import axios from 'axios';

const api = axios.create({
    baseURL: 'http://localhost:8000/api/v1', // TODO: Load from env
});

// TODO: Add request interceptor to attach JWT token
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export default api;
