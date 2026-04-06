import React, { useState, useEffect, useRef } from 'react';
import chatbotService from '../services/chatbot.service';
import './Chatbot.css';

const Chatbot = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState([
        { text: "Hello! I'm your Academic Assistant. How can I help you today?", isBot: true }
    ]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        if (isOpen) {
            scrollToBottom();
        }
    }, [messages, isOpen]);

    const handleSend = async (e) => {
        e.preventDefault();
        const msg = input.trim();
        if (!msg) return;

        setMessages(prev => [...prev, { text: msg, isUser: true }]);
        setInput('');
        setIsLoading(true);

        try {
            const res = await chatbotService.ask(msg);
            setMessages(prev => [...prev, { text: res.data.reply, isBot: true }]);
        } catch (err) {
            setMessages(prev => [...prev, { text: "Sorry, I'm having trouble connecting right now. 😕", isBot: true }]);
        } finally {
            setIsLoading(false);
        }
    };

    const quickActions = [
        "My Attendance",
        "Risk Status",
        "My Marks",
        "Pending Assignments"
    ];

    return (
        <div className={`chatbot-wrapper ${isOpen ? 'open' : ''}`}>
            {/* Chat Window */}
            {isOpen && (
                <div className="chat-window">
                    <div className="chat-header">
                        <h3>🎓 Academic Assistant</h3>
                        <button className="close-btn" onClick={() => setIsOpen(false)}>×</button>
                    </div>
                    
                    <div className="chat-messages">
                        {messages.map((msg, i) => (
                            <div key={i} className={`message ${msg.isBot ? 'bot' : 'user'}`}>
                                <div className="message-content">
                                    {msg.text.split('\n').map((line, li) => (
                                        <p key={li}>{line}</p>
                                    ))}
                                </div>
                            </div>
                        ))}
                        {isLoading && (
                            <div className="message bot">
                                <div className="message-content typing">
                                    <span>.</span><span>.</span><span>.</span>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    <div className="chat-footer">
                        {messages.length < 5 && (
                            <div className="quick-actions">
                                {quickActions.map((action, i) => (
                                    <button 
                                        key={i} 
                                        onClick={() => { setInput(action); }}
                                        className="quick-btn"
                                    >
                                        {action}
                                    </button>
                                ))}
                            </div>
                        )}
                        <form onSubmit={handleSend} className="chat-input-area">
                            <input 
                                type="text" 
                                placeholder="Type your question..." 
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                disabled={isLoading}
                            />
                            <button type="submit" disabled={isLoading || !input.trim()}>
                                ➜
                            </button>
                        </form>
                    </div>
                </div>
            )}

            {/* Floating Bubble */}
            <button 
                className={`chat-bubble ${isOpen ? 'active' : ''}`} 
                onClick={() => setIsOpen(!isOpen)}
            >
                {isOpen ? '✕' : '💬'}
            </button>
        </div>
    );
};

export default Chatbot;
