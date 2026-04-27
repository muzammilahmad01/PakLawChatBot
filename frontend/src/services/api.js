const API_URL = '';  // Empty = same origin, Nginx handles the proxy


export const sendChatMessage = async (message, useRag = true, category = null, signal = null) => {
    try {
        const response = await fetch(`${API_URL}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                use_rag: useRag,
                category: category,
            }),
            signal: signal,
        });

        if (!response.ok) {
            throw new Error('Failed to get response');
        }

        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
};