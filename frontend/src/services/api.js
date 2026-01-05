const API_URL = 'http://localhost:5000';

export const sendChatMessage = async (message, useRag = true) => {
    try {
        const response = await fetch(`${API_URL}/api/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                use_rag: useRag,
            }),
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