import { sendChatMessage } from '../services/api';
import { useState, useRef, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import ReactMarkdown from 'react-markdown';
import './Chat.css';

// Category display names
const CATEGORY_NAMES = {
    cyber: 'Cyber Crime Laws',
    identity: 'Identity & NADRA Laws',
    provincial: 'KPK Provincial Laws',
    constitutional: 'Constitutional Rights',
    general: 'General Legal Query'
};

function Chat() {
    const [searchParams] = useSearchParams();
    const category = searchParams.get('category') || 'general';
    const categoryName = CATEGORY_NAMES[category] || 'Legal Assistant';

    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [showHistory, setShowHistory] = useState(false);
    const [chatHistory, setChatHistory] = useState([
        { id: 1, title: 'Article 25 Discussion', date: 'Today' },
        { id: 2, title: 'Fundamental Rights', date: 'Yesterday' },
        { id: 3, title: 'Constitutional Amendments', date: 'Dec 28' },
    ]);
    const messagesEndRef = useRef(null);
    const navigate = useNavigate();
    const { user, profile, signOut } = useAuth();

    // Get display name and initial from profile
    const displayName = profile?.username || profile?.full_name || user?.email?.split('@')[0] || 'User';
    const userInitial = profile?.full_name?.charAt(0).toUpperCase() ||
        profile?.username?.charAt(0).toUpperCase() ||
        user?.email?.charAt(0).toUpperCase() || 'U';

    // Auto-scroll to bottom when new messages arrive
    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!inputValue.trim() || isLoading) return;

        const userMessage = {
            id: Date.now(),
            type: 'user',
            content: inputValue.trim(),
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        setInputValue('');
        setIsLoading(true);

        try {
            // Call the FastAPI backend with category filter
            const result = await sendChatMessage(inputValue.trim(), true, category);

            const botMessage = {
                id: Date.now() + 1,
                type: 'bot',
                content: result.response,
                timestamp: new Date(),
                sources: result.sources || []
            };
            setMessages(prev => [...prev, botMessage]);
        } catch (error) {
            console.error('Error:', error);
            const errorMessage = {
                id: Date.now() + 1,
                type: 'bot',
                content: 'Sorry, I encountered an error. Please try again.',
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
        }
    };

    const handleNewChat = () => {
        setMessages([]);
        setShowHistory(false);
    };

    const handleLogout = async () => {
        try {
            await signOut();
            navigate('/login');
        } catch (error) {
            console.error('Logout error:', error);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage(e);
        }
    };

    const handleSelectChat = (chatId) => {
        setShowHistory(false);
        console.log('Selected chat:', chatId);
    };

    const isNewChat = messages.length === 0;

    return (
        <div className="chat-layout">
            {/* Sidebar */}
            <aside className="sidebar">
                <div className="sidebar-top">
                    <button className="sidebar-btn" title="Back to Dashboard" onClick={() => navigate('/dashboard')}>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                            <polyline points="9 22 9 12 15 12 15 22"></polyline>
                        </svg>
                    </button>
                    <button className="sidebar-btn" title="New Chat" onClick={handleNewChat}>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <line x1="12" y1="5" x2="12" y2="19"></line>
                            <line x1="5" y1="12" x2="19" y2="12"></line>
                        </svg>
                    </button>
                    <button
                        className={`sidebar-btn ${showHistory ? 'active' : ''}`}
                        title="Chat History"
                        onClick={() => setShowHistory(!showHistory)}
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <circle cx="12" cy="12" r="10"></circle>
                            <polyline points="12 6 12 12 16 14"></polyline>
                        </svg>
                    </button>
                </div>
                <div className="sidebar-bottom">
                    <button className="user-avatar" title={`Logout (${displayName})`} onClick={handleLogout}>
                        {userInitial}
                    </button>
                </div>
            </aside>

            {/* Chat History Panel */}
            {showHistory && (
                <div className="history-panel">
                    <div className="history-header">
                        <h3>Chat History</h3>
                        <button className="close-history" onClick={() => setShowHistory(false)}>×</button>
                    </div>
                    <div className="history-list">
                        {chatHistory.map(chat => (
                            <div
                                key={chat.id}
                                className="history-item"
                                onClick={() => handleSelectChat(chat.id)}
                            >
                                <div className="history-icon">💬</div>
                                <div className="history-info">
                                    <span className="history-title">{chat.title}</span>
                                    <span className="history-date">{chat.date}</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Main Content */}
            <main className="main-content">
                {isNewChat ? (
                    <div className="welcome-screen">
                        <div className="welcome-message">
                            <span className="welcome-icon">⚖️</span>
                            <h1>Hey there, {displayName}</h1>
                        </div>
                        <div className="welcome-subtitle">
                            <p className="category-label">{categoryName}</p>
                            <p>Ask me anything about this legal topic</p>
                        </div>
                    </div>
                ) : (
                    <div className="messages-container">
                        <div className="messages-list">
                            {messages.map((message) => (
                                <div
                                    key={message.id}
                                    className={`message ${message.type === 'user' ? 'user-message' : 'bot-message'}`}
                                >
                                    {message.type === 'bot' && (
                                        <div className="message-avatar">⚖️</div>
                                    )}
                                    {message.type === 'user' && (
                                        <div className="message-avatar user-msg-avatar">{userInitial}</div>
                                    )}
                                    <div className="message-content">
                                        {message.type === 'bot' ? (
                                            <ReactMarkdown>{message.content}</ReactMarkdown>
                                        ) : (
                                            <p>{message.content}</p>
                                        )}
                                    </div>
                                </div>
                            ))}

                            {isLoading && (
                                <div className="message bot-message">
                                    <div className="message-avatar">⚖️</div>
                                    <div className="message-content typing">
                                        <span className="typing-dot"></span>
                                        <span className="typing-dot"></span>
                                        <span className="typing-dot"></span>
                                    </div>
                                </div>
                            )}

                            <div ref={messagesEndRef} />
                        </div>
                    </div>
                )}

                {/* Input Area */}
                <div className="input-wrapper">
                    <div className="input-container">
                        <form onSubmit={handleSendMessage} className="input-form">
                            <textarea
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                onKeyPress={handleKeyPress}
                                placeholder="How can I help you today?"
                                disabled={isLoading}
                                rows={1}
                            />
                            <button type="submit" disabled={isLoading || !inputValue.trim()} className="send-btn">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                                    <line x1="12" y1="19" x2="12" y2="5"></line>
                                    <polyline points="5 12 12 5 19 12"></polyline>
                                </svg>
                            </button>
                        </form>
                    </div>
                    <p className="disclaimer">
                        PakLaw ChatBot provides general legal information only.
                    </p>
                </div>
            </main>
        </div>
    );
}

export default Chat;
