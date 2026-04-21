import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function ProtectedRoute({ children }) {
    const { user, loading } = useAuth();

    if (loading) {
        return (
            <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                height: '100vh',
                background: '#1f1f1f',
                color: 'white'
            }}>
                Loading...
            </div>
        );
    }

    if (!user) {
        return <Navigate to="/login" replace />;
    }

    // Strict validation: Only allow if the account is verified
    if (!user.email_confirmed_at) {
        return <Navigate to="/verify-email" replace />;
    }

    return children;
}

export default ProtectedRoute;
