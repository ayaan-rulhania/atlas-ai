(() => {
    const messagesEl = document.getElementById('messages');
    const promptForm = document.getElementById('promptForm');
    const promptInput = document.getElementById('promptInput');
    const newChatBtn = document.getElementById('newChatBtn');

    let chatId = null;
    let sending = false;

    const appendMessage = (role, text, isPending = false) => {
        const wrapper = document.createElement('div');
        wrapper.className = `message ${role}`;
        const roleEl = document.createElement('span');
        roleEl.className = 'role';
        roleEl.textContent = role === 'user' ? 'You' : 'Thor 1.0';
        const textEl = document.createElement('div');
        textEl.className = 'text';
        textEl.textContent = text;
        wrapper.appendChild(roleEl);
        wrapper.appendChild(textEl);
        if (isPending) {
            wrapper.dataset.pending = 'true';
        }
        messagesEl.appendChild(wrapper);
        messagesEl.scrollTop = messagesEl.scrollHeight;
        return wrapper;
    };

    const clearMessages = () => {
        messagesEl.innerHTML = '';
        chatId = null;
    };

    const updatePendingMessage = (wrapper, text) => {
        if (!wrapper) return;
        wrapper.dataset.pending = 'false';
        const textEl = wrapper.querySelector('.text');
        if (textEl) textEl.textContent = text;
    };

    const setSendingState = (state) => {
        sending = state;
        promptInput.disabled = state;
    };

    const sendMessage = async (message) => {
        if (!message || sending) return;
        setSendingState(true);

        appendMessage('user', message);
        const pending = appendMessage('assistant', '…', true);

        try {
            const res = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message,
                    chat_id: chatId,
                    task: 'text_generation',
                    model: 'thor-1.0'
                })
            });

            if (!res.ok) {
                const err = await res.json().catch(() => ({}));
                throw new Error(err.error || `HTTP ${res.status}`);
            }

            const data = await res.json();
            chatId = data.chat_id || chatId;
            updatePendingMessage(pending, data.response || '(no response)');
        } catch (err) {
            console.error(err);
            updatePendingMessage(pending, `Error: ${err.message}`);
        } finally {
            setSendingState(false);
        }
    };

    promptForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const val = promptInput.value.trim();
        if (!val) return;
        sendMessage(val);
        promptInput.value = '';
    });

    newChatBtn.addEventListener('click', () => {
        clearMessages();
        promptInput.focus();
    });

    // Focus input on load
    promptInput.focus();
})();


