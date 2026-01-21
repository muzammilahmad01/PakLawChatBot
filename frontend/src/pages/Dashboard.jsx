import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Dashboard.css';

function Dashboard() {
    const navigate = useNavigate();
    const { user, profile, signOut } = useAuth();

    const displayName = profile?.username || profile?.full_name || user?.email?.split('@')[0] || 'User';

    const categories = [
        {
            id: 'cyber',
            title: 'Cyber Crime Laws',
            subtitle: 'PTA Regulations & PECA',
            icon: '💻',
            color: '#3b82f6',
            description: 'Telecommunication laws, cyber crime prevention, digital regulations'
        },
        {
            id: 'criminal',
            title: 'Criminal Laws',
            subtitle: 'Criminal Code',
            icon: '🪪',
            color: '#8b5cf6',
            description: 'Criminal Code, Penal Code, Criminal Procedure Code'
        },
        {
            id: 'Family',
            title: 'Family Laws',
            subtitle: 'Family Code',
            icon: '👨',
            color: '#10b981',
            description: 'Family Code, Matrimonial laws, Child laws'
        },
        {
            id: 'Property',
            title: "Property & Land Laws",
            subtitle: "Property Act, Land Act,",
            icon: "🏠",
            color: "#f59e0b",
            description: "Property Act, Land Act, Succession Act"
        },
        {
            id: "labour",
            title: "Labour Laws",
            subtitle: "Labour Act,",
            icon: "👷",
            color: "#148a6d",
            description: "Labour Act"
        },
        {
            id: 'constitutional',
            title: 'Constitutional Rights',
            subtitle: 'Pakistan Constitution',
            icon: '📜',
            color: '#f59e0b',
            description: 'Fundamental rights, constitutional provisions'
        },
        {
            id: 'general',
            title: 'General Legal Query',
            subtitle: 'All Laws',
            icon: '⚖️',
            color: '#ef4444',
            description: 'Ask anything about Pakistani law'
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
                    <span className="logo-icon">⚖️</span>
                    <h1>PakLawChatBot AI Powered Legal Platform</h1>
                </div>
                <div className="header-right">
                    <span className="welcome-text">Welcome, {displayName}</span>
                    <button className="logout-btn" onClick={handleLogout}>
                        Logout
                    </button>
                </div>
            </header>

            {/* Main Content */}
            <main className="dashboard-main">
                <div className="dashboard-hero">
                    <h2>What legal topic can I help you with?</h2>
                    <p>Select a category to get specialized legal assistance</p>
                </div>

                <div className="categories-grid">
                    {categories.map((category) => (
                        <div
                            key={category.id}
                            className="category-card"
                            onClick={() => handleCategoryClick(category.id)}
                            style={{ '--card-color': category.color }}
                        >
                            <div className="card-icon">{category.icon}</div>
                            <div className="card-content">
                                <h3>{category.title}</h3>
                                <span className="card-subtitle">{category.subtitle}</span>
                                <p className="card-description">{category.description}</p>
                            </div>
                            <div className="card-arrow">→</div>
                        </div>
                    ))}
                </div>

                <div className="dashboard-footer">
                    <p>🔒 Your conversations are private and secure</p>
                    <p className="disclaimer">PakLaw provides general legal information only. Consult a lawyer for specific legal advice.</p>
                </div>
            </main>
        </div>
    );
}

export default Dashboard;
