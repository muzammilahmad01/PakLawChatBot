import { sendChatMessage } from '../services/api';
import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { supabase } from '../lib/supabase';
import ReactMarkdown from 'react-markdown';
import './Chat.css';

// Category display names and icons
const CATEGORIES = {
    cyber: { name: 'Cyber Crime Laws', icon: '💻', gradient: 'linear-gradient(135deg, #3b82f6, #6366f1)' },
    criminal: { name: 'Criminal Laws', icon: '⚔️', gradient: 'linear-gradient(135deg, #8b5cf6, #a855f7)' },
    Family: { name: 'Family Laws', icon: '👨‍👩‍👧', gradient: 'linear-gradient(135deg, #10b981, #14b8a6)' },
    Property: { name: 'Property & Land Laws', icon: '🏠', gradient: 'linear-gradient(135deg, #f59e0b, #f97316)' },
    labour: { name: 'Labour Laws', icon: '👷', gradient: 'linear-gradient(135deg, #06b6d4, #0891b2)' },
    constitutional: { name: 'Constitutional Rights', icon: '📜', gradient: 'linear-gradient(135deg, #c9a227, #f0d55b)' },
    general: { name: 'General Legal Query', icon: '⚖️', gradient: 'linear-gradient(135deg, #ef4444, #f97316)' }
};

// Suggested prompts per category
const SUGGESTED_PROMPTS = {
    cyber: [
        'What is PECA and its penalties?',
        'How to report a cyber crime?',
        'Data protection laws in Pakistan'
    ],
    criminal: [
        'What is the punishment for theft?',
        'Explain bail procedures in Pakistan',
        'What are bailable vs non-bailable offences?'
    ],
    Family: [
        'What are marriage laws in Pakistan?',
        'Explain khula procedure for women',
        'Child custody rights after divorce'
    ],
    Property: [
        'How to transfer property in Punjab?',
        'What is mutation of land records?',
        'Explain inheritance laws in Islam'
    ],
    labour: [
        'What is minimum wage in Pakistan?',
        'Employee termination rights',
        'Workplace harassment laws'
    ],
    constitutional: [
        'What are fundamental rights in Pakistan?',
        'Explain Article 25 of Constitution',
        'Right to freedom of speech'
    ],
    general: [
        'How to file an FIR in Pakistan?',
        'What is the court system structure?',
        'Consumer protection laws in Pakistan'
    ]
};

