import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import './Auth.css';

function ResetPassword() {
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [loading, setLoading] = useState(false);
    const [sessionReady, setSessionReady] = useState(false);
    const navigate = useNavigate();

    useEffect(() => {
        // Supabase automatically picks up the recovery token from the URL hash
        // and establishes a session. We listen for that event.
        const { data: { subscription } } = supabase.auth.onAuthStateChange(
            (event, session) => {
                if (event === 'PASSWORD_RECOVERY') {
                    setSessionReady(true);
                }
            }
        );

        // Also check if session already exists (in case event fired before listener)
        supabase.auth.getSession().then(({ data: { session } }) => {
            if (session) {
                setSessionReady(true);
            }
        });

        return () => subscription.unsubscribe();
    }, []);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');

        // Validation
        if (!password || !confirmPassword) {
            setError('Please fill in both fields');
            return;
        }

        if (password.length < 6) {
            setError('Password must be at least 6 characters');
            return;
        }

        if (password !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }

        try {
            setLoading(true);

            const { error: updateError } = await supabase.auth.updateUser({
                password: password
            });

            if (updateError) throw updateError;

            setSuccess('Password updated successfully! Redirecting to login...');

            // Sign out and redirect to login
            setTimeout(async () => {
                await supabase.auth.signOut();
                navigate('/login');
            }, 2000);

        } catch (err) {
            setError(err.message || 'Failed to update password');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-container">
            <div className="auth-card">
                <div className="auth-header">
                    <h1>⚖️ PakLaw ChatBot</h1>
                    <p>Your AI Legal Assistant</p>
                </div>

                <form onSubmit={handleSubmit} className="auth-form">
                    <h2>Reset Password</h2>
                    <p className="auth-subtitle">
                        {sessionReady
                            ? 'Enter your new password below'
                            : 'Verifying your reset link...'}
                    </p>

                    {error && <div className="error-message">{error}</div>}
                    {success && <div className="success-message">{success}</div>}

                    {!sessionReady && !error && (
                        <div style={{
                            textAlign: 'center',
                            padding: '20px',
                            color: 'rgba(255,255,255,0.6)'
                        }}>
                            <div style={{
                                width: '40px',
                                height: '40px',
                                border: '3px solid rgba(255,255,255,0.2)',
                                borderTop: '3px solid #c9a227',
                                borderRadius: '50%',
                                animation: 'spin 1s linear infinite',
                                margin: '0 auto 15px'
                            }} />
                            Loading...
                        </div>
                    )}

                    {sessionReady && !success && (
                        <>
                            <div className="form-group">
                                <label htmlFor="new-password">New Password</label>
                                <input
                                    type="password"
                                    id="new-password"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    placeholder="Enter new password (min 6 characters)"
                                    disabled={loading}
                                />
                            </div>

                            <div className="form-group">
                                <label htmlFor="confirm-new-password">Confirm New Password</label>
                                <input
                                    type="password"
                                    id="confirm-new-password"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    placeholder="Confirm your new password"
                                    disabled={loading}
                                />
                            </div>

                            <button type="submit" className="auth-button" disabled={loading}>
                                {loading ? 'Updating Password...' : 'Update Password'}
                            </button>
                        </>
                    )}
                </form>
            </div>

            <style>{`
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
            `}</style>
        </div>
    );
}

export default ResetPassword;
