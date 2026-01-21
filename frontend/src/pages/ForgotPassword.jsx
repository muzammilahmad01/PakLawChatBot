import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Auth.css';

function ForgotPassword() {
    const [email, setEmail] = useState('');
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [loading, setLoading] = useState(false);
    const { resetPassword } = useAuth();

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setSuccess('');

        if (!email) {
            setError('Please enter your email address');
            return;
        }

        try {
            setLoading(true);
            await resetPassword(email);
            setSuccess('Password reset link sent! Check your email inbox.');
        } catch (err) {
            setError(err.message || 'Failed to send reset email');
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
                    <h2>Forgot Password?</h2>
                    <p className="auth-subtitle">Enter your email to receive a reset link</p>

                    {error && <div className="error-message">{error}</div>}
                    {success && <div className="success-message">{success}</div>}

                    <div className="form-group">
                        <label htmlFor="email">Email Address</label>
                        <input
                            type="email"
                            id="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="Enter your email"
                            disabled={loading || success}
                        />
                    </div>

                    <button type="submit" className="auth-button" disabled={loading || success}>
                        {loading ? 'Sending...' : 'Send Reset Link'}
                    </button>

                    <p className="auth-footer">
                        Remember your password? <Link to="/login">Sign In</Link>
                    </p>
                </form>
            </div>
        </div>
    );
}

export default ForgotPassword;
