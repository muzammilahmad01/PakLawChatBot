import { Link } from 'react-router-dom';
import { useState, useEffect, useRef } from 'react';
import { useAuth } from '../context/AuthContext';
import './LandingPage.css';

// ─── Animated Counter Component ───
function AnimatedCounter({ end, suffix = '', duration = 2000 }) {
    const [count, setCount] = useState(0);
    const [hasAnimated, setHasAnimated] = useState(false);
    const ref = useRef(null);

    useEffect(() => {
        const observer = new IntersectionObserver(
            ([entry]) => {
                if (entry.isIntersecting && !hasAnimated) {
                    setHasAnimated(true);
                    let start = 0;
                    const increment = end / (duration / 16);
                    const timer = setInterval(() => {
                        start += increment;
                        if (start >= end) {
                            setCount(end);
                            clearInterval(timer);
                        } else {
                            setCount(Math.floor(start));
                        }
                    }, 16);
                    return () => clearInterval(timer);
                }
            },
            { threshold: 0.3 }
        );

        if (ref.current) observer.observe(ref.current);
        return () => observer.disconnect();
    }, [end, duration, hasAnimated]);

    return (
        <span ref={ref}>
            {count.toLocaleString()}{suffix}
        </span>
    );
}

// ─── Scroll Reveal Component ───
function Reveal({ children, delay = 0, className = '' }) {
    const [isVisible, setIsVisible] = useState(false);
    const ref = useRef(null);

    useEffect(() => {
        const observer = new IntersectionObserver(
            ([entry]) => {
                if (entry.isIntersecting) {
                    setTimeout(() => setIsVisible(true), delay);
                    observer.unobserve(entry.target);
                }
            },
            { threshold: 0.1 }
        );

        if (ref.current) observer.observe(ref.current);
        return () => observer.disconnect();
    }, [delay]);

    return (
        <div
            ref={ref}
            className={`reveal ${isVisible ? 'reveal-visible' : ''} ${className}`}
            style={{ transitionDelay: `${delay}ms` }}
        >
            {children}
        </div>
    );
}

