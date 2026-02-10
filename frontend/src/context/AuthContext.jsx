
import React, { createContext, useState, useContext, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // TODO: Check if user is logged in (check local storage)
        const token = localStorage.getItem('token');
        const role = localStorage.getItem('role');
        if (token) {
            setUser({ role }); // Mock user
        }
        setLoading(false);
    }, []);

    const login = async (username, password) => {
        // TODO: Call API
        // const response = await api.post('/auth/login', { username, password });
        // localStorage.setItem('token', response.data.access_token);
        // setUser({ role: response.data.role });
        console.log("Login stub called");
        localStorage.setItem('token', 'mock_token');
        // Mock role based on username for demo
        let role = 'student';
        if (username === 'admin') role = 'admin';
        if (username === 'lecturer') role = 'lecturer';
        if (username === 'mentor') role = 'mentor';

        localStorage.setItem('role', role);
        setUser({ role });
        return role;
    };

    const logout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('role');
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, login, logout, loading }}>
            {!loading && children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
