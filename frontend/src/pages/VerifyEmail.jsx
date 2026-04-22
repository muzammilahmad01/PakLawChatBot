import { useState } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { supabase } from '../lib/supabase';
import './Auth.css';

function VerifyEmail() {
    const { user } = useAuth();
    const [resending, setResending] = useState(false);
    const [resendMessage, setResendMessage] = useState('');

    // If user is verified, send them to dashboard
    if (user && user.email_confirmed_at) {
        return <Navigate to="/dashboard" replace />;
    }

    const handleResendEmail = async () => {
        if (!user?.email) return;
        try {
            setResending(true);
            setResendMessage('');
            const { error } = await supabase.auth.resend({
                type: 'signup',
                email: user.email,
            });
            if (error) throw error;
            setResendMessage('Verification email resent! Check your inbox.');
        } catch (err) {
            console.error(err);
            setResendMessage('Could not resend email. Please try again later.');
        } finally {
            setResending(false);
        }
    };

    const handleSignOut = async () => {
        await supabase.auth.signOut();
    };

    return (
        <div className="auth-container">
            <div className="auth-card" style={{ textAlign: 'center', padding: '40px 20px' }}>
                <div style={{ fontSize: '3rem', marginBottom: '16px' }}>✉️</div>
                <h2 style={{ marginBottom: '12px', color: 'var(--text-primary)' }}>Verify Your Email</h2>
                <p style={{ color: 'var(--text-muted)', marginBottom: '24px', lineHeight: '1.6' }}>
                    We've sent a verification link to <strong style={{ color: 'var(--text-primary)' }}>{user?.email || 'your email address'}</strong>. Please check your inbox (and spam folder) and click the link to activate your account.
                </p>
                <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginBottom: '24px' }}>
                    You will not be able to access the dashboard until your email is verified.
                </p>

                {resendMessage && (
                    <p style={{ color: 'var(--pk-green)', fontSize: '0.85rem', marginBottom: '16px' }}>
                        {resendMessage}
                    </p>
                )}

                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', alignItems: 'center' }}>
                    {user && (
                        <button
                            onClick={handleResendEmail}
                            disabled={resending}
                            className="auth-button"
                            style={{ width: 'auto', padding: '10px 24px' }}
                        >
                            {resending ? 'Sending...' : 'Resend Verification Email'}
                        </button>
                    )}
                    <button
                        onClick={handleSignOut}
                        style={{
                            background: 'transparent',
                            border: '1px solid var(--border-light)',
                            borderRadius: '8px',
                            padding: '10px 24px',
                            color: 'var(--text-muted)',
                            cursor: 'pointer',
                            fontSize: '0.9rem'
                        }}
                    >
                        Sign out & use a different account
                    </button>
                    <Link to="/login" style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '8px' }}>
                        Back to Login
                    </Link>
                </div>
            </div>
        </div>
    );
}

export default VerifyEmail;
