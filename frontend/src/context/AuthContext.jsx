import { createContext, useContext, useEffect, useState } from 'react';
import { supabase } from '../lib/supabase';

const AuthContext = createContext({});

export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Get initial session
        supabase.auth.getSession().then(({ data: { session } }) => {
            setUser(session?.user ?? null);

            // Fetch profile if user exists
            if (session?.user) {
                supabase
                    .from('profiles')
                    .select('full_name, username')
                    .eq('id', session.user.id)
                    .single()
                    .then(({ data }) => {
                        setProfile(data);
                    })
                    .catch(console.error);
            }

            setLoading(false);
        }).catch((error) => {
            console.error('Session error:', error);
            setLoading(false);
        });

        // Listen for auth changes
        const { data: { subscription } } = supabase.auth.onAuthStateChange(
            (_event, session) => {
                setUser(session?.user ?? null);

                if (session?.user) {
                    supabase
                        .from('profiles')
                        .select('full_name, username')
                        .eq('id', session.user.id)
                        .single()
                        .then(({ data }) => setProfile(data))
                        .catch(console.error);
                } else {
                    setProfile(null);
                }
            }
        );

        return () => subscription.unsubscribe();
    }, []);

    // Sign up with email and password
    const signUp = async (email, password, fullName, username) => {
        const { data, error } = await supabase.auth.signUp({
            email,
            password,
        });

        if (error) throw error;

        if (data.user) {
            await supabase.from('profiles').insert([{
                id: data.user.id,
                full_name: fullName,
                username: username,
            }]);
        }

        return data;
    };

    // Sign in
    const signIn = async (email, password) => {
        const { data, error } = await supabase.auth.signInWithPassword({
            email,
            password,
        });

        if (error) throw error;
        return data;
    };

    // Sign out
    const signOut = async () => {
        await supabase.auth.signOut();
        setProfile(null);
    };

    // Sign in with Google
    const signInWithGoogle = async () => {
        const { data, error } = await supabase.auth.signInWithOAuth({
            provider: 'google',
            options: {
                redirectTo: window.location.origin + '/dashboard'
            }
        });

        if (error) throw error;
        return data;
    };

    // Reset password (forgot password)
    const resetPassword = async (email) => {
        const { data, error } = await supabase.auth.resetPasswordForEmail(email, {
            redirectTo: window.location.origin + '/reset-password'
        });

        if (error) throw error;
        return data;
    };

    return (
        <AuthContext.Provider value={{ user, profile, loading, signUp, signIn, signOut, signInWithGoogle, resetPassword }}>
            {!loading && children}
        </AuthContext.Provider>
    );
}