function Chat() {
    const [searchParams] = useSearchParams();
    const category = searchParams.get('category') || 'general';
    const catInfo = CATEGORIES[category] || CATEGORIES.general;

    const [messages, setMessages] = useState([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [showHistory, setShowHistory] = useState(false);
    const [chatHistory, setChatHistory] = useState([]);
    const [currentConversationId, setCurrentConversationId] = useState(null);
    const [historyLoading, setHistoryLoading] = useState(false);

    const messagesEndRef = useRef(null);
    const textareaRef = useRef(null);
    const navigate = useNavigate();
    const { user, profile, signOut } = useAuth();

    const displayName = profile?.username || profile?.full_name || user?.email?.split('@')[0] || 'User';
    const userInitial = profile?.full_name?.charAt(0).toUpperCase() ||
        profile?.username?.charAt(0).toUpperCase() ||
        user?.email?.charAt(0).toUpperCase() || 'U';

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 150) + 'px';
        }
    }, [inputValue]);

    // ========== DATABASE FUNCTIONS ==========

    // Load chat history (conversations list) from Supabase
    const loadChatHistory = useCallback(async () => {
        if (!user) return;
        setHistoryLoading(true);
        try {
            const { data, error } = await supabase
                .from('conversations')
                .select('id, title, category, created_at, updated_at')
                .eq('user_id', user.id)
                .order('updated_at', { ascending: false })
                .limit(50);

            if (error) throw error;

            // Format the dates for display
            const formatted = (data || []).map(conv => ({
                ...conv,
                displayDate: formatDate(conv.updated_at)
            }));
            setChatHistory(formatted);
        } catch (error) {
            console.error('Error loading chat history:', error);
        } finally {
            setHistoryLoading(false);
        }
    }, [user]);

    // Load chat history on mount
    useEffect(() => {
        loadChatHistory();
    }, [loadChatHistory]);

    // Format date for sidebar display
    const formatDate = (dateString) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffDays === 0) return 'Today';
        if (diffDays === 1) return 'Yesterday';
        if (diffDays < 7) return `${diffDays} days ago`;
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    };

    // Create a new conversation in the database
    const createConversation = async (firstMessage) => {
        if (!user) return null;
        try {
            // Generate a title from the first message (first 50 chars)
            const title = firstMessage.length > 50
                ? firstMessage.substring(0, 50) + '...'
                : firstMessage;

            const { data, error } = await supabase
                .from('conversations')
                .insert({
                    user_id: user.id,
                    title: title,
                    category: category,
                })
                .select()
                .single();

            if (error) throw error;
            return data;
        } catch (error) {
            console.error('Error creating conversation:', error);
            return null;
        }
    };

    // Save a message to the database and return the saved message
    const saveMessage = async (conversationId, role, content) => {
        if (!conversationId) return null;
        try {
            const { data, error } = await supabase
                .from('messages')
                .insert({
                    conversation_id: conversationId,
                    role: role,
                    content: content,
                })
                .select('id')
                .single();

            if (error) throw error;

            // Update the conversation's updated_at timestamp
            await supabase
                .from('conversations')
                .update({ updated_at: new Date().toISOString() })
                .eq('id', conversationId);

            return data;
        } catch (error) {
            console.error('Error saving message:', error);
            return null;
        }
    };

    // Load messages for a specific conversation
    const loadConversation = async (conversationId) => {
        try {
            const { data, error } = await supabase
                .from('messages')
                .select('id, role, content, feedback, created_at')
                .eq('conversation_id', conversationId)
                .order('created_at', { ascending: true });

            if (error) throw error;

            const formattedMessages = (data || []).map(msg => ({
                id: msg.id,
                type: msg.role,
                content: msg.content,
                feedback: msg.feedback || null,
                timestamp: new Date(msg.created_at)
            }));

            setMessages(formattedMessages);
            setCurrentConversationId(conversationId);
            setShowHistory(false);
        } catch (error) {
            console.error('Error loading conversation:', error);
        }
    };

    // Delete a conversation
    const deleteConversation = async (e, conversationId) => {
        e.stopPropagation(); // Don't trigger the click on the history item
        try {
            const { error } = await supabase
                .from('conversations')
                .delete()
                .eq('id', conversationId);

            if (error) throw error;

            // If we deleted the current conversation, clear the chat
            if (currentConversationId === conversationId) {
                setMessages([]);
                setCurrentConversationId(null);
            }

            // Refresh history
            await loadChatHistory();
        } catch (error) {
            console.error('Error deleting conversation:', error);
        }
    };

    // Submit feedback (thumbs up / down) on a bot message
    const handleFeedback = async (messageId, rating) => {
        try {
            // Update the message's feedback in the database
            const { error } = await supabase
                .from('messages')
                .update({ feedback: rating })
                .eq('id', messageId);

            if (error) throw error;

            // Update the local state so the UI reflects the change
            setMessages(prev => prev.map(msg =>
                msg.id === messageId ? { ...msg, feedback: rating } : msg
            ));
        } catch (error) {
            console.error('Error saving feedback:', error);
        }
    };

    // ========== UI HANDLERS ==========

    const handleSendMessage = async (e, promptText = null) => {
        e?.preventDefault();
        const messageText = promptText || inputValue.trim();
        if (!messageText || isLoading) return;

        let convId = currentConversationId;

        // If this is a new chat, create a conversation first
        if (!convId) {
            const newConv = await createConversation(messageText);
            if (newConv) {
                convId = newConv.id;
                setCurrentConversationId(convId);
            }
        }

        const userMessage = {
            id: Date.now(),
            type: 'user',
            content: messageText,
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        setInputValue('');
        setIsLoading(true);

        // Save user message to database
        await saveMessage(convId, 'user', messageText);

        try {
            const result = await sendChatMessage(messageText, true, category);
            // Save bot response to database first to get the real ID
            const savedMsg = await saveMessage(convId, 'bot', result.response);

            const botMessage = {
                id: savedMsg?.id || Date.now() + 1,
                type: 'bot',
                content: result.response,
                feedback: null,
                timestamp: new Date(),
                sources: result.sources || []
            };
            setMessages(prev => [...prev, botMessage]);

            // Refresh chat history in sidebar
            await loadChatHistory();

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
        setCurrentConversationId(null);
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

    const handleSelectChat = (conversationId) => {
        loadConversation(conversationId);
    };

    const handlePromptClick = (prompt) => {
        handleSendMessage(null, prompt);
    };

    const isNewChat = messages.length === 0;
    const prompts = SUGGESTED_PROMPTS[category] || SUGGESTED_PROMPTS.general;

    return (
        <div className="chat-layout">
            {/* Sidebar */}
            <aside className="sidebar">
                <div className="sidebar-top">
                    <button className="sidebar-btn" title="Back to Dashboard" onClick={() => navigate('/dashboard')}>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                            <polyline points="9 22 9 12 15 12 15 22"></polyline>
                        </svg>
                    </button>
                    <button className="sidebar-btn" title="New Chat" onClick={handleNewChat}>
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <line x1="12" y1="5" x2="12" y2="19"></line>
                            <line x1="5" y1="12" x2="19" y2="12"></line>
                        </svg>
                    </button>
                    <button
                        className={`sidebar-btn ${showHistory ? 'active' : ''}`}
                        title="Chat History"
                        onClick={() => setShowHistory(!showHistory)}
                    >
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
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
                        {historyLoading ? (
                            <div className="history-loading">Loading chats...</div>
                        ) : chatHistory.length === 0 ? (
                            <div className="history-empty">
                                <p>No conversations yet</p>
                                <span>Start a new chat to see it here</span>
                            </div>
                        ) : (
                            chatHistory.map(conv => (
                                <div
                                    key={conv.id}
                                    className={`history-item ${currentConversationId === conv.id ? 'active' : ''}`}
                                    onClick={() => handleSelectChat(conv.id)}
                                >
                                    <div className="history-icon">
                                        {CATEGORIES[conv.category]?.icon || '💬'}
                                    </div>
                                    <div className="history-info">
                                        <span className="history-title">{conv.title}</span>
                                        <span className="history-date">{conv.displayDate}</span>
                                    </div>
                                    <button
                                        className="history-delete"
                                        title="Delete conversation"
                                        onClick={(e) => deleteConversation(e, conv.id)}
                                    >
                                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <polyline points="3 6 5 6 21 6"></polyline>
                                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                        </svg>
                                    </button>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            )}

            {/* Main Content */}
            <main className="main-content">
                {/* Top bar with category info */}
                <div className="chat-topbar">
                    <div className="topbar-category" style={{ background: catInfo.gradient }}>
                        <span>{catInfo.icon}</span>
                        <span>{catInfo.name}</span>
                    </div>
                </div>

                {isNewChat ? (
                    <div className="welcome-screen">
                        <div className="welcome-content">
                            <div className="welcome-badge" style={{ background: catInfo.gradient }}>
                                <span className="welcome-badge-icon">{catInfo.icon}</span>
                            </div>
                            <h1 className="welcome-heading">
                                Hello, <span className="welcome-name">{displayName}</span>
                            </h1>
                            <p className="welcome-sub">How can I assist you with <strong>{catInfo.name}</strong> today?</p>

                            <div className="suggested-prompts">
                                {prompts.map((prompt, index) => (
                                    <button
                                        key={index}
                                        className="prompt-card"
                                        onClick={() => handlePromptClick(prompt)}
                                    >
                                        <span className="prompt-icon">💡</span>
                                        <span className="prompt-text">{prompt}</span>
                                        <svg className="prompt-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <polyline points="9 18 15 12 9 6"></polyline>
                                        </svg>
                                    </button>
                                ))}
                            </div>
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
                                    <div className={`message-avatar ${message.type === 'user' ? 'user-msg-avatar' : 'bot-msg-avatar'}`}>
                                        {message.type === 'bot' ? '⚖️' : userInitial}
                                    </div>
                                    <div className="message-body">
                                        <span className="message-sender">
                                            {message.type === 'bot' ? 'PakLaw AI' : displayName}
                                        </span>
                                        <div className="message-content">
                                            {message.type === 'bot' ? (
                                                <ReactMarkdown>{message.content}</ReactMarkdown>
                                            ) : (
                                                <p>{message.content}</p>
                                            )}
                                        </div>
                                        {/* Feedback buttons for bot messages */}
                                        {message.type === 'bot' && (
                                            <div className="feedback-buttons">
                                                <button
                                                    className={`feedback-btn ${message.feedback === 'up' ? 'active-up' : ''}`}
                                                    onClick={() => handleFeedback(message.id, message.feedback === 'up' ? null : 'up')}
                                                    title="Helpful"
                                                >
                                                    <svg width="16" height="16" viewBox="0 0 24 24" fill={message.feedback === 'up' ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                        <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
                                                    </svg>
                                                </button>
                                                <button
                                                    className={`feedback-btn ${message.feedback === 'down' ? 'active-down' : ''}`}
                                                    onClick={() => handleFeedback(message.id, message.feedback === 'down' ? null : 'down')}
                                                    title="Not helpful"
                                                >
                                                    <svg width="16" height="16" viewBox="0 0 24 24" fill={message.feedback === 'down' ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                        <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"></path>
                                                    </svg>
                                                </button>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}

                            {isLoading && (
                                <div className="message bot-message">
                                    <div className="message-avatar bot-msg-avatar">⚖️</div>
                                    <div className="message-body">
                                        <span className="message-sender">PakLaw AI</span>
                                        <div className="message-content typing-indicator">
                                            <div className="typing-dots">
                                                <span className="typing-dot"></span>
                                                <span className="typing-dot"></span>
                                                <span className="typing-dot"></span>
                                            </div>
                                            <span className="typing-text">Analyzing legal documents...</span>
                                        </div>
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
                                ref={textareaRef}
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                onKeyDown={handleKeyPress}
                                placeholder={`Ask about ${catInfo.name.toLowerCase()}...`}
                                disabled={isLoading}
                                rows={1}
                            />
                            <button type="submit" disabled={isLoading || !inputValue.trim()} className="send-btn">
                                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                    <line x1="22" y1="2" x2="11" y2="13"></line>
                                    <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                                </svg>
                            </button>
                        </form>
                    </div>
                    <p className="disclaimer">
                        ⚖️ PakLaw AI provides general legal information only. Always consult a qualified lawyer.
                    </p>
                </div>
            </main>
        </div>
    );
}

export default Chat;
