import { useNavigate, Link } from 'react-router-dom';
import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { supabase } from '../lib/supabase';
import './Dashboard.css';

// Category icons for recent conversations
const CATEGORY_META = {
    cyber: { icon: '💻', name: 'Cyber Crime Laws' },
    criminal: { icon: '⚔️', name: 'Criminal Laws' },
    Family: { icon: '👨‍👩‍👧', name: 'Family Laws' },
    Property: { icon: '🏠', name: 'Property Laws' },
    labour: { icon: '👷', name: 'Labour Laws' },
    constitutional: { icon: '📜', name: 'Constitutional Rights' },
    general: { icon: '⚖️', name: 'General Legal' },
};

function Dashboard() {
    const navigate = useNavigate();
    const { user, profile, signOut } = useAuth();
    const { theme, toggleTheme } = useTheme();

    const [recentChats, setRecentChats] = useState([]);
    const [recentLoading, setRecentLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState(null);
    const [isSearching, setIsSearching] = useState(false);

    const displayName = profile?.full_name || profile?.username || user?.email?.split('@')[0] || 'User';

    // Load recent conversations from Supabase
    const loadRecentChats = useCallback(async () => {
        if (!user) return;
        setRecentLoading(true);
        try {
            const { data, error } = await supabase
                .from('conversations')
                .select('id, title, category, created_at, updated_at')
                .eq('user_id', user.id)
                .order('updated_at', { ascending: false })
                .limit(5);

            if (error) throw error;
            setRecentChats(data || []);
        } catch (error) {
            console.error('Error loading recent chats:', error);
        } finally {
            setRecentLoading(false);
        }
    }, [user]);

    useEffect(() => {
        loadRecentChats();
    }, [loadRecentChats]);

    // Handle Global Search for Conversations
    const handleSearch = async (e) => {
        const query = e.target.value;
        setSearchQuery(query);

        if (!query.trim()) {
            setSearchResults(null);
            return;
        }

        setIsSearching(true);
        try {
            const { data, error } = await supabase
                .from('conversations')
                .select('id, title, category, updated_at')
                .eq('user_id', user.id)
                .ilike('title', `%${query}%`)
                .order('updated_at', { ascending: false })
                .limit(10);

            if (error) throw error;
            setSearchResults(data || []);
        } catch (error) {
            console.error('Error searching conversations:', error);
        } finally {
            setIsSearching(false);
        }
    };

    // Format relative date
    const formatRelativeDate = (dateString) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / (1000 * 60));
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays === 1) return 'Yesterday';
        if (diffDays < 7) return `${diffDays}d ago`;
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    };

    const categories = [
        {
            id: 'constitutional',
            title: 'Constitutional Rights',
            subtitle: 'Pakistan Constitution',
            icon: '📜',
            gradient: 'linear-gradient(135deg, #c9a227, #f0d55b)',
            description: 'Fundamental rights, constitutional provisions, amendments'
        },
        {
            id: 'criminal',
            title: 'Criminal Laws',
            subtitle: 'PPC & CrPC',
            icon: '⚔️',
            gradient: 'linear-gradient(135deg, #8b5cf6, #a855f7)',
            description: 'Pakistan Penal Code, Criminal Procedure, Evidence Act'
        },
        {
            id: 'Family',
            title: 'Family Laws',
            subtitle: 'MFLO & Family Courts',
            icon: '👨‍👩‍👧',
            gradient: 'linear-gradient(135deg, #10b981, #14b8a6)',
            description: 'Marriage, divorce, custody, inheritance, guardianship'
        },
        {
            id: 'Property',
            title: 'Property & Land Laws',
            subtitle: 'Transfer & Revenue',
            icon: '🏠',
            gradient: 'linear-gradient(135deg, #f59e0b, #f97316)',
            description: 'Property transfer, land revenue, registration, mutation'
        },
        {
            id: 'cyber',
            title: 'Cyber Crime Laws',
            subtitle: 'PECA & PTA',
            icon: '💻',
            gradient: 'linear-gradient(135deg, #3b82f6, #6366f1)',
            description: 'Electronic crimes, data protection, digital regulations'
        },
        {
            id: 'labour',
            title: 'Labour Laws',
            subtitle: 'Employment & Workers',
            icon: '👷',
            gradient: 'linear-gradient(135deg, #06b6d4, #0891b2)',
            description: 'Employment contracts, wages, workplace safety, disputes'
        },
        {
            id: 'general',
            title: 'General Legal Query',
            subtitle: 'All Laws',
            icon: '⚖️',
            gradient: 'linear-gradient(135deg, #ef4444, #f97316)',
            description: 'Ask anything about Pakistani law — all topics covered'
        },
        
    ];

    const handleCategoryClick = (categoryId) => {
        navigate(`/chat?category=${categoryId}`);
    };

    const handleLogout = async () => {
        try {
            await signOut();
            navigate('/login');
        } catch (error) {
            console.error('Logout error:', error);
        }
    };

    return (
        <div className="dashboard-container">
            {/* Header */}
            <header className="dashboard-header">
                <div className="header-left">
                    <div className="logo-badge">⚖️</div>
                    <div className="logo-text">
                        <h1>PakLawChatBot</h1>
                        <p className="logo-tagline">AI-Powered Legal Platform</p>
                    </div>
                </div>
                <div className="header-right">
                    <div className="user-info">
                        <span className="user-greeting">Welcome back,</span>
                        <span className="user-name">{displayName}</span>
                    </div>

                    {/* Dark Mode Toggle */}
                    <button
                        className="theme-toggle-btn"
                        onClick={toggleTheme}
                        title={theme === 'light' ? 'Switch to Dark Mode' : 'Switch to Light Mode'}
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

                    <Link to="/" className="home-btn">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                            <polyline points="9 22 9 12 15 12 15 22"></polyline>
                        </svg>
                        Home
                    </Link>
                    <button className="logout-btn" onClick={handleLogout}>
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path>
                            <polyline points="16 17 21 12 16 7"></polyline>
                            <line x1="21" y1="12" x2="9" y2="12"></line>
                        </svg>
                        Logout
                    </button>
                </div>
            </header>

            {/* Main Content */}
            <main className="dashboard-main">
                <div className="dashboard-hero">
                    <div className="hero-glow"></div>
                    <h2>What legal topic can I help you with?</h2>
                    <p>Select a category below for specialized legal assistance powered by AI</p>
                    
                    {/* Global Search Bar */}
                    <div className="global-search-container">
                        <div className="search-input-wrapper">
                            <svg className="search-icon" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <circle cx="11" cy="11" r="8"></circle>
                                <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                            </svg>
                            <input
                                type="text"
                                placeholder="Search past conversations..."
                                value={searchQuery}
                                onChange={handleSearch}
                                className="global-search-input"
                            />
                        </div>

                        {/* Search Results Dropdown */}
                        {searchQuery.trim() && (
                            <div className="search-results-dropdown">
                                {isSearching ? (
                                    <div className="search-result-item loading">Searching...</div>
                                ) : searchResults && searchResults.length > 0 ? (
                                    searchResults.map(result => {
                                        const meta = CATEGORY_META[result.category] || CATEGORY_META.general;
                                        return (
                                            <div 
                                                key={result.id} 
                                                className="search-result-item"
                                                onClick={() => navigate(`/chat?category=${result.category || 'general'}`)}
                                            >
                                                <div className="search-result-icon">{meta.icon}</div>
                                                <div className="search-result-info">
                                                    <span className="search-result-title">{result.title}</span>
                                                    <span className="search-result-meta">{meta.name} · {formatRelativeDate(result.updated_at)}</span>
                                                </div>
                                            </div>
                                        );
                                    })
                                ) : (
                                    <div className="search-result-item empty">No conversations found matching "{searchQuery}"</div>
                                )}
                            </div>
                        )}
                    </div>
                </div>

                {/* Recent Conversations Widget */}
                {!recentLoading && recentChats.length > 0 && (
                    <div className="recent-chats-section">
                        <div className="section-label">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                <circle cx="12" cy="12" r="10"></circle>
                                <polyline points="12 6 12 12 16 14"></polyline>
                            </svg>
                            <span>Continue where you left off</span>
                        </div>
                        <div className="recent-chats-grid">
                            {recentChats.map((chat) => {
                                const meta = CATEGORY_META[chat.category] || CATEGORY_META.general;
                                return (
                                    <div
                                        key={chat.id}
                                        className="recent-chat-card"
                                        onClick={() => navigate(`/chat?category=${chat.category || 'general'}`)}
                                    >
                                        <div className="recent-chat-icon">{meta.icon}</div>
                                        <div className="recent-chat-info">
                                            <span className="recent-chat-title">{chat.title}</span>
                                            <span className="recent-chat-meta">
                                                {meta.name} · {formatRelativeDate(chat.updated_at)}
                                            </span>
                                        </div>
                                        <svg className="recent-chat-arrow" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <polyline points="9 18 15 12 9 6"></polyline>
                                        </svg>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}

                <div className="categories-grid">
                    {categories.map((category) => (
                        <div
                            key={category.id}
                            className="category-card"
                            onClick={() => handleCategoryClick(category.id)}
                        >
                            <div className="card-glow" style={{ background: category.gradient }}></div>
                            <div className="card-icon" style={{ background: category.gradient }}>
                                {category.icon}
                            </div>
                            <div className="card-content">
                                <h3>{category.title}</h3>
                                <span className="card-subtitle">{category.subtitle}</span>
                                <p className="card-description">{category.description}</p>
                            </div>
                            <div className="card-arrow">
                                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                    <polyline points="9 18 15 12 9 6"></polyline>
                                </svg>
                            </div>
                        </div>
                    ))}
                </div>

                <div className="dashboard-footer">
                    <div className="footer-badges">
                        <span className="footer-badge">🔒 Private & Secure</span>
                        <span className="footer-badge">🤖 AI Powered</span>
                        <span className="footer-badge">📚 15,000+ Legal Documents</span>
                    </div>
                    <p className="disclaimer">⚖️ PakLawChatBot provides general legal information only. Always consult a qualified lawyer for specific legal advice.</p>
                </div>
            </main>
        </div>
    );
}

export default Dashboard;
