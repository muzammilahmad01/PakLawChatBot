import { Link } from 'react-router-dom';
import './Auth.css';

function VerifyEmail() {
    return (
        <div className="auth-container">
            <div className="auth-card" style={{ textAlign: 'center', padding: '40px 20px' }}>
                <div style={{ fontSize: '3rem', marginBottom: '16px' }}>✉️</div>
                <h2 style={{ marginBottom: '12px', color: 'var(--text-primary)' }}>Verify Your Email</h2>
                <p style={{ color: 'var(--text-muted)', marginBottom: '24px', lineHeight: '1.6' }}>
                    We've sent a verification link to your email address. Please check your inbox (and spam folder) and click the link to activate your account.
                </p>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '24px' }}>
                    You will not be able to access the dashboard until your email is verified.
                </p>
                <Link to="/login" className="auth-button" style={{ display: 'inline-block', textDecoration: 'none', width: 'auto', padding: '10px 24px' }}>
                    Back to Login
                </Link>
            </div>
        </div>
    );
}

export default VerifyEmail;
