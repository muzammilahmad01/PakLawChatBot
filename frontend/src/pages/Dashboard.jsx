import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Dashboard.css';

function Dashboard() {
    const navigate = useNavigate();
    const { user, profile, signOut } = useAuth();

    const displayName = profile?.username || profile?.full_name || user?.email?.split('@')[0] || 'User';

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
                </div>

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
                    <p className="disclaimer">⚖️ PakLaw AI provides general legal information only. Always consult a qualified lawyer for specific legal advice.</p>
                </div>
            </main>
        </div>
    );
}

export default Dashboard;
