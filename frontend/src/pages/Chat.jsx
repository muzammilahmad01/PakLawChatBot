import { sendChatMessage } from '../services/api';
import { useState, useRef, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { supabase } from '../lib/supabase';
import ReactMarkdown from 'react-markdown';
import toast, { Toaster } from 'react-hot-toast';
import html2pdf from 'html2pdf.js';
import logo from '../assets/logo.jpeg';
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

// Follow-up suggestions per category (shown after bot response)
const FOLLOW_UP_SUGGESTIONS = {
    cyber: [
        'What are the penalties under PECA?',
        'How to file a complaint with FIA?',
        'What is online defamation law?',
        'How does data privacy work in Pakistan?',
        'What is the punishment for hacking?',
        'Can social media posts lead to arrest?'
    ],
    criminal: [
        'What is the difference between cognizable and non-cognizable offences?',
        'How does the bail process work?',
        'What is culpable homicide?',
        'Explain the role of public prosecutor',
        'What are the rights of an accused person?',
        'How to get an FIR registered?'
    ],
    Family: [
        'What is the waiting period (iddat) after divorce?',
        'How is mehr (dower) calculated?',
        'What are grandparent visitation rights?',
        'How does Islamic inheritance distribution work?',
        'Can a wife claim maintenance after divorce?',
        'What is the procedure for nikah registration?'
    ],
    Property: [
        'What documents are needed for property transfer?',
        'How to check property ownership records?',
        'What is stamp duty on property in Punjab?',
        'How to resolve a land dispute?',
        'What is the role of patwari?',
        'Explain the concept of adverse possession'
    ],
    labour: [
        'What are overtime pay regulations?',
        'How to file a complaint with labour court?',
        'What is the social security scheme?',
        'What are maternity leave rights?',
        'Can an employer terminate without notice?',
        'What is the Workers Welfare Fund?'
    ],
    constitutional: [
        'What is the role of Supreme Court?',
        'Explain judicial review in Pakistan',
        'What are directive principles of policy?',
        'How can fundamental rights be suspended?',
        'What is Article 184(3)?',
        'Explain the amendment process'
    ],
    general: [
        'What is the hierarchy of courts in Pakistan?',
        'How to hire a lawyer in Pakistan?',
        'What is alternative dispute resolution?',
        'How long do court cases take?',
        'What is the role of ombudsman?',
        'Explain the difference between civil and criminal cases'
    ]
};

// Format timestamp for display
const formatTimestamp = (date) => {
    if (!date) return '';
    const d = date instanceof Date ? date : new Date(date);
    return d.toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
    });
};

// Get random follow-up suggestions (excluding current question)
const getFollowUpSuggestions = (category, currentQuestion, count = 3) => {
    const pool = FOLLOW_UP_SUGGESTIONS[category] || FOLLOW_UP_SUGGESTIONS.general;
    const filtered = pool.filter(q => q.toLowerCase() !== currentQuestion?.toLowerCase());
    const shuffled = [...filtered].sort(() => Math.random() - 0.5);
    return shuffled.slice(0, count);
};

/**
 * Convert legal references (Article X, Section Y) in the model's response
 * into clickable Google Search links so users can verify the law.
 * 
 * Smart context: When a Section/Article has no abbreviation (PPC, CrPC, etc.),
 * the function scans nearby text for the full Act/Ordinance name and includes
 * it in the Google search query for accurate results.
 * 
 * Example: "Section 19" near "Extradition Act, 1972" will search for
 *          "Section 19 Extradition Act 1972 Pakistan" instead of just
 *          "Section 19 Pakistan law".
 */
