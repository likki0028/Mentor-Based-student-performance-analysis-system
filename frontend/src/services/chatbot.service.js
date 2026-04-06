import api from './api';

const chatbotService = {
    ask: (message) => api.post('/chatbot/ask', { message })
};

export default chatbotService;