function LandingPage() {
    const { user } = useAuth();
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [scrolled, setScrolled] = useState(false);
    const [activeFaq, setActiveFaq] = useState(null);

    useEffect(() => {
        const handleScroll = () => setScrolled(window.scrollY > 20);
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const stats = [
        { value: 19000, suffix: '+', label: 'Legal Documents Indexed', icon: '📚' },
        { value: 7, suffix: '', label: 'Specialized Law Categories', icon: '📂' },
        { value: 5, suffix: 's', label: 'Average Response Time', prefix: '<', icon: '⚡' },
        { value: 99, suffix: '%', label: 'Uptime & Availability', icon: '🟢' },
        { value: 1, suffix: '', label: 'Language Supported', icon: '🌐' },
        { value: 24, suffix: '/7', label: 'Always Available', icon: '🕐' },
    ];

    const features = [
        {
            icon: (
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" /><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
                </svg>
            ),
            title: 'Legal Database',
            description: 'Instant access to Pakistani federal statutes, criminal laws, family laws, property laws, and more.',
        },
        {
            icon: (
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
                </svg>
            ),
            title: 'Smart AI Search',
            description: 'AI-powered search across multiple legal sources with multi-step reasoning for complex questions.',
        },

        {
            icon: (
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
            ),
            title: 'Chat History',
            description: 'Save and revisit your past legal conversations. Your research, always accessible.',
        },
        {
            icon: (
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <rect x="3" y="11" width="18" height="11" rx="2" ry="2" /><path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
            ),
            title: 'Private & Secure',
            description: 'Your queries are processed securely. We never share your data with third parties.',
        },
        {
            icon: (
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" /><polyline points="10 9 9 9 8 9" />
                </svg>
            ),
            title: 'Source Citations',
            description: 'Every answer is backed by verifiable legal sources and references you can trust.',
        },
    ];

    const categories = [
        { id: 'constitutional', title: 'Constitutional Rights', subtitle: 'Pakistan Constitution', icon: '📜', gradient: 'linear-gradient(135deg, #01411C, #05632E)' },
        { id: 'criminal', title: 'Criminal Laws', subtitle: 'PPC & CrPC', icon: '⚔️', gradient: 'linear-gradient(135deg, #7c3aed, #a855f7)' },
        { id: 'Family', title: 'Family Laws', subtitle: 'MFLO & Family Courts', icon: '👨‍👩‍👧', gradient: 'linear-gradient(135deg, #059669, #10b981)' },
        { id: 'Property', title: 'Property & Land Laws', subtitle: 'Transfer & Revenue', icon: '🏠', gradient: 'linear-gradient(135deg, #d97706, #f59e0b)' },
        { id: 'cyber', title: 'Cyber Crime Laws', subtitle: 'PECA & PTA', icon: '💻', gradient: 'linear-gradient(135deg, #2563eb, #6366f1)' },
        { id: 'labour', title: 'Labour Laws', subtitle: 'Employment & Workers', icon: '👷', gradient: 'linear-gradient(135deg, #0891b2, #06b6d4)' },
        { id: 'general', title: 'General Legal Query', subtitle: 'All Laws', icon: '⚖️', gradient: 'linear-gradient(135deg, #01411C, #c9a227)' },
    ];

    const faqs = [
        {
            question: 'What is PakLawChatBot?',
            answer: 'PakLawChatBot is an AI-powered legal assistant specializing in Pakistani law. It uses advanced RAG (Retrieval-Augmented Generation) technology to provide accurate legal information from a database of over 15,000+ legal documents including statutes, case laws, and legal texts.',
        },
        {
            question: 'Is PakLawChatBot free to use?',
            answer: 'Yes! PakLawChatBot is completely free. We believe legal information should be accessible to everyone. Simply create an account and start asking your legal questions.',
        },
        {
            question: 'What areas of Pakistani law does it cover?',
            answer: 'PakLawChatBot covers Constitutional Law, Criminal Law (PPC & CrPC), Family Law (MFLO), Property & Land Laws, Cyber Crime Laws (PECA & PTA), Labour Laws, and general legal queries across all areas of Pakistani law.',
        },

        {
            question: 'Does PakLawChatBot replace a real lawyer?',
            answer: 'No. PakLawChatBot provides general legal information and guidance only. For formal legal proceedings, complex cases, or official legal advice, we strongly recommend consulting with a qualified lawyer.',
        },
        {
            question: 'Is my data secure?',
            answer: 'Absolutely. We use industry-standard encryption for all data transmission and storage. Your conversations remain confidential, and we do not share personal information with any third parties.',
        },
    ];

    return (
        <div className="landing-page">

            {/* ─── NAVBAR ─── */}
            <nav className={`landing-nav ${scrolled ? 'nav-scrolled' : ''}`}>
                <div className="nav-container">
                    <Link to="/" className="nav-logo">
                        <span className="nav-logo-icon">⚖️</span>
                        <span className="nav-logo-text">PakLaw<span className="nav-logo-accent">ChatBot</span></span>
                    </Link>

                    <div className={`nav-links ${mobileMenuOpen ? 'nav-links-open' : ''}`}>
                        <a href="#features" onClick={() => setMobileMenuOpen(false)}>Features</a>
                        <a href="#categories" onClick={() => setMobileMenuOpen(false)}>Categories</a>
                        <a href="#faq" onClick={() => setMobileMenuOpen(false)}>FAQ</a>
                    </div>

                    <div className="nav-actions">
                        {user ? (
                            <Link to="/dashboard" className="nav-btn nav-btn-primary">Go to Dashboard</Link>
                        ) : (
                            <>
                                <Link to="/login" className="nav-btn nav-btn-ghost">Sign In</Link>
                                <Link to="/signup" className="nav-btn nav-btn-primary">Get Started</Link>
                            </>
                        )}
                    </div>

                    <button
                        className="nav-hamburger"
                        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                        aria-label="Toggle menu"
                    >
                        <span className={`hamburger-line ${mobileMenuOpen ? 'open' : ''}`}></span>
                        <span className={`hamburger-line ${mobileMenuOpen ? 'open' : ''}`}></span>
                        <span className={`hamburger-line ${mobileMenuOpen ? 'open' : ''}`}></span>
                    </button>
                </div>
            </nav>

            {/* ─── HERO ─── */}
            <section className="hero-section">
                <div className="hero-bg-shapes">
                    <div className="hero-shape hero-shape-1"></div>
                    <div className="hero-shape hero-shape-2"></div>
                    <div className="hero-shape hero-shape-3"></div>
                </div>

                <div className="hero-container">
                    <div className="hero-content">
                        <Reveal>
                            <div className="hero-badge">
                                <span className="hero-badge-dot"></span>
                                AI-Powered Legal Assistant for Pakistan
                            </div>
                        </Reveal>

                        <Reveal delay={100}>
                            <h1 className="hero-title">
                                Navigate <span className="hero-title-accent">Pakistani Law</span> with Confidence
                            </h1>
                        </Reveal>

                        <Reveal delay={200}>
                            <p className="hero-subtitle">
                                Get instant legal guidance. Powered by AI trained on
                                Pakistan's Constitution, Penal Codes, Family Laws, and 15,000+ legal documents.
                            </p>
                        </Reveal>

                        <Reveal delay={300}>
                            <div className="hero-actions">
                                <Link to="/signup" className="hero-btn hero-btn-primary">
                                    Start Chatting Free
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                        <line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" />
                                    </svg>
                                </Link>
                                <a href="#features" className="hero-btn hero-btn-secondary">
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <polygon points="5 3 19 12 5 21 5 3" />
                                    </svg>
                                    How It Works
                                </a>
                            </div>
                        </Reveal>

                        <Reveal delay={400}>
                            <div className="hero-trust-badges">
                                <span className="trust-badge">🔒 Secure & Private</span>
                                <span className="trust-badge">🤖 AI Powered</span>
                                <span className="trust-badge">🇵🇰 Made for Pakistan</span>
                            </div>
                        </Reveal>
                    </div>

                    <Reveal delay={300} className="hero-preview-wrapper">
                        <div className="hero-chat-preview">
                            <div className="preview-header">
                                <div className="preview-dots">
                                    <span></span><span></span><span></span>
                                </div>
                                <span className="preview-title">PakLawChatBot</span>
                                <div style={{ width: 48 }}></div>
                            </div>
                            <div className="preview-messages">
                                <div className="preview-msg preview-msg-user">
                                    <div className="preview-msg-bubble user-bubble">
                                        What are the fundamental rights in Pakistan's Constitution?
                                    </div>
                                </div>
                                <div className="preview-msg preview-msg-bot">
                                    <div className="preview-msg-avatar">⚖️</div>
                                    <div className="preview-msg-bubble bot-bubble">
                                        <p>The Constitution of Pakistan guarantees several <strong>fundamental rights</strong> under Part II, Chapter 1 (Articles 8-28):</p>
                                        <ul>
                                            <li><strong>Article 9:</strong> Security of person</li>
                                            <li><strong>Article 14:</strong> Inviolability of dignity</li>
                                            <li><strong>Article 19:</strong> Freedom of speech</li>
                                            <li><strong>Article 25:</strong> Equality of citizens</li>
                                        </ul>
                                        <div className="preview-citations">
                                            <span className="preview-citation">📄 Constitution of Pakistan</span>
                                            <span className="preview-citation">📄 Part II, Ch. 1</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            <div className="preview-input">
                                <span>Ask about Pakistani law...</span>
                                <div className="preview-send-btn">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                                        <line x1="22" y1="2" x2="11" y2="13" /><polygon points="22 2 15 22 11 13 2 9 22 2" />
                                    </svg>
                                </div>
                            </div>
                        </div>
                    </Reveal>
                </div>
            </section>

            {/* ─── STATS ─── */}
            <section className="stats-section">
                <div className="section-container">
                    <Reveal>
                        <div className="section-header">
                            <span className="section-label">By the Numbers</span>
                            <h2 className="section-title">Built for Scale & Reliability</h2>
                            <p className="section-subtitle">Transparent data about our platform's capabilities</p>
                        </div>
                    </Reveal>

                    <div className="stats-grid">
                        {stats.map((stat, index) => (
                            <Reveal key={index} delay={index * 80}>
                                <div className="stat-card">
                                    <span className="stat-icon">{stat.icon}</span>
                                    <div className="stat-value">
                                        {stat.prefix || ''}
                                        <AnimatedCounter end={stat.value} suffix={stat.suffix} />
                                    </div>
                                    <span className="stat-label">{stat.label}</span>
                                </div>
                            </Reveal>
                        ))}
                    </div>
                </div>
            </section>

            {/* ─── FEATURES ─── */}
            <section className="features-section" id="features">
                <div className="section-container">
                    <Reveal>
                        <div className="section-header">
                            <span className="section-label">Features</span>
                            <h2 className="section-title">Everything You Need for Legal Research</h2>
                            <p className="section-subtitle">Powerful AI tools designed specifically for navigating Pakistani law</p>
                        </div>
                    </Reveal>

                    <div className="features-grid">
                        {features.map((feature, index) => (
                            <Reveal key={index} delay={index * 100}>
                                <div className="feature-card">
                                    <div className="feature-icon-wrap">
                                        {feature.icon}
                                    </div>
                                    <h3 className="feature-title">{feature.title}</h3>
                                    <p className="feature-desc">{feature.description}</p>
                                </div>
                            </Reveal>
                        ))}
                    </div>
                </div>
            </section>

            {/* ─── LAW CATEGORIES ─── */}
            <section className="categories-section" id="categories">
                <div className="section-container">
                    <Reveal>
                        <div className="section-header">
                            <span className="section-label">Law Categories</span>
                            <h2 className="section-title">Explore Pakistani Law by Category</h2>
                            <p className="section-subtitle">Select a category and get specialized legal guidance from our AI</p>
                        </div>
                    </Reveal>

                    <div className="landing-categories-grid">
                        {categories.map((cat, index) => (
                            <Reveal key={cat.id} delay={index * 80}>
                                <Link
                                    to={user ? `/chat?category=${cat.id}` : '/signup'}
                                    className="landing-category-card"
                                >
                                    <div className="landing-cat-icon" style={{ background: cat.gradient }}>
                                        {cat.icon}
                                    </div>
                                    <div className="landing-cat-info">
                                        <h3>{cat.title}</h3>
                                        <span>{cat.subtitle}</span>
                                    </div>
                                    <svg className="landing-cat-arrow" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                        <polyline points="9 18 15 12 9 6" />
                                    </svg>
                                </Link>
                            </Reveal>
                        ))}
                    </div>
                </div>
            </section>

            {/* ─── HOW IT WORKS ─── */}
            <section className="how-it-works-section">
                <div className="section-container">
                    <Reveal>
                        <div className="section-header">
                            <span className="section-label">How It Works</span>
                            <h2 className="section-title">Get Legal Answers in 3 Simple Steps</h2>
                        </div>
                    </Reveal>

                    <div className="steps-grid">
                        <Reveal delay={0}>
                            <div className="step-card">
                                <div className="step-number">01</div>
                                <div className="step-icon-wrap">
                                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
                                    </svg>
                                </div>
                                <h3>Create Account</h3>
                                <p>Sign up for free in seconds with email or Google account</p>
                            </div>
                        </Reveal>

                        <Reveal delay={150}>
                            <div className="step-card">
                                <div className="step-number">02</div>
                                <div className="step-icon-wrap">
                                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                        <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" /><rect x="14" y="14" width="7" height="7" /><rect x="3" y="14" width="7" height="7" />
                                    </svg>
                                </div>
                                <h3>Choose Category</h3>
                                <p>Select from 7 specialized legal categories for tailored results</p>
                            </div>
                        </Reveal>

                        <Reveal delay={300}>
                            <div className="step-card">
                                <div className="step-number">03</div>
                                <div className="step-icon-wrap">
                                    <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                                    </svg>
                                </div>
                                <h3>Ask Your Question</h3>
                                <p>Get instant AI-powered answers with source citations</p>
                            </div>
                        </Reveal>
                    </div>
                </div>
            </section>

            {/* ─── FAQ ─── */}
            <section className="faq-section" id="faq">
                <div className="section-container">
                    <Reveal>
                        <div className="section-header">
                            <span className="section-label">FAQ</span>
                            <h2 className="section-title">Frequently Asked Questions</h2>
                            <p className="section-subtitle">Everything you need to know about PakLawChatBot</p>
                        </div>
                    </Reveal>

                    <div className="faq-list">
                        {faqs.map((faq, index) => (
                            <Reveal key={index} delay={index * 60}>
                                <div
                                    className={`faq-item ${activeFaq === index ? 'faq-active' : ''}`}
                                    onClick={() => setActiveFaq(activeFaq === index ? null : index)}
                                >
                                    <div className="faq-question">
                                        <h3>{faq.question}</h3>
                                        <svg
                                            className="faq-chevron"
                                            width="20" height="20"
                                            viewBox="0 0 24 24"
                                            fill="none"
                                            stroke="currentColor"
                                            strokeWidth="2"
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                        >
                                            <polyline points="6 9 12 15 18 9" />
                                        </svg>
                                    </div>
                                    <div className="faq-answer">
                                        <p>{faq.answer}</p>
                                    </div>
                                </div>
                            </Reveal>
                        ))}
                    </div>
                </div>
            </section>

            {/* ─── CTA BANNER ─── */}
            <section className="cta-section">
                <div className="section-container">
                    <div className="cta-card">
                        <div className="cta-bg-pattern"></div>
                        <Reveal>
                            <h2>Legal information should be accessible to everyone.</h2>
                        </Reveal>
                        <Reveal delay={100}>
                            <p>Free to use. Built for Pakistani law.</p>
                        </Reveal>
                        <Reveal delay={200}>
                            <div className="cta-actions">
                                <Link to="/signup" className="hero-btn hero-btn-primary cta-btn-white">
                                    Start Using PakLawChatBot
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                        <line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" />
                                    </svg>
                                </Link>
                            </div>
                        </Reveal>
                    </div>
                </div>
            </section>

            {/* ─── FOOTER ─── */}
            <footer className="landing-footer">
                <div className="section-container">
                    <div className="footer-grid">
                        <div className="footer-brand">
                            <div className="footer-logo">
                                <span>⚖️</span>
                                <span>PakLaw<strong>ChatBot</strong></span>
                            </div>
                            <p>AI-powered legal assistance for every Pakistani citizen. Democratizing legal knowledge through technology.</p>
                            <div className="footer-socials">
                                <a href="#" aria-label="Twitter" className="social-link">
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                                        <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
                                    </svg>
                                </a>
                                <a href="#" aria-label="LinkedIn" className="social-link">
                                    <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                                        <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
                                    </svg>
                                </a>
                            </div>
                        </div>

                        <div className="footer-links-group">
                            <h4>Platform</h4>
                            <a href="#features">Features</a>
                            <a href="#categories">Law Categories</a>
                            <a href="#faq">FAQ</a>
                            <Link to="/login">Sign In</Link>
                        </div>

                        <div className="footer-links-group">
                            <h4>Legal Areas</h4>
                            <span>Constitutional Law</span>
                            <span>Criminal Law</span>
                            <span>Family Law</span>
                            <span>Property Law</span>
                        </div>

                        <div className="footer-links-group">
                            <h4>Contact</h4>
                            <span>Islamabad, Pakistan</span>
                            <a href="mailto:support@pakLawChatBot.com">support@pakLawChatBot.com</a>
                        </div>
                    </div>

                    <div className="footer-bottom">
                        <p>© {new Date().getFullYear()} PakLawChatBot. All rights reserved.</p>
                        <p className="footer-disclaimer">
                            ⚖️ PakLawChatBot AI provides general legal information only. Always consult a qualified lawyer for specific legal advice.
                        </p>
                    </div>
                </div>
            </footer>
        </div>
    );
}

export default LandingPage;