const linkifyLegalReferences = (text) => {
    if (!text) return text;

    const pattern = /(\*{2})?((?:Articles?|Sections?)\s+\d+[A-Z]?(?:\s*\(\d+\))?(?:[-–]\d+[A-Z]?)?)(\s+(?:PPC|CrPC|CRPC|CPC|PECA|MFLO|TPA|PLA|PO|NAB))?(\*{2})?/gi;

    // Don't process text inside existing markdown links [...](...) 
    const linkPattern = /(\[[^\]]*\]\([^)]*\))/g;
    const parts = text.split(linkPattern);

    const processed = parts.map(part => {
        // If this part is already a markdown link, skip it
        if (linkPattern.test(part)) {
            linkPattern.lastIndex = 0;
            return part;
        }

        return part.replace(pattern, (match, openBold, coreRef, lawAbbrev, closeBold, offset) => {
            const fullRef = (coreRef + (lawAbbrev || '')).trim();
            let searchContext;

            if (lawAbbrev) {
                // Already has a clear abbreviation like PPC, CrPC — use as is
                searchContext = fullRef + ' Pakistan law';
            } else {
                // No abbreviation — search surrounding text for Act/Ordinance/Code name
                const windowStart = Math.max(0, offset - 200);
                const windowEnd = Math.min(part.length, offset + match.length + 200);
                const rawWindow = part.substring(windowStart, windowEnd);
                // Strip markdown bold markers for cleaner regex matching
                const cleanWindow = rawWindow.replace(/\*{2}/g, '');

                // Match full Act/Ordinance/Code names with optional year
                // e.g., "Extradition Act, 1972", "Security of Pakistan Act, 1952",
                //        "Code of Criminal Procedure, 1898"
                const actRegex = /([A-Z][a-zA-Z\s]+?(?:Act|Ordinance|Code|Rules|Order|Regulation)(?:,?\s*\d{4})?)/g;
                const actMatches = [...cleanWindow.matchAll(actRegex)];

                if (actMatches.length > 0) {
                    // Find the Act name closest to our Section/Article reference
                    const approxRefPos = offset - windowStart;
                    let closestAct = actMatches[0][1].trim();
                    let minDist = Infinity;

                    for (const am of actMatches) {
                        const dist = Math.abs(am.index - approxRefPos);
                        if (dist < minDist) {
                            minDist = dist;
                            closestAct = am[1].trim();
                        }
                    }
                    searchContext = `${fullRef} ${closestAct} Pakistan`;
                } else {
                    searchContext = fullRef + ' Pakistan law';
                }
            }

            const searchQuery = encodeURIComponent(searchContext);
            const googleUrl = `https://www.google.com/search?q=${searchQuery}`;

            // Keep bold formatting if it was bold originally
            if (openBold && closeBold) {
                return `[**${fullRef}**](${googleUrl})`;
            }
            return `[${fullRef}](${googleUrl})`;
        });
    });

    return processed.join('');
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
    const [expandedSources, setExpandedSources] = useState({});
    const [lastUserQuestion, setLastUserQuestion] = useState('');

    const messagesEndRef = useRef(null);
    const textareaRef = useRef(null);
    const abortControllerRef = useRef(null);
    const navigate = useNavigate();

    const stopGenerating = () => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }
    };
    const { user, profile, signOut } = useAuth();
    const { theme, toggleTheme } = useTheme();

    const displayName = profile?.full_name || profile?.username || user?.email?.split('@')[0] || 'User';
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

    // ========== UTILITY FUNCTIONS ==========

    const handleCopyMessage = async (content) => {
        try {
            await navigator.clipboard.writeText(content);
            toast.success('Copied to clipboard!', {
                duration: 2000,
                style: {
                    background: 'var(--pk-green)',
                    color: '#fff',
                    borderRadius: '10px',
                    fontSize: '0.85rem',
                    fontWeight: '500',
                },
                iconTheme: {
                    primary: '#fff',
                    secondary: 'var(--pk-green)',
                },
            });
        } catch (err) {
            toast.error('Failed to copy');
        }
    };

    const toggleSourceExpand = (messageId) => {
        setExpandedSources(prev => ({
            ...prev,
            [messageId]: !prev[messageId]
        }));
    };

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

    // Auto-load a conversation if 'conversation' param is in the URL (from Dashboard click)
    useEffect(() => {
        const conversationId = searchParams.get('conversation');
        if (conversationId) {
            loadConversation(conversationId);
        }
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

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

            // Set last user question for follow-up suggestions
            const lastUserMsg = formattedMessages.filter(m => m.type === 'user').pop();
            if (lastUserMsg) setLastUserQuestion(lastUserMsg.content);
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
            toast.success('Conversation deleted', {
                duration: 2000,
                style: {
                    borderRadius: '10px',
                    fontSize: '0.85rem',
                },
            });
        } catch (error) {
            console.error('Error deleting conversation:', error);
            toast.error('Failed to delete conversation');
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

            if (rating === 'up') {
                toast.success('Thanks for the feedback!', { duration: 1500, style: { borderRadius: '10px', fontSize: '0.85rem' } });
            } else if (rating === 'down') {
                toast('We\'ll try to improve', { icon: '📝', duration: 1500, style: { borderRadius: '10px', fontSize: '0.85rem' } });
            }
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
        setLastUserQuestion(messageText);

        // Save user message to database
        await saveMessage(convId, 'user', messageText);

        try {
            abortControllerRef.current = new AbortController();
            const result = await sendChatMessage(messageText, true, category, abortControllerRef.current.signal);
            // Save bot response to database first to get the real ID
            const savedMsg = await saveMessage(convId, 'bot', result.response);

            const botMessage = {
                id: savedMsg?.id || Date.now() + 1,
                type: 'bot',
                content: result.response,
                feedback: null,
                timestamp: new Date(),
                sources: result.sources || [],
                followUps: getFollowUpSuggestions(category, messageText)
            };
            setMessages(prev => [...prev, botMessage]);

            // Refresh chat history in sidebar
            await loadChatHistory();

        } catch (error) {
            console.error('Error:', error);
            if (error.name === 'AbortError') {
                const errorMessage = {
                    id: Date.now() + 1,
                    type: 'bot',
                    content: 'Generation stopped by user.',
                    timestamp: new Date()
                };
                setMessages(prev => [...prev, errorMessage]);
            } else {
                const errorMessage = {
                    id: Date.now() + 1,
                    type: 'bot',
                    content: 'Sorry, I encountered an error. Please try again.',
                    timestamp: new Date()
                };
                setMessages(prev => [...prev, errorMessage]);
                toast.error('Failed to get response. Please try again.');
            }
        } finally {
            setIsLoading(false);
            abortControllerRef.current = null;
        }
    };

    const handleNewChat = () => {
        setMessages([]);
        setCurrentConversationId(null);
        setShowHistory(false);
        setLastUserQuestion('');
        setExpandedSources({});
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

    // Regenerate: re-send the last user message
    const handleRegenerate = () => {
        if (!lastUserQuestion || isLoading) return;
        // Remove the last bot message from UI
        setMessages(prev => {
            const lastBotIdx = [...prev].reverse().findIndex(m => m.type === 'bot');
            if (lastBotIdx === -1) return prev;
            const actualIdx = prev.length - 1 - lastBotIdx;
            return prev.slice(0, actualIdx);
        });
        // Re-send the last user question
        handleSendMessage(null, lastUserQuestion);
    };

    // Export Conversation to PDF
    const handleExportPDF = () => {
        if (messages.length === 0) {
            toast.error("No conversation to export.");
            return;
        }

        const element = document.getElementById('pdf-export-container');
        if (!element) return;

        const opt = {
            margin:       10,
            filename:     `${catInfo.name.replace(/\s+/g, '_')}_Conversation.pdf`,
            image:        { type: 'jpeg', quality: 0.98 },
            html2canvas:  { scale: 2, useCORS: true },
            jsPDF:        { unit: 'mm', format: 'a4', orientation: 'portrait' }
        };

        toast.loading("Generating PDF...", { id: 'pdf-toast' });
        
        html2pdf().from(element).set(opt).save().then(() => {
            toast.success("PDF Downloaded successfully!", { id: 'pdf-toast' });
        }).catch((err) => {
            console.error("PDF Export Error:", err);
            toast.error("Failed to generate PDF.", { id: 'pdf-toast' });
        });
    };

    const isNewChat = messages.length === 0;
    const prompts = SUGGESTED_PROMPTS[category] || SUGGESTED_PROMPTS.general;

    // Find the last bot message for follow-up suggestions
    const lastBotMessage = [...messages].reverse().find(m => m.type === 'bot');

    return (
        <div className="chat-layout">
            {/* Toast Container */}
            <Toaster
                position="top-center"
                toastOptions={{
                    style: {
                        fontFamily: "'Inter', sans-serif",
                    },
                }}
            />

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
                    <button
                        className="sidebar-btn theme-toggle-sidebar"
                        title={theme === 'light' ? 'Dark Mode' : 'Light Mode'}
                        onClick={toggleTheme}
                    >
                        {theme === 'light' ? (
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
                            </svg>
                        ) : (
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <circle cx="12" cy="12" r="5"></circle>
                                <line x1="12" y1="1" x2="12" y2="3"></line>
                                <line x1="12" y1="21" x2="12" y2="23"></line>
                                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
                                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
                                <line x1="1" y1="12" x2="3" y2="12"></line>
                                <line x1="21" y1="12" x2="23" y2="12"></line>
                                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
                                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
                            </svg>
                        )}
                    </button>
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
                            <div className="history-loading">
                                <div className="loading-skeleton"></div>
                                <div className="loading-skeleton short"></div>
                                <div className="loading-skeleton"></div>
                            </div>
                        ) : chatHistory.length === 0 ? (
                            <div className="history-empty">
                                <div className="empty-icon">
                                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                                    </svg>
                                </div>
                                <p>No conversations yet</p>
                                <span>Your chat history will appear here once you start a conversation</span>
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
                <div className="chat-topbar" style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
                    <button 
                        onClick={() => navigate('/dashboard')} 
                        style={{ background: 'transparent', border: '1px solid var(--border-light)', color: 'var(--text-secondary)', padding: '6px 12px', borderRadius: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.9rem' }}
                    >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <line x1="19" y1="12" x2="5" y2="12"></line>
                            <polyline points="12 19 5 12 12 5"></polyline>
                        </svg>
                        Back
                    </button>
                    <div className="topbar-category" style={{ background: catInfo.gradient }}>
                        <span>{catInfo.icon}</span>
                        <span>{catInfo.name}</span>
                    </div>
                    {!isNewChat && (
                        <button className="export-pdf-btn" onClick={handleExportPDF} title="Export Conversation to PDF">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                <polyline points="14 2 14 8 20 8"></polyline>
                                <line x1="12" y1="18" x2="12" y2="12"></line>
                                <polyline points="9 15 12 18 15 15"></polyline>
                            </svg>
                            Export PDF
                        </button>
                    )}
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
                        <div className="messages-list" id="pdf-export-container">
                            {messages.map((message, index) => (
                                <div
                                    key={message.id}
                                    className={`message ${message.type === 'user' ? 'user-message' : 'bot-message'}`}
                                >
                                    <div className={`message-avatar ${message.type === 'user' ? 'user-msg-avatar' : 'bot-msg-avatar'}`} style={{ overflow: 'hidden' }}>
                                        {message.type === 'bot' ? <img src={logo} alt="Bot" style={{ width: '100%', height: '100%', objectFit: 'cover' }} /> : userInitial}
                                    </div>
                                    <div className="message-body">
                                        <div className="message-header">
                                            <span className="message-sender">
                                                {message.type === 'bot' ? 'PakLawChatBot' : displayName}
                                            </span>
                                            <span className="message-timestamp">
                                                {formatTimestamp(message.timestamp)}
                                            </span>
                                        </div>
                                        <div className="message-content">
                                            {message.type === 'bot' ? (
                                                <ReactMarkdown
                                                    components={{
                                                        a: ({ node, children, ...props }) => (
                                                            <a
                                                                {...props}
                                                                target="_blank"
                                                                rel="noopener noreferrer"
                                                                className="legal-ref-link"
                                                            >
                                                                {children}
                                                            </a>
                                                        )
                                                    }}
                                                >
                                                    {linkifyLegalReferences(message.content)}
                                                </ReactMarkdown>
                                            ) : (
                                                <p>{message.content}</p>
                                            )}
                                        </div>

                                        {/* Source Citations Panel — only for bot messages with sources */}
                                        {message.type === 'bot' && message.sources && message.sources.length > 0 && (
                                            <div className="sources-panel">
                                                <button
                                                    className={`sources-toggle ${expandedSources[message.id] ? 'expanded' : ''}`}
                                                    onClick={() => toggleSourceExpand(message.id)}
                                                >
                                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                                                        <polyline points="14 2 14 8 20 8"></polyline>
                                                    </svg>
                                                    <span>{message.sources.length} Source{message.sources.length !== 1 ? 's' : ''} Referenced</span>
                                                    <svg className="sources-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                                        <polyline points="6 9 12 15 18 9"></polyline>
                                                    </svg>
                                                </button>
                                                {expandedSources[message.id] && (
                                                    <div className="sources-list">
                                                        {message.sources.map((source, idx) => (
                                                            <div key={idx} className="source-item">
                                                                <div className="source-header">
                                                                    <span className="source-icon">📄</span>
                                                                    <span className="source-name">{source.source || 'Legal Document'}</span>
                                                                    {source.page !== 'N/A' && (
                                                                        <span className="source-page">Page {source.page}</span>
                                                                    )}
                                                                </div>
                                                                {source.preview && (
                                                                    <p className="source-preview">{source.preview}</p>
                                                                )}
                                                            </div>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        )}

                                        {/* Action buttons for bot messages */}
                                        {message.type === 'bot' && (
                                            <div className="message-actions">
                                                {/* Copy button */}
                                                <button
                                                    className="action-btn copy-btn"
                                                    onClick={() => handleCopyMessage(message.content)}
                                                    title="Copy response"
                                                >
                                                    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                                                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                                                    </svg>
                                                </button>

                                                {/* Feedback buttons */}
                                                <button
                                                    className={`action-btn feedback-btn ${message.feedback === 'up' ? 'active-up' : ''}`}
                                                    onClick={() => handleFeedback(message.id, message.feedback === 'up' ? null : 'up')}
                                                    title="Helpful"
                                                >
                                                    <svg width="15" height="15" viewBox="0 0 24 24" fill={message.feedback === 'up' ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                        <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path>
                                                    </svg>
                                                </button>
                                                <button
                                                    className={`action-btn feedback-btn ${message.feedback === 'down' ? 'active-down' : ''}`}
                                                    onClick={() => handleFeedback(message.id, message.feedback === 'down' ? null : 'down')}
                                                    title="Not helpful"
                                                >
                                                    <svg width="15" height="15" viewBox="0 0 24 24" fill={message.feedback === 'down' ? 'currentColor' : 'none'} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                        <path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3zm7-13h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"></path>
                                                    </svg>
                                                </button>

                                                {/* Regenerate button — only on the last bot message */}
                                                {message === lastBotMessage && (
                                                    <button
                                                        className="action-btn regenerate-btn"
                                                        onClick={handleRegenerate}
                                                        title="Regenerate response"
                                                        disabled={isLoading}
                                                    >
                                                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                            <polyline points="23 4 23 10 17 10"></polyline>
                                                            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
                                                        </svg>
                                                    </button>
                                                )}
                                            </div>
                                        )}

                                        {/* Follow-up Suggestions — only on the LAST bot message */}
                                        {message.type === 'bot' && message === lastBotMessage && !isLoading && message.followUps && message.followUps.length > 0 && (
                                            <div className="followup-suggestions">
                                                <span className="followup-label">Related questions</span>
                                                <div className="followup-chips">
                                                    {message.followUps.map((followUp, idx) => (
                                                        <button
                                                            key={idx}
                                                            className="followup-chip"
                                                            onClick={() => handlePromptClick(followUp)}
                                                        >
                                                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                                <circle cx="12" cy="12" r="10"></circle>
                                                                <line x1="12" y1="8" x2="12" y2="16"></line>
                                                                <line x1="8" y1="12" x2="16" y2="12"></line>
                                                            </svg>
                                                            <span>{followUp}</span>
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}

                            {isLoading && (
                                <div className="message bot-message">
                                    <div className="message-avatar bot-msg-avatar">⚖️</div>
                                    <div className="message-body">
                                        <div className="message-header">
                                            <span className="message-sender">PakLawChatBot</span>
                                        </div>
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
                            {isLoading ? (
                                <button type="button" onClick={stopGenerating} className="send-btn stop-btn" style={{ background: '#ef4444', color: 'white', padding: '10px' }} title="Stop generating">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                                        <rect x="5" y="5" width="14" height="14"></rect>
                                    </svg>
                                </button>
                            ) : (
                                <button type="submit" disabled={!inputValue.trim()} className="send-btn" title="Send message">
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                        <line x1="22" y1="2" x2="11" y2="13"></line>
                                        <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                                    </svg>
                                </button>
                            )}
                        </form>
                    </div>
                    <p className="disclaimer">
                        ⚖️ PakLawChatBot provides general legal information only. Always consult a qualified lawyer.
                    </p>
                </div>
            </main>
        </div>
    );
}

export default Chat;
