// Atlas AI - Thor 1.0 Frontend
let currentChatId = null;
let isLoading = false;
let thinkDeeperMode = false;
let allChats = [];
let currentTheme = 'light';
let themePreference = 'system';
let currentModel = 'thor-1.0';  // Track selected model
const PRO_ACCESS_CODE = 'QUANTUM4FUTURE';
let currentTone = 'normal';
let systemMode = localStorage.getItem('systemMode') || 'latest';
let uiMode = localStorage.getItem('uiMode') || 'standard';

// Gems (custom sub-models)
let gems = [];
let activeGemDraft = null; 

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
});

async function initializeApp() {
    initializeTheme();
    initializeTone();
    initializeSystemMode();
    initializeUIMode();
    restoreModelPreference();
    await loadGems();
    loadChats();
    setupEventListeners();
    checkModelStatus();
    initializePoseidon();
    
    // Restore Pro unlock UI if previously unlocked
    if (localStorage.getItem('proUnlocked') === 'true') {
        applyProUnlockedUI();
    }

    // Restore tone (initializeTone wires UI listeners)
    currentTone = localStorage.getItem('atlasTone') || 'normal';
}

function restoreModelPreference() {
    // Load saved model preference - Gems are not in dropdown, only accessible via sidebar
    const savedModel = localStorage.getItem('selectedModel') || 'thor-1.0';
    // If a gem is saved, keep it (for sidebar access) but default dropdown to Thor 1.0
    // Gems can still be selected via sidebar, just not shown in dropdown
    if (savedModel && savedModel.startsWith('gem:')) {
        currentModel = savedModel; // Keep gem selection for sidebar
    } else {
        currentModel = savedModel || 'thor-1.0';
    }
    // UI will be updated after `loadGems()` rebuilds the dropdown.
    // Apply a default tone immediately; `loadGems()` may override with a Gem tone.
    document.body.setAttribute('data-tone', currentTone || 'normal');
}

function setupEventListeners() {
    const sendBtn = document.getElementById('sendBtn');
    const messageInput = document.getElementById('messageInput');
    const newChatBtn = document.getElementById('newChatBtn');
    const attachBtn = document.getElementById('attachBtn');
    const thinkDeeperToggle = document.getElementById('thinkDeeperToggle');
    const historyBtn = document.getElementById('historyBtn');
    // History header button removed (duplicate of history button in input area)
    // const historyHeaderBtn = document.getElementById('historyHeaderBtn');
    const modelSelector = document.getElementById('modelSelector');
    const sidebarMenuBtn = document.getElementById('sidebarMenuBtn');
    const settingsBtn = document.getElementById('settingsBtn');
    const upgradeBtn = document.getElementById('upgradeBtn');
    const newProjectBtn = document.getElementById('newProjectBtn');
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    const helpBtn = document.getElementById('helpBtn');
    const customizeBtn = document.getElementById('customizeBtn');
    const newGemBtn = document.getElementById('newGemBtn');
    
    sendBtn.addEventListener('click', handleSendMessage);
    newChatBtn.addEventListener('click', startNewChat);
    attachBtn.addEventListener('click', handleAttach);
    thinkDeeperToggle.addEventListener('click', toggleThinkDeeper);
    if (historyBtn) historyBtn.addEventListener('click', handleHistory);
    modelSelector.addEventListener('click', toggleModelDropdown);
    
    if (sidebarMenuBtn) sidebarMenuBtn.addEventListener('click', toggleSidebar);
    if (settingsBtn) settingsBtn.addEventListener('click', openSettingsModal);
    if (upgradeBtn) upgradeBtn.addEventListener('click', openUpgradeModal);
    if (newProjectBtn) newProjectBtn.addEventListener('click', () => openProjectModal());
    if (helpBtn) helpBtn.addEventListener('click', openHelpModal);
    if (customizeBtn) customizeBtn.addEventListener('click', openCustomizeModal);
    if (newGemBtn) newGemBtn.addEventListener('click', () => {
        openCustomizeModal();
        openGemEditor(); // new gem
    });
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const base = themePreference === 'system' ? currentTheme : themePreference;
            const nextTheme = base === 'light' ? 'dark' : 'light';
            setTheme(nextTheme);
        });
    }
    
    // Settings modal
    const closeSettingsModal = document.getElementById('closeSettingsModal');
    if (closeSettingsModal) closeSettingsModal.addEventListener('click', closeSettingsModalFunc);

    // Help modal
    const closeHelpModal = document.getElementById('closeHelpModal');
    if (closeHelpModal) closeHelpModal.addEventListener('click', closeHelpModalFunc);

    // Customize (Gems) modal
    const closeCustomizeModal = document.getElementById('closeCustomizeModal');
    if (closeCustomizeModal) closeCustomizeModal.addEventListener('click', closeCustomizeModalFunc);
    const createGemBtn = document.getElementById('createGemBtn');
    if (createGemBtn) createGemBtn.addEventListener('click', () => openGemEditor());
    const cancelGemEditBtn = document.getElementById('cancelGemEditBtn');
    if (cancelGemEditBtn) cancelGemEditBtn.addEventListener('click', closeGemEditor);
    const tryGemBtn = document.getElementById('tryGemBtn');
    if (tryGemBtn) tryGemBtn.addEventListener('click', tryGemFromEditor);
    const gemForm = document.getElementById('gemForm');
    if (gemForm) gemForm.addEventListener('submit', handleGemSubmit);
    
    // Upgrade modal
    const closeUpgradeModal = document.getElementById('closeUpgradeModal');
    if (closeUpgradeModal) closeUpgradeModal.addEventListener('click', closeUpgradeModalFunc);
    const proAccessBtn = document.getElementById('proAccessBtn');
    if (proAccessBtn) proAccessBtn.addEventListener('click', handleProAccessUnlock);
    
    // Project modal
    const projectForm = document.getElementById('projectForm');
    const closeProjectModal = document.getElementById('closeProjectModal');
    const cancelProjectBtn = document.getElementById('cancelProjectBtn');
    if (projectForm) projectForm.addEventListener('submit', handleProjectSubmit);
    if (closeProjectModal) closeProjectModal.addEventListener('click', closeProjectModalFunc);
    if (cancelProjectBtn) cancelProjectBtn.addEventListener('click', closeProjectModalFunc);
    
    // History modal
    const closeHistoryModal = document.getElementById('closeHistoryModal');
    if (closeHistoryModal) closeHistoryModal.addEventListener('click', closeHistoryModalFunc);
    
    // Quick prompts on welcome screen
    document.querySelectorAll('.quick-prompt-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const prompt = btn.getAttribute('data-prompt') || '';
            const sendMessage = btn.getAttribute('data-send-message');
            
            if (sendMessage) {
                messageInput.value = sendMessage;
                autoResizeTextarea(messageInput);
                handleSendMessage();
                return;
            }
            
            messageInput.value = prompt;
            autoResizeTextarea(messageInput);
            messageInput.focus();
        });
    });
    
    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });
    
    messageInput.addEventListener('input', () => {
        autoResizeTextarea(messageInput);
    });
}

function handleProAccessUnlock() {
    const entered = prompt('Enter your access code to unlock Pro:');
    if (!entered) return;
    if (entered.trim() === PRO_ACCESS_CODE) {
        localStorage.setItem('proUnlocked', 'true');
        applyProUnlockedUI();
        showProUnlockAnimation();
    } else {
        alert('Invalid code. Please check and try again.');
    }
}

function applyProUnlockedUI() {
    document.body.classList.add('pro-unlocked');
    const proBadge = document.querySelector('.plan-badge-coming');
    if (proBadge) proBadge.textContent = 'Pro Unlocked';
    const proBtn = document.getElementById('proAccessBtn');
    if (proBtn) {
        proBtn.textContent = 'Pro Unlocked';
        proBtn.disabled = true;
    }
    const statusPill = document.querySelector('.pill.gold');
    if (statusPill) statusPill.textContent = 'Pro Unlocked';
    
    const freeCard = document.getElementById('freePlanCard');
    const proCard = document.getElementById('proPlanCard');
    const freeBadge = document.querySelector('.plan-badge-current');
    if (freeCard) freeCard.classList.remove('active');
    if (proCard) proCard.classList.add('active');
    if (freeBadge) freeBadge.textContent = 'Free';
    
    injectProVine();
}

function showProUnlockAnimation() {
    const existing = document.getElementById('proUnlockOverlay');
    if (existing) existing.remove();
    const overlay = document.createElement('div');
    overlay.id = 'proUnlockOverlay';
    overlay.innerHTML = `
        <div class="pro-unlock-card">
            <div class="pro-unlock-orb"></div>
            <div class="pro-unlock-text">Pro Unlocked!</div>
        </div>
    `;
    document.body.appendChild(overlay);
    requestAnimationFrame(() => overlay.classList.add('visible'));
    setTimeout(() => {
        overlay.classList.remove('visible');
        setTimeout(() => overlay.remove(), 450);
    }, 1600);
}

function injectProVine() {
    // Pro header badge removed per design request; ensure any existing badge is cleaned up.
    const existing = document.getElementById('proVine');
    if (existing) existing.remove();
    return;
}

function autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 200) + 'px';
}

async function checkModelStatus() {
    try {
        const response = await fetch('/api/model/status');
        const data = await response.json();
        
        if (!data.loaded) {
            console.warn('Model not loaded');
        }
    } catch (error) {
        console.error('Error checking model status:', error);
    }
}

async function loadChats() {
    try {
        const response = await fetch('/api/chats');
        const data = await response.json();
        allChats = Array.isArray(data.chats) ? data.chats : [];
        displayChats(allChats);
    } catch (error) {
        console.error('Error loading chats:', error);
        document.getElementById('chatsList').innerHTML = 
            '<div class="chats-loading">Error loading chats</div>';
    }
}

function displayChats(chats) {
    const chatsList = document.getElementById('chatsList');
    
    if (chats.length === 0) {
        chatsList.innerHTML = '<div class="chats-loading">No chats yet</div>';
        return;
    }
    
    chatsList.innerHTML = chats.map(chat => {
        const title = getChatTitle(chat);
        
        return `
            <button class="chat-item ${chat.chat_id === currentChatId ? 'active' : ''}" 
                 data-chat-id="${chat.chat_id}">
                <span class="chat-item-title">${escapeHtml(title)}</span>
                <span class="chat-delete-btn" data-chat-id="${chat.chat_id}" onclick="event.stopPropagation(); deleteChat('${chat.chat_id}')" title="Delete chat" role="button" tabindex="0">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                        <path d="M3.5 3.5L10.5 10.5M10.5 3.5L3.5 10.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                    </svg>
                </span>
            </button>
        `;
    }).join('');
    
    // Add click listeners
    chatsList.querySelectorAll('.chat-item').forEach(item => {
        item.addEventListener('click', (e) => {
            // Don't trigger if clicking delete button
            if (e.target.closest('.chat-delete-btn')) return;
            const chatId = item.dataset.chatId;
            loadChat(chatId);
        });
    });
    
    // Add keyboard support for delete button
    chatsList.querySelectorAll('.chat-delete-btn').forEach(btn => {
        btn.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                e.stopPropagation();
                deleteChat(btn.dataset.chatId);
            }
        });
    });
}

function getChatTitle(chat) {
    if (chat.name) return chat.name;
    if (chat.created_at) {
        try {
            const date = new Date(chat.created_at);
            if (!isNaN(date.getTime())) {
                return `Chat from ${date.toLocaleDateString()}`;
            }
        } catch (error) {
            console.warn('Error parsing chat date', error);
        }
    }
    return 'Untitled chat';
}

async function loadChat(chatId) {
    try {
        const response = await fetch(`/api/chats/${chatId}`);
        const data = await response.json();
        
        currentChatId = chatId;
        displayMessages(data.messages);
        updateChatList();
        
        // Hide welcome screen, show messages
        document.getElementById('welcomeScreen').style.display = 'none';
        document.getElementById('messagesContainer').style.display = 'block';
    } catch (error) {
        console.error('Error loading chat:', error);
    }
}

function displayMessages(messages) {
    const container = document.getElementById('messagesContainer');
    
    container.innerHTML = messages.map(msg => {
        const role = msg.role;
        const content = msg.content;
        const avatar = role === 'user' ? 'U' : 'A';
        
        // Render markdown for assistant messages
        const renderedContent = role === 'assistant' 
            ? renderMarkdown(content) 
            : escapeHtml(content);
        
        return `
            <div class="message ${role}">
                <div class="message-avatar">${avatar}</div>
                <div class="message-content">${renderedContent}</div>
            </div>
        `;
    }).join('');
    
    scrollToBottom();
}

function startNewChat() {
    currentChatId = null;
    document.getElementById('welcomeScreen').style.display = 'block';
    document.getElementById('messagesContainer').style.display = 'none';
    document.getElementById('messagesContainer').innerHTML = '';
    document.getElementById('messageInput').value = '';
    updateChatList();
}

function updateChatList() {
    loadChats();
}

async function handleSendMessage() {
    const messageInput = document.getElementById('messageInput');
    const message = messageInput.value.trim();
    
    if (!message || isLoading) return;
    
    // Check for easter egg: "I am in C5."
    if (message === "I am in C5.") {
        showEasterEgg();
        messageInput.value = '';
        return;
    }
    
    // Check for command shortcuts
    const messageLower = message.toLowerCase().trim();
    if (messageLower === '/office' || messageLower.startsWith('/office ')) {
        messageInput.value = 'Load Office Suite';
        handleSendMessage();
        return;
    }
    if (messageLower === '/arcade' || messageLower.startsWith('/arcade ')) {
        messageInput.value = 'Load Game Suite';
        handleSendMessage();
        return;
    }
    if (messageLower.startsWith('/image ')) {
        const imageDesc = message.substring(7).trim();
        if (imageDesc) {
            messageInput.value = `Create an image of ${imageDesc}`;
            handleSendMessage();
            return;
        }
    }
    
    isLoading = true;
    updateSendButton(true);
    
    // Hide welcome screen if showing
    const welcomeScreen = document.getElementById('welcomeScreen');
    const messagesContainer = document.getElementById('messagesContainer');
    
    if (welcomeScreen.style.display !== 'none') {
        welcomeScreen.style.display = 'none';
        messagesContainer.style.display = 'block';
    }
    
    // Add user message to UI
    addMessageToUI('user', message);
    messageInput.value = '';
    autoResizeTextarea(messageInput);
    
    // Show loading indicator
    const loadingId = addMessageToUI('assistant', '', true);
    
    // If think deeper mode, show thinking message
    if (thinkDeeperMode) {
        const thinkingMsg = addMessageToUI('assistant', 'Thinking deeper...', false);
        setTimeout(() => {
            const msgDiv = document.getElementById(thinkingMsg);
            if (msgDiv) {
                msgDiv.remove();
            }
        }, 1000);
    }
    
    try {
        const requestBody = {
            message: message,
            chat_id: currentChatId,
            task: 'text_generation',
            think_deeper: thinkDeeperMode,
            model: currentModel,  // Include selected model
            tone: getEffectiveTone(),
        };

        // If we're trying a Gem (preview), include the draft config
        if (currentModel === 'gem:preview' && activeGemDraft) {
            requestBody.gem_draft = activeGemDraft;
        }
        
        // Add image if pending
        if (window.pendingImage) {
            requestBody.image_data = window.pendingImage.data;
            requestBody.image_filename = window.pendingImage.filename;
            window.pendingImage = null;
        }
        
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        });
        
        if (!response.ok) {
            // Try to get error message
            let errorData = {};
            try {
                errorData = await response.json();
            } catch (e) {
                errorData = { error: `HTTP ${response.status}: ${response.statusText}` };
            }
            throw new Error(errorData.error || errorData.response || `HTTP ${response.status}: ${response.statusText}`);
        }
        
        let data;
        try {
            data = await response.json();
        } catch (jsonError) {
            console.error('Error parsing JSON response:', jsonError);
            const text = await response.text();
            console.error('Response text:', text.substring(0, 500));
            throw new Error(`Failed to parse server response: ${jsonError.message}`);
        }
        
        // Check if response has error field
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Ensure we have a response field
        if (!data.response) {
            console.error('No response field in data:', data);
            throw new Error('Server returned invalid response format');
        }
        
        // Update current chat ID
        currentChatId = data.chat_id;
        
        // Replace loading with actual response
        replaceLoadingMessage(loadingId, data.response || 'No response received');
        
        // Reload chats list
        loadChats();
    } catch (error) {
        console.error('Error sending message:', error);
        console.error('Error type:', error.constructor.name);
        console.error('Error stack:', error.stack);
        const errorMessage = error.message || 'Unknown error';
        console.error('Full error details:', {
            message: errorMessage,
            stack: error.stack,
            name: error.name,
            cause: error.cause
        });
        // Show more helpful error message
        let userFriendlyError = errorMessage;
        if (errorMessage.includes('Failed to fetch') || errorMessage.includes('NetworkError')) {
            userFriendlyError = 'Cannot connect to server. Please make sure the server is running (python app.py)';
        } else if (errorMessage.includes('parse')) {
            userFriendlyError = 'Server returned invalid response. Please check server logs.';
        }
        replaceLoadingMessage(loadingId, `Sorry, I encountered an error: ${userFriendlyError}. Please check the browser console (F12) for details.`);
    } finally {
        isLoading = false;
        updateSendButton(false);
    }
}

function addMessageToUI(role, content, isLoading = false) {
    const container = document.getElementById('messagesContainer');
    const messageId = 'msg-' + Date.now() + '-' + Math.random();
    
    const avatar = role === 'user' ? 'U' : 'A';
    let messageContent;
    
    if (isLoading) {
        messageContent = '<div class="loading"></div>';
    } else if (role === 'assistant') {
        // Render markdown for assistant messages
        messageContent = renderMarkdown(content);
    } else {
        // Escape HTML for user messages
        messageContent = escapeHtml(content);
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    messageDiv.id = messageId;
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">${messageContent}</div>
    `;
    
    container.appendChild(messageDiv);
    scrollToBottom();
    
    return messageId;
}

function replaceLoadingMessage(messageId, content) {
    const messageDiv = document.getElementById(messageId);
    if (messageDiv) {
        const contentDiv = messageDiv.querySelector('.message-content');
        // Render markdown for assistant responses
        contentDiv.innerHTML = renderMarkdown(content);
    }
}

function scrollToBottom() {
    const container = document.getElementById('messagesContainer');
    container.scrollTop = container.scrollHeight;
}

function updateSendButton(disabled) {
    const sendBtn = document.getElementById('sendBtn');
    sendBtn.disabled = disabled;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function renderMarkdown(text) {
    if (!text) return '';
    
    // Normalize TrainX Q/A syntax (e.g., "A: https://...") into iframe + img tokens
    let processed = text.replace(/A:\s*(https?:\/\/[^\s)]+)\s*$/gm, (match, url) => {
        return `{{TRAINX_IFRAME:${url}}}\n![Image](${url})`;
    });

    // Collect markdown image URLs so we can suppress duplicate TrainX iframe tokens
    const markdownImageUrls = new Set();
    processed.replace(/!\[[^\]]*\]\((https?:\/\/[^\s)]+)\)/g, (match, url) => {
        markdownImageUrls.add(url.trim());
        return match;
    });

    // Extract TrainX iframe tokens before escaping
    const iframeTokens = [];
    const seenIframeUrls = new Set();
    processed = processed.replace(/\{\{TRAINX_IFRAME:([^\}]+)\}\}/g, (match, url) => {
        const normalizedUrl = url.trim();
        // If we already have a markdown image for this URL (TrainX image pair) or saw this iframe, drop the extra token
        if (markdownImageUrls.has(normalizedUrl) || seenIframeUrls.has(normalizedUrl)) {
            return '';
        }
        seenIframeUrls.add(normalizedUrl);

        const token = `__IFRAME_TOKEN_${iframeTokens.length}__`;
        const safeUrl = normalizedUrl.replace(/"/g, '%22');
        iframeTokens.push(`<div class="markdown-media"><iframe src="${safeUrl}" class="trainx-frame" loading="lazy" referrerpolicy="no-referrer"></iframe></div>`);
        return token;
    });

    // FIRST: Extract images BEFORE escaping HTML (brackets get escaped otherwise)
    const imageTokens = [];
    processed = processed.replace(/!\[([^\]]*)\]\((https?:\/\/[^\s)]+)\)/g, (match, alt, url) => {
        const token = `__IMG_TOKEN_${imageTokens.length}__`;
        const safeAlt = (alt || 'Image').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
        const safeUrl = url.replace(/"/g, '%22');
        imageTokens.push(`<div class="markdown-media"><img src="${safeUrl}" alt="${safeAlt}" loading="lazy" class="markdown-img" onerror="this.onerror=null; this.src='https://placehold.co/800x600/5a5df0/ffffff?text=Image+not+found'"></div>`);
        return token;
    });
    
    // Now escape HTML
    let html = escapeHtml(processed);
    
    // Restore image tokens
    imageTokens.forEach((imgHtml, i) => {
        html = html.replace(`__IMG_TOKEN_${i}__`, imgHtml);
    });

    // Restore iframe tokens
    iframeTokens.forEach((frameHtml, i) => {
        html = html.replace(`__IFRAME_TOKEN_${i}__`, frameHtml);
    });
    
    // Code blocks (```language\ncode\n```) - process first to avoid interfering with other markdown
    html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
        const language = lang || 'text';
        return `__CODE_BLOCK_START__${language}__CODE_SEP__${code.trim()}__CODE_BLOCK_END__`;
    });
    
    // Inline code (`code`)
    html = html.replace(/`([^`\n]+)`/g, '<code class="inline-code">$1</code>');
    
    // Headers (# Header, ## Header, ### Header) - Enhanced with better styling classes
    html = html.replace(/^### (.*$)/gm, '<h3 class="markdown-h3 md-h3">$1</h3>');
    html = html.replace(/^## (.*$)/gm, '<h2 class="markdown-h2 md-h2">$1</h2>');
    html = html.replace(/^# (.*$)/gm, '<h1 class="markdown-h1 md-h1">$1</h1>');
    
    // Bold (**text** or __text__) - with enhanced styling
    html = html.replace(/\*\*([^*\n]+)\*\*/g, '<strong class="md-bold">$1</strong>');
    html = html.replace(/__([^_\n]+)__(?!CODE)/g, '<strong class="md-bold">$1</strong>');
    
    // Italic (*text* or _text_) - single asterisk/underscore
    html = html.replace(/(?<!\*)\*([^*\n]+)\*(?!\*)/g, '<em class="md-italic">$1</em>');
    html = html.replace(/(?<!_)_([^_\n]+)_(?!_)/g, '<em class="md-italic">$1</em>');
    
    // Blockquotes (> text)
    html = html.replace(/^&gt;\s*(.+)$/gm, '<blockquote class="md-blockquote">$1</blockquote>');
    
    // Horizontal rules (---, ***, ___)
    html = html.replace(/^[-*_]{3,}$/gm, '<hr class="md-hr">');
    
    // Links [text](url)
    html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, 
        '<a href="$2" target="_blank" rel="noopener noreferrer" class="md-link">$1</a>');
    
    // Bullet points (- item or * item)
    const lines = html.split('\n');
    let result = [];
    let inList = false;
    let listItems = [];
    let listType = 'ul';
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const bulletMatch = line.match(/^[\-\*] (.+)$/);
        const numberedMatch = line.match(/^(\d+)\. (.+)$/);
        
        if (bulletMatch) {
            if (!inList || listType !== 'ul') {
                if (inList) {
                    result.push(`<${listType} class="markdown-${listType} md-list">${listItems.join('')}</${listType}>`);
                }
                listItems = [];
                inList = true;
                listType = 'ul';
            }
            listItems.push(`<li class="markdown-li md-li">${bulletMatch[1]}</li>`);
        } else if (numberedMatch) {
            if (!inList || listType !== 'ol') {
                if (inList) {
                    result.push(`<${listType} class="markdown-${listType} md-list">${listItems.join('')}</${listType}>`);
                }
                listItems = [];
                inList = true;
                listType = 'ol';
            }
            listItems.push(`<li class="markdown-li md-li">${numberedMatch[2]}</li>`);
        } else {
            if (inList) {
                result.push(`<${listType} class="markdown-${listType} md-list">${listItems.join('')}</${listType}>`);
                listItems = [];
                inList = false;
            }
            if (line.trim()) {
                result.push(line);
            }
        }
    }
    
    if (inList && listItems.length > 0) {
        result.push(`<${listType} class="markdown-${listType} md-list">${listItems.join('')}</${listType}>`);
    }
    
    html = result.join('\n');
    
    // Restore code blocks with syntax highlighting class
    html = html.replace(/__CODE_BLOCK_START__(\w+)__CODE_SEP__([\s\S]*?)__CODE_BLOCK_END__/g, 
        (match, lang, code) => {
            return `<pre class="code-block md-code-block"><code class="language-${lang}">${code}</code></pre>`;
        });
    
    // Convert double newlines to paragraph breaks
    html = html.split('\n\n').map(para => {
        para = para.trim();
        if (!para) return '';
        // Don't wrap if it's already a block element
        if (/^<(h[1-6]|ul|ol|pre|code|figure|blockquote|hr|div)/.test(para)) {
            return para;
        }
        return `<p class="markdown-p md-p">${para}</p>`;
    }).join('');
    
    // Clean up empty paragraphs
    html = html.replace(/<p class="markdown-p md-p"><\/p>/g, '');
    
    // Handle single newlines as line breaks within paragraphs
    html = html.replace(/([^>])\n([^<])/g, '$1<br>$2');
    
    return html;
}

async function deleteChat(chatId) {
    if (!confirm('Are you sure you want to delete this chat?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/chats/${chatId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            // If deleted chat was current, start new chat
            if (currentChatId === chatId) {
                startNewChat();
            }
            // Reload chat list
            loadChats();
        } else {
            alert('Error deleting chat');
        }
    } catch (error) {
        console.error('Error deleting chat:', error);
        alert('Error deleting chat');
    }
}

function handleAttach() {
    // Create file input for attachments (text and images)
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'text/*,.txt,.md,.json,image/*,.png,.jpg,.jpeg,.gif,.webp';
    input.onchange = (e) => {
        const file = e.target.files[0];
        if (file) {
            if (file.type.startsWith('image/')) {
                // Handle image
                const reader = new FileReader();
                reader.onload = (event) => {
                    const imageData = event.target.result;
                    // Send image for processing
                    processImage(imageData, file.name);
                };
                reader.readAsDataURL(file);
            } else {
                // Handle text file
                const reader = new FileReader();
                reader.onload = (event) => {
                    const content = event.target.result;
                    const messageInput = document.getElementById('messageInput');
                    messageInput.value = content.substring(0, 1000);
                    autoResizeTextarea(messageInput);
                };
                reader.readAsText(file);
            }
        }
    };
    input.click();
}

function processImage(imageData, filename) {
    // Add image processing message
    const messageInput = document.getElementById('messageInput');
    messageInput.value = `[Image: ${filename}] Describe this image`;
    autoResizeTextarea(messageInput);
    
    // Store image data for sending
    window.pendingImage = {
        data: imageData,
        filename: filename
    };
}

function toggleModelDropdown(e) {
    e.stopPropagation();
    const dropdown = document.getElementById('modelDropdown');
    const isOpen = dropdown.classList.contains('open');
    
    // Close all dropdowns first
    document.querySelectorAll('.model-dropdown').forEach(d => d.classList.remove('open'));
    
    // Toggle this dropdown
    if (!isOpen) {
        // Ensure dropdown reflects current gem/preview state
        rebuildModelDropdown();
        dropdown.classList.add('open');
        
        // Close when clicking outside
        setTimeout(() => {
            document.addEventListener('click', function closeDropdown() {
                dropdown.classList.remove('open');
                document.removeEventListener('click', closeDropdown);
            }, { once: true });
        }, 0);
    }
}

function selectModel(e) {
    const modelOption = e.currentTarget;
    const selectedModel = modelOption.getAttribute('data-model');
    if (!selectedModel) return;
    const wasPreview = currentModel === 'gem:preview';
    currentModel = selectedModel;
    
    // If leaving preview, drop it from the dropdown (so it doesn't "stick")
    if (wasPreview && selectedModel !== 'gem:preview') {
        activeGemDraft = null;
    }

    // Save preference to localStorage
    localStorage.setItem('selectedModel', selectedModel);
    
    // Rebuild to reflect any preview removal + correct active state
    rebuildModelDropdown();
    updateModelDisplay();
    renderGemsSidebar();
    
    // Close dropdown
    const dropdown = document.getElementById('modelDropdown');
    dropdown.classList.remove('open');
    
    console.log('Switched to model:', selectedModel);
}

function toggleThinkDeeper() {
    thinkDeeperMode = !thinkDeeperMode;
    const toggle = document.getElementById('thinkDeeperToggle');
    if (toggle) {
        if (thinkDeeperMode) {
            toggle.classList.add('active');
            toggle.title = 'Think Deeper Mode: ON';
        } else {
            toggle.classList.remove('active');
            toggle.title = 'Think Deeper Mode: OFF';
        }
    }
    console.log('Think Deeper Mode:', thinkDeeperMode ? 'ON' : 'OFF');
}

function handleHistory() {
    openHistoryModal();
}

function openHistoryModal() {
    const modal = document.getElementById('historyModal');
    if (modal) {
        modal.style.display = 'flex';
        loadHistory();
    }
}

function closeHistoryModalFunc() {
    const modal = document.getElementById('historyModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

async function loadHistory() {
    try {
        const response = await fetch('/api/history?limit=100');
        const data = await response.json();
        displayHistory(data.history || []);
    } catch (error) {
        console.error('Error loading history:', error);
        const historyList = document.getElementById('historyList');
        if (historyList) {
            historyList.innerHTML = '<div class="chats-loading">Error loading history</div>';
        }
    }
}

function displayHistory(history) {
    const historyList = document.getElementById('historyList');
    if (!historyList) return;
    
    if (history.length === 0) {
        historyList.innerHTML = '<div class="chats-loading">No history yet</div>';
        return;
    }
    
    historyList.innerHTML = history.map(entry => {
        const date = new Date(entry.timestamp);
        const typeIcon = entry.type === 'chat' ? '💬' : entry.type === 'project' ? '📁' : '📝';
        
        return `
            <div class="history-item" data-entry-id="${entry.id}">
                <div class="history-icon">${typeIcon}</div>
                <div class="history-content">
                    <div class="history-title">${escapeHtml(entry.title || entry.description || 'Untitled')}</div>
                    <div class="history-meta">
                        <span class="history-type">${entry.type}</span>
                        <span class="history-date">${date.toLocaleString()}</span>
                    </div>
                </div>
                <button class="history-delete-btn" onclick="event.stopPropagation(); deleteHistoryEntry('${entry.id}')" title="Delete">
                    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                        <path d="M3.5 3.5L10.5 10.5M10.5 3.5L3.5 10.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                    </svg>
                </button>
            </div>
        `;
    }).join('');
    
    // Add click listeners
    historyList.querySelectorAll('.history-item').forEach(item => {
        item.addEventListener('click', (e) => {
            if (e.target.closest('.history-delete-btn')) return;
            const entryId = item.dataset.entryId;
            const entry = history.find(h => h.id === entryId);
            if (entry) {
                if (entry.chat_id) {
                    loadChat(entry.chat_id);
                    closeHistoryModalFunc();
                } else if (entry.project_id) {
                    switchView('projects');
                    loadProject(entry.project_id);
                    closeHistoryModalFunc();
                }
            }
        });
    });
}

async function deleteHistoryEntry(entryId) {
    if (!confirm('Delete this history entry?')) return;
    
    try {
        const response = await fetch(`/api/history/${entryId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadHistory();
        }
    } catch (error) {
        console.error('Error deleting history entry:', error);
    }
}

// ==================== PROJECTS FUNCTIONS ====================

function switchView(view) {
    const chatsSection = document.querySelector('.chats-section');
    const projectsSection = document.getElementById('projectsSection');
    
    if (view === 'chats') {
        if (chatsSection) chatsSection.style.display = 'block';
        if (projectsSection) projectsSection.style.display = 'none';
        loadChats();
    } else if (view === 'projects') {
        if (chatsSection) chatsSection.style.display = 'none';
        if (projectsSection) projectsSection.style.display = 'block';
        loadProjects();
    }
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
        sidebar.classList.toggle('collapsed');
        document.body.classList.toggle('sidebar-collapsed', sidebar.classList.contains('collapsed'));
        // Create or update floating toggle button
        updateFloatingToggle();
    }
}

function updateFloatingToggle() {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.querySelector('.main-content');
    let floatingBtn = document.getElementById('sidebarToggleFloat');
    
    if (sidebar && sidebar.classList.contains('collapsed')) {
        // Create floating button if it doesn't exist
        if (!floatingBtn) {
            floatingBtn = document.createElement('button');
            floatingBtn.id = 'sidebarToggleFloat';
            floatingBtn.className = 'sidebar-toggle-float';
            floatingBtn.title = 'Toggle Sidebar';
            floatingBtn.innerHTML = `
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <path d="M3 12H21M3 6H21M3 18H21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
                </svg>
            `;
            floatingBtn.addEventListener('click', toggleSidebar);
            if (mainContent) {
                mainContent.appendChild(floatingBtn);
            }
        }
        floatingBtn.style.display = 'flex';
    } else {
        // Hide floating button when sidebar is visible
        if (floatingBtn) {
            floatingBtn.style.display = 'none';
        }
    }
}

function openSettingsModal() {
    const modal = document.getElementById('settingsModal');
    if (modal) {
        modal.style.display = 'flex';
    }
}

function closeSettingsModalFunc() {
    const modal = document.getElementById('settingsModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function openUpgradeModal() {
    const modal = document.getElementById('upgradeModal');
    if (modal) {
        modal.style.display = 'flex';
    }
}

function closeUpgradeModalFunc() {
    const modal = document.getElementById('upgradeModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function openHelpModal() {
    const modal = document.getElementById('helpModal');
    if (modal) {
        modal.style.display = 'flex';
    }
}

function closeHelpModalFunc() {
    const modal = document.getElementById('helpModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function openCustomizeModal() {
    const modal = document.getElementById('customizeModal');
    if (modal) {
        modal.style.display = 'flex';
        renderGemTryTemplates();
        renderGemsManageList();
    }
}

function closeCustomizeModalFunc() {
    const modal = document.getElementById('customizeModal');
    if (modal) {
        modal.style.display = 'none';
    }
    closeGemEditor();
}

function initializeTheme() {
    const savedTheme = localStorage.getItem('atlasTheme') || 'system';
    themePreference = savedTheme;
    setTheme(savedTheme);
    const systemMedia = window.matchMedia('(prefers-color-scheme: dark)');
    if (systemMedia.addEventListener) {
        systemMedia.addEventListener('change', () => {
            if (themePreference === 'system') {
                setTheme('system');
            }
        });
    }
    const themeInputs = document.querySelectorAll('input[name="theme"]');
    themeInputs.forEach(input => {
        input.checked = input.value === savedTheme;
        input.addEventListener('change', (event) => {
            setTheme(event.target.value);
        });
    });
}

function initializeTone() {
    const saved = localStorage.getItem('atlasTone') || 'normal';
    currentTone = saved;
    document.body.setAttribute('data-tone', currentTone);
    document.querySelectorAll('input[name="tone"]').forEach(input => {
        input.checked = input.value === saved;
        input.addEventListener('change', (e) => {
            currentTone = e.target.value;
            localStorage.setItem('atlasTone', currentTone);
            document.body.setAttribute('data-tone', currentTone);
        });
    });
}

function initializeSystemMode() {
    const savedMode = localStorage.getItem('systemMode') || 'latest';
    systemMode = savedMode;
    const modeSelect = document.getElementById('systemMode');
    if (modeSelect) {
        modeSelect.value = savedMode;
        modeSelect.addEventListener('change', (e) => {
            systemMode = e.target.value;
            localStorage.setItem('systemMode', systemMode);
            applyStableMode(systemMode);
        });
    }
    applyStableMode(systemMode);
}

function applyStableMode(mode) {
    if (mode === 'stable') {
        document.body.classList.add('stable-mode');
        // Disable latest features
        const poseidonBtn = document.getElementById('poseidonLaunchBtn');
        if (poseidonBtn) {
            poseidonBtn.style.display = 'none';
        }
        // Hide advanced features
        const thinkDeeperBtn = document.getElementById('thinkDeeperToggle');
        if (thinkDeeperBtn) {
            thinkDeeperBtn.style.display = 'none';
        }
        // Use simpler UI by default in stable mode
        if (uiMode === 'standard') {
            uiMode = 'simple';
            localStorage.setItem('uiMode', 'simple');
            const uiModeSelect = document.getElementById('uiMode');
            if (uiModeSelect) uiModeSelect.value = 'simple';
            applyUIMode('simple');
        }
    } else {
        document.body.classList.remove('stable-mode');
        // Re-enable features
        const poseidonBtn = document.getElementById('poseidonLaunchBtn');
        if (poseidonBtn) {
            poseidonBtn.style.display = '';
        }
        const thinkDeeperBtn = document.getElementById('thinkDeeperToggle');
        if (thinkDeeperBtn) {
            thinkDeeperBtn.style.display = '';
        }
    }
}

function initializeUIMode() {
    const savedUIMode = localStorage.getItem('uiMode') || 'standard';
    uiMode = savedUIMode;
    const uiModeSelect = document.getElementById('uiMode');
    if (uiModeSelect) {
        uiModeSelect.value = savedUIMode;
        uiModeSelect.addEventListener('change', (e) => {
            uiMode = e.target.value;
            localStorage.setItem('uiMode', uiMode);
            document.body.setAttribute('data-ui-mode', uiMode);
            applyUIMode(uiMode);
        });
    }
    applyUIMode(uiMode);
}

function applyUIMode(mode) {
    if (mode === 'simple') {
        document.body.classList.add('ui-simple');
        // Hide non-essential elements
        const thinkDeeperBtn = document.getElementById('thinkDeeperToggle');
        const historyBtn = document.getElementById('historyBtn');
        const customizeBtn = document.getElementById('customizeBtn');
        const helpBtn = document.getElementById('helpBtn');
        const upgradeBtn = document.getElementById('upgradeBtn');
        const modelSelector = document.getElementById('modelSelector');
        
        if (thinkDeeperBtn) thinkDeeperBtn.style.display = 'none';
        if (historyBtn) historyBtn.style.display = 'none';
        if (customizeBtn) customizeBtn.style.display = 'none';
        if (helpBtn) helpBtn.style.display = 'none';
        if (upgradeBtn) upgradeBtn.style.display = 'none';
        if (modelSelector) modelSelector.style.display = 'none';
        
        // Simplify sidebar
        const sidebar = document.getElementById('sidebar');
        if (sidebar) sidebar.classList.add('ui-simple');
        
        // Hide gem actions in sidebar
        document.querySelectorAll('.gem-actions').forEach(el => {
            el.style.display = 'none';
        });
    } else {
        document.body.classList.remove('ui-simple');
        const thinkDeeperBtn = document.getElementById('thinkDeeperToggle');
        const historyBtn = document.getElementById('historyBtn');
        const customizeBtn = document.getElementById('customizeBtn');
        const helpBtn = document.getElementById('helpBtn');
        const upgradeBtn = document.getElementById('upgradeBtn');
        const modelSelector = document.getElementById('modelSelector');
        
        if (thinkDeeperBtn) thinkDeeperBtn.style.display = '';
        if (historyBtn) historyBtn.style.display = '';
        if (customizeBtn) customizeBtn.style.display = '';
        if (helpBtn) helpBtn.style.display = '';
        if (upgradeBtn) upgradeBtn.style.display = '';
        if (modelSelector) modelSelector.style.display = '';
        
        // Restore sidebar
        const sidebar = document.getElementById('sidebar');
        if (sidebar) sidebar.classList.remove('ui-simple');
        
        // Show gem actions
        document.querySelectorAll('.gem-actions').forEach(el => {
            el.style.display = '';
        });
    }
}

function getEffectiveTone() {
    // Try-preview gem tone
    if (currentModel === 'gem:preview' && activeGemDraft) {
        return (activeGemDraft.tone || currentTone || 'normal');
    }
    // Saved gem tone
    if (currentModel && currentModel.startsWith('gem:') && currentModel !== 'gem:preview') {
        const id = currentModel.replace(/^gem:/, '');
        const g = gems.find(x => x.id === id);
        if (g && g.tone) return g.tone;
    }
    return currentTone || 'normal';
}

function setTheme(theme) {
    themePreference = theme;
    const resolved = theme === 'system' ? resolveSystemTheme() : theme;
    currentTheme = resolved;
    document.body.setAttribute('data-theme', resolved);
    localStorage.setItem('atlasTheme', theme);
    updateThemeControls(theme);
}

function resolveSystemTheme() {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return 'dark';
    }
    return 'light';
}

function updateThemeControls(themeKey) {
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    if (themeToggleBtn) {
        themeToggleBtn.setAttribute('data-theme', themeKey);
    }
    document.querySelectorAll('input[name="theme"]').forEach(input => {
        input.checked = input.value === themeKey;
    });
}

// Close modals when clicking outside
document.addEventListener('click', (e) => {
    const settingsModal = document.getElementById('settingsModal');
    const upgradeModal = document.getElementById('upgradeModal');
    const helpModal = document.getElementById('helpModal');
    const customizeModal = document.getElementById('customizeModal');
    
    if (settingsModal && e.target === settingsModal) {
        closeSettingsModalFunc();
    }
    if (upgradeModal && e.target === upgradeModal) {
        closeUpgradeModalFunc();
    }
    if (helpModal && e.target === helpModal) {
        closeHelpModalFunc();
    }
    if (customizeModal && e.target === customizeModal) {
        closeCustomizeModalFunc();
    }
});

async function loadProjects() {
    try {
        const response = await fetch('/api/projects');
        const data = await response.json();
        displayProjects(data.projects || []);
    } catch (error) {
        console.error('Error loading projects:', error);
        const projectsContent = document.getElementById('projectsContent');
        if (projectsContent) {
            projectsContent.innerHTML = '<div class="chats-loading">Error loading projects</div>';
        }
    }
}

function displayProjects(projects) {
    const projectsContent = document.getElementById('projectsContent');
    if (!projectsContent) return;
    
    if (projects.length === 0) {
        projectsContent.innerHTML = '<div class="chats-loading">No projects yet. Create one to get started!</div>';
        return;
    }
    
    projectsContent.innerHTML = projects.map(project => {
        return `
            <div class="project-item" data-project-id="${project.project_id}">
                <div class="project-header">
                    <div class="project-icon">📁</div>
                    <div class="project-info">
                        <div class="project-name">${escapeHtml(project.name)}</div>
                        <div class="project-meta">
                            <span>${project.chat_count} chats</span>
                            <span>•</span>
                            <span>${new Date(project.updated_at).toLocaleDateString()}</span>
                        </div>
                    </div>
                </div>
                <div class="project-description">${escapeHtml(project.description || 'No description')}</div>
                <div class="project-actions">
                    <button class="project-edit-btn" onclick="event.stopPropagation(); editProject('${project.project_id}')" title="Edit">
                        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                            <path d="M8.5 2.5L11.5 5.5M10 1L13 4L9 8H6V5L10 1Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </button>
                    <button class="project-delete-btn" onclick="event.stopPropagation(); deleteProject('${project.project_id}')" title="Delete">
                        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                            <path d="M3.5 3.5L10.5 10.5M10.5 3.5L3.5 10.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                        </svg>
                    </button>
                </div>
            </div>
        `;
    }).join('');
    
    // Add click listeners
    projectsContent.querySelectorAll('.project-item').forEach(item => {
        item.addEventListener('click', (e) => {
            if (e.target.closest('.project-actions')) return;
            const projectId = item.dataset.projectId;
            loadProject(projectId);
        });
    });
}

async function loadProject(projectId) {
    try {
        const response = await fetch(`/api/projects/${projectId}`);
        const data = await response.json();
        
        // Show project details - can be enhanced with a project view
        console.log('Project loaded:', data);
        alert(`Project: ${data.name}\nDescription: ${data.description}\nChats: ${data.chat_ids.length}\n\nContext: ${data.context || 'No context'}`);
    } catch (error) {
        console.error('Error loading project:', error);
    }
}

function openProjectModal(projectId = null) {
    const modal = document.getElementById('projectModal');
    const form = document.getElementById('projectForm');
    const title = document.getElementById('projectModalTitle');
    
    if (modal) {
        modal.style.display = 'flex';
        
        if (projectId) {
            if (title) title.textContent = 'Edit Project';
            loadProjectForEdit(projectId);
        } else {
            if (title) title.textContent = 'New Project';
            if (form) form.reset();
            const projectIdInput = document.getElementById('projectId');
            if (projectIdInput) projectIdInput.value = '';
        }
    }
}

function closeProjectModalFunc() {
    const modal = document.getElementById('projectModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

async function loadProjectForEdit(projectId) {
    try {
        const response = await fetch(`/api/projects/${projectId}`);
        const data = await response.json();
        
        const projectIdInput = document.getElementById('projectId');
        const projectName = document.getElementById('projectName');
        const projectDescription = document.getElementById('projectDescription');
        const projectContext = document.getElementById('projectContext');
        
        if (projectIdInput) projectIdInput.value = data.project_id;
        if (projectName) projectName.value = data.name || '';
        if (projectDescription) projectDescription.value = data.description || '';
        if (projectContext) projectContext.value = data.context || '';
    } catch (error) {
        console.error('Error loading project for edit:', error);
    }
}

async function handleProjectSubmit(e) {
    e.preventDefault();
    
    const projectIdInput = document.getElementById('projectId');
    const projectName = document.getElementById('projectName');
    const projectDescription = document.getElementById('projectDescription');
    const projectContext = document.getElementById('projectContext');
    
    if (!projectIdInput || !projectName || !projectDescription || !projectContext) return;
    
    const projectId = projectIdInput.value;
    const name = projectName.value;
    const description = projectDescription.value;
    const context = projectContext.value;
    
    try {
        const projectData = {
            name: name,
            description: description,
            context: context,
            chat_ids: []
        };
        
        let response;
        if (projectId) {
            response = await fetch(`/api/projects/${projectId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(projectData)
            });
        } else {
            response = await fetch('/api/projects', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(projectData)
            });
        }
        
        if (response.ok) {
            const result = await response.json();
            closeProjectModalFunc();
            loadProjects();
            
            // Create history entry
            const historyData = {
                type: 'project',
                title: name,
                description: description,
                project_id: result.project_id || projectId,
                metadata: { action: projectId ? 'updated' : 'created' }
            };
            fetch('/api/history', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(historyData)
            });
        }
    } catch (error) {
        console.error('Error saving project:', error);
        alert('Error saving project. Please try again.');
    }
}

function editProject(projectId) {
    openProjectModal(projectId);
}

async function deleteProject(projectId) {
    if (!confirm('Delete this project? This will not delete the chats, only the project grouping.')) return;
    
    try {
        const response = await fetch(`/api/projects/${projectId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            loadProjects();
        }
    } catch (error) {
        console.error('Error deleting project:', error);
    }
}


// ==================== GEMS (Custom Sub-models) ====================

const GEM_TRY_TEMPLATES = [
    {
        id: 'study-buddy',
        name: 'Study Buddy',
        description: 'Explains concepts step-by-step, then quizzes you.',
        tone: 'friendly',
        instructions: 'Be a Study Buddy. Teach in small chunks, then ask 1 quick check question. If asked for depth, expand with examples. Avoid long bullets unless requested.',
        sources: { links: ['https://en.wikipedia.org/wiki/Spaced_repetition'], files: [] }
    },
    {
        id: 'product-manager',
        name: 'Product Manager',
        description: 'Turns ideas into crisp PRDs, risks, and roadmaps.',
        tone: 'formal',
        instructions: 'Act like a product manager. Ask 1–2 clarifying questions, then draft a PRD (goal, users, scope, non-goals), risks, metrics, and a simple roadmap. Prefer concise sections over big bullet dumps.',
        sources: { links: ['https://en.wikipedia.org/wiki/Product_management'], files: [] }
    },
    {
        id: 'design-critic',
        name: 'Design Critic',
        description: 'Gives direct UI/UX critique with actionable fixes.',
        tone: 'critical',
        instructions: 'Be a UI/UX critic. Be blunt but helpful. Provide: 1) top problems, 2) why it matters, 3) specific fixes. If the user wants more, add a short checklist.',
        sources: { links: ['https://en.wikipedia.org/wiki/User_experience_design'], files: [] }
    },
    {
        id: 'cowboy',
        name: 'Cowboy',
        description: 'Straight-shootin’ guidance with a calm frontier vibe.',
        tone: 'calm',
        instructions: 'Adopt a calm cowboy voice (no slang overload). Be concise, practical, and reassuring. Use short paragraphs. If the user asks for steps, give 3–6 steps.',
        sources: { links: ['https://en.wikipedia.org/wiki/Cowboy'], files: [] }
    }
];

async function loadGems() {
    try {
        const res = await fetch('/api/gems');
        const data = await res.json();
        gems = Array.isArray(data.gems) ? data.gems : [];

        // Preview gems are ephemeral and can't survive reload without the draft config.
        // If a stale preference points to gem:preview, fall back to the default model.
        if (currentModel === 'gem:preview' && !activeGemDraft) {
            currentModel = 'thor-1.0';
            localStorage.setItem('selectedModel', currentModel);
        }

        // Validate saved selection once we know which gems exist
        if (currentModel && currentModel.startsWith('gem:') && currentModel !== 'gem:preview') {
            const id = currentModel.replace(/^gem:/, '');
            const exists = gems.some(g => g.id === id);
            if (!exists) {
                currentModel = 'thor-1.0';
                localStorage.setItem('selectedModel', currentModel);
            }
        }

        // Reflect effective tone in UI accent on load (covers saved Gem selections).
        try {
            if (currentModel === 'gem:preview' && activeGemDraft?.tone) {
                document.body.setAttribute('data-tone', activeGemDraft.tone);
            } else if (currentModel && currentModel.startsWith('gem:') && currentModel !== 'gem:preview') {
                const id = currentModel.replace(/^gem:/, '');
                const g = gems.find(x => x.id === id);
                document.body.setAttribute('data-tone', (g?.tone || currentTone || 'normal'));
            } else {
                document.body.setAttribute('data-tone', currentTone || 'normal');
            }
        } catch (e) {
            document.body.setAttribute('data-tone', currentTone || 'normal');
        }

        rebuildModelDropdown();
        updateModelDisplay();
        renderGemsSidebar();
        renderGemsManageList();
    } catch (e) {
        console.error('Error loading gems:', e);
        gems = [];
        rebuildModelDropdown();
        updateModelDisplay();
        renderGemsSidebar();
        renderGemsManageList();
    }
}

function getModelDisplayName(modelId) {
    if (!modelId) return 'Thor 1.0';
    if (modelId === 'thor-1.0') return 'Thor 1.0';
    if (modelId === 'gem:preview' && activeGemDraft) return `Gem: ${toTitleCase(activeGemDraft.name || 'Gem')} (Try)`;
    if (modelId.startsWith('gem:')) {
        const id = modelId.replace(/^gem:/, '');
        const gem = gems.find(g => g.id === id);
        return gem ? `Gem: ${toTitleCase(gem.name || 'Gem')}` : 'Gem';
    }
    return modelId;
}

function updateModelDisplay() {
    const modelNameDisplay = document.querySelector('.model-name');
    if (!modelNameDisplay) return;
    modelNameDisplay.textContent = getModelDisplayName(currentModel);
}

function rebuildModelDropdown() {
    const dropdown = document.getElementById('modelDropdown');
    if (!dropdown) return;

    const items = [];

    // Only show Thor 1.0 in dropdown - Gems are accessible via sidebar
    items.push({ id: 'thor-1.0', name: 'Thor 1.0', note: 'Default model' });

    dropdown.innerHTML = items.map(it => {
        // Only mark as active if it's Thor 1.0 and no gem is selected
        // (Gems selected via sidebar won't show as active in dropdown, which is fine)
        const active = (it.id === currentModel && !currentModel.startsWith('gem:')) ? 'active' : '';
        const displayName = toTitleCase(it.name || '');
        return `
            <div class="model-option ${active}" data-model="${it.id}">
                <div class="model-option-info">
                    <span class="model-option-name">${escapeHtml(displayName)}</span>
                    <span class="model-option-note">${escapeHtml(it.note)}</span>
                </div>
                <span class="model-option-status">${active ? '✓' : ''}</span>
            </div>
        `;
    }).join('');

    dropdown.querySelectorAll('.model-option').forEach(opt => {
        opt.addEventListener('click', selectModel);
    });
}

function toTitleCase(str) {
    if (!str) return '';
    return str.replace(/\w\S*/g, (txt) => {
        return txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase();
    });
}

function renderGemsSidebar() {
    const el = document.getElementById('gemsSidebarList');
    if (!el) return;

    if (!gems.length) {
        el.innerHTML = '';
        return;
    }

    el.innerHTML = gems.map(g => {
        const isActive = currentModel === `gem:${g.id}`;
        const tone = (g.tone || 'normal').toLowerCase();
        const displayName = toTitleCase(g.name || 'Gem');
        return `
            <div class="gem-item-wrapper ${isActive ? 'active' : ''}" data-gem-id="${g.id}" data-tone="${tone}">
                <button class="gem-item" data-gem-id="${g.id}">
                    <span class="gem-item-content">
                        <span class="gem-item-title gem-tone-${tone}">${escapeHtml(displayName)}</span>
                    </span>
                </button>
                <span class="gem-actions">
                    <button class="gem-action-btn" data-action="edit" data-gem-id="${g.id}" title="Edit" aria-label="Edit Gem" type="button">
                        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                            <path d="M8.5 2.5L11.5 5.5M10 1L13 4L5 12H2V9L10 1Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                        </svg>
                    </button>
                    <button class="gem-action-btn danger" data-action="delete" data-gem-id="${g.id}" title="Delete" aria-label="Delete Gem" type="button">
                        <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                            <path d="M3.5 3.5L10.5 10.5M10.5 3.5L3.5 10.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                        </svg>
                    </button>
                </span>
            </div>
        `;
    }).join('');

    // Handle gem selection (clicking on the gem name)
    el.querySelectorAll('.gem-item').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const gemId = btn.getAttribute('data-gem-id');
            if (gemId) {
                selectGemModel(gemId);
            }
        });
    });

    // Handle edit button
    el.querySelectorAll('.gem-action-btn[data-action="edit"]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            e.preventDefault();
            const gemId = btn.getAttribute('data-gem-id');
            if (gemId) {
                openCustomizeModal();
                openGemEditor(gemId);
            }
        });
    });

    // Handle delete button
    el.querySelectorAll('.gem-action-btn[data-action="delete"]').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            e.preventDefault();
            const gemId = btn.getAttribute('data-gem-id');
            if (gemId) {
                deleteGem(gemId);
            }
        });
    });
}

function renderGemsManageList() {
    const el = document.getElementById('gemsManageList');
    if (!el) return;

    if (!gems.length) {
        el.innerHTML = '';
        return;
    }

    el.innerHTML = gems.map(g => {
        return `
            <div class="history-item" style="cursor:default;">
                <div class="history-item-title">${escapeHtml(g.name)}</div>
                <div class="history-item-description">${escapeHtml(g.description || 'Custom Gem')}</div>
                <div style="display:flex; gap:8px; margin-top:10px;">
                    <button class="btn-secondary" data-action="select" data-gem-id="${g.id}" type="button">Use</button>
                    <button class="btn-secondary" data-action="edit" data-gem-id="${g.id}" type="button">Edit</button>
                    <button class="btn-secondary" data-action="delete" data-gem-id="${g.id}" type="button">Delete</button>
                </div>
            </div>
        `;
    }).join('');

    el.querySelectorAll('button[data-gem-id]').forEach(b => {
        b.addEventListener('click', () => {
            const id = b.getAttribute('data-gem-id');
            const action = b.getAttribute('data-action');
            if (!id) return;
            if (action === 'select') selectGemModel(id);
            if (action === 'edit') openGemEditor(id);
            if (action === 'delete') deleteGem(id);
        });
    });
}

function renderGemTryTemplates() {
    const grid = document.getElementById('gemsTryGrid');
    if (!grid) return;
    grid.innerHTML = GEM_TRY_TEMPLATES.map(t => {
        const tone = (t.tone || 'normal').toLowerCase();
        const sources = (t.sources && Array.isArray(t.sources.links)) ? t.sources.links.length : 0;
        return `
            <button class="gem-try-card tone-${tone}" type="button" data-template-id="${t.id}">
                <div class="gem-try-name">${escapeHtml(toTitleCase(t.name))}</div>
                <div class="gem-try-desc">${escapeHtml(t.description)}</div>
                <div class="gem-try-meta">
                    <span class="gem-tone-badge tone-${tone}">${escapeHtml(toTitleCase(tone))}</span>
                    <span class="gem-sources-badge">${sources} source${sources === 1 ? '' : 's'}</span>
                </div>
            </button>
        `;
    }).join('');

    grid.querySelectorAll('.gem-try-card').forEach(btn => {
        btn.addEventListener('click', () => {
            const id = btn.getAttribute('data-template-id');
            const t = GEM_TRY_TEMPLATES.find(x => x.id === id);
            if (!t) return;
            setPreviewGem(t);
            closeCustomizeModalFunc();
        });
    });
}

function setPreviewGem(template) {
    activeGemDraft = {
        name: template.name,
        description: template.description,
        instructions: template.instructions,
        sources: template.sources || { links: [], files: [] },
        tone: template.tone || 'normal',
    };
    currentModel = 'gem:preview';
    localStorage.setItem('selectedModel', currentModel);
    rebuildModelDropdown();
    updateModelDisplay();
    renderGemsSidebar();
    if (activeGemDraft && activeGemDraft.tone) {
        document.body.setAttribute('data-tone', activeGemDraft.tone);
    }
}

function selectGemModel(gemId) {
    activeGemDraft = null;
    currentModel = `gem:${gemId}`;
    localStorage.setItem('selectedModel', currentModel);
    rebuildModelDropdown();
    updateModelDisplay();
    renderGemsSidebar();
    // Reflect the gem tone in the UI accent
    const g = gems.find(x => x.id === gemId);
    if (g && g.tone) {
        document.body.setAttribute('data-tone', g.tone);
    }
}

function openGemEditor(gemId = null) {
    const section = document.getElementById('gemEditorSection');
    const title = document.getElementById('gemEditorTitle');
    const idEl = document.getElementById('gemId');
    const nameEl = document.getElementById('gemName');
    const descEl = document.getElementById('gemDescription');
    const instrEl = document.getElementById('gemInstructions');
    const linksEl = document.getElementById('gemLinks');
    const filesEl = document.getElementById('gemFiles');
    const toneEl = document.querySelector('input[name="gemTone"]:checked');
    if (!section || !title || !idEl || !nameEl || !linksEl) return;

    section.classList.remove('hidden');
    if (filesEl) filesEl.value = '';

    if (!gemId) {
        title.textContent = 'New Gem';
        idEl.value = '';
        nameEl.value = '';
        if (descEl) descEl.value = '';
        if (instrEl) instrEl.value = '';
        linksEl.value = '';
        document.querySelectorAll('input[name="gemTone"]').forEach(r => {
            r.checked = (r.value === (currentTone || 'normal'));
        });
        return;
    }

    const g = gems.find(x => x.id === gemId);
    if (!g) return;
    title.textContent = `Edit Gem: ${g.name}`;
    idEl.value = g.id;
    nameEl.value = g.name || '';
    if (descEl) descEl.value = g.description || '';
    if (instrEl) instrEl.value = g.instructions || '';
    document.querySelectorAll('input[name="gemTone"]').forEach(r => {
        r.checked = (r.value === (g.tone || 'normal'));
    });
    const links = (g.sources && Array.isArray(g.sources.links)) ? g.sources.links : [];
    linksEl.value = links.join('\n');
}

function closeGemEditor() {
    const section = document.getElementById('gemEditorSection');
    if (section) section.classList.add('hidden');
    const form = document.getElementById('gemForm');
    if (form) form.reset();
    const idEl = document.getElementById('gemId');
    if (idEl) idEl.value = '';
}

function tryGemFromEditor() {
    const draft = collectGemDraftFromEditor();
    if (!draft) return;
    setPreviewGem({
        id: 'custom-editor',
        name: draft.name,
        description: draft.description,
        instructions: draft.instructions,
        sources: draft.sources
    });
    closeCustomizeModalFunc();
}

function collectGemDraftFromEditor() {
    const nameEl = document.getElementById('gemName');
    const descEl = document.getElementById('gemDescription');
    const instrEl = document.getElementById('gemInstructions');
    const linksEl = document.getElementById('gemLinks');
    const toneEl = document.querySelector('input[name="gemTone"]:checked');
    if (!nameEl) return null;
    const name = (nameEl.value || '').trim();
    if (!name) return null;
    const description = (descEl?.value || '').trim();
    const instructions = (instrEl?.value || '').trim();
    const links = (linksEl?.value || '')
        .split('\n')
        .map(l => l.trim())
        .filter(Boolean);
    const tone = (toneEl?.value || 'normal').trim();
    return {
        name,
        description,
        instructions,
        tone,
        sources: { links, files: [] }
    };
}

async function handleGemSubmit(e) {
    e.preventDefault();
    const idEl = document.getElementById('gemId');
    const filesEl = document.getElementById('gemFiles');
    const draft = collectGemDraftFromEditor();
    if (!draft) return;

    const files = filesEl ? Array.from(filesEl.files || []) : [];
    const filePayload = [];
    for (const f of files) {
        try {
            const text = await f.text();
            filePayload.push({
                filename: f.name,
                content: (text || '').slice(0, 50000)
            });
        } catch (err) {
            console.warn('Failed reading file', f?.name, err);
        }
    }
    draft.sources.files = filePayload;

    const gemId = (idEl?.value || '').trim();
    const method = gemId ? 'PUT' : 'POST';
    const url = gemId ? `/api/gems/${encodeURIComponent(gemId)}` : '/api/gems';

    try {
        const res = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(draft)
        });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.error || `HTTP ${res.status}`);
        }
        await loadGems();
        closeGemEditor();
    } catch (err) {
        console.error('Error saving gem:', err);
        alert(`Error saving gem: ${err.message}`);
    }
}

async function deleteGem(gemId) {
    if (!confirm('Delete this Gem?')) return;
    try {
        const res = await fetch(`/api/gems/${encodeURIComponent(gemId)}`, { method: 'DELETE' });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.error || `HTTP ${res.status}`);
        }
        if (currentModel === `gem:${gemId}`) {
            currentModel = 'thor-1.0';
            localStorage.setItem('selectedModel', currentModel);
        }
        await loadGems();
    } catch (err) {
        console.error('Error deleting gem:', err);
        alert(`Error deleting gem: ${err.message}`);
    }
}

// Plan dropdown removed in new design

// ==================== EASTER EGG ====================

function showEasterEgg() {
    // Create overlay for celebration
    const overlay = document.createElement('div');
    overlay.id = 'easterEggOverlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.8);
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-direction: column;
        animation: fadeIn 0.3s ease-in;
    `;
    
    // Create celebration container
    const container = document.createElement('div');
    container.style.cssText = `
        text-align: center;
        color: white;
        animation: scaleIn 0.5s ease-out;
    `;
    
    // Celebration GIF/Animation
    const gif = document.createElement('img');
    gif.src = 'https://media.giphy.com/media/3o7abldb0xflxXT2zC/giphy.gif'; // Celebration GIF
    gif.alt = 'Congratulations!';
    gif.style.cssText = `
        max-width: 400px;
        width: 100%;
        height: auto;
        border-radius: 10px;
        margin-bottom: 20px;
    `;
    
    // Fallback if GIF fails to load
    gif.onerror = function() {
        this.style.display = 'none';
        const fallback = document.createElement('div');
        fallback.innerHTML = '🎉🎊🎉🎊🎉';
        fallback.style.cssText = `
            font-size: 80px;
            margin-bottom: 20px;
            animation: bounce 1s infinite;
        `;
        container.insertBefore(fallback, container.firstChild);
    };
    
    // Congratulations message
    const message = document.createElement('h1');
    message.textContent = 'Congratulations! 🎉';
    message.style.cssText = `
        font-size: 48px;
        margin: 20px 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
        animation: pulse 1s infinite;
    `;
    
    const subMessage = document.createElement('p');
    subMessage.textContent = 'You found the secret!';
    subMessage.style.cssText = `
        font-size: 24px;
        margin: 10px 0;
        opacity: 0.9;
    `;
    
    // Close button
    const closeBtn = document.createElement('button');
    closeBtn.textContent = 'Close';
    closeBtn.style.cssText = `
        margin-top: 30px;
        padding: 12px 30px;
        font-size: 18px;
        background: #4CAF50;
        color: white;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        transition: background 0.3s;
    `;
    closeBtn.onmouseover = function() { this.style.background = '#45a049'; };
    closeBtn.onmouseout = function() { this.style.background = '#4CAF50'; };
    closeBtn.onclick = function() {
        overlay.remove();
        document.getElementById('easterEggStyles')?.remove();
    };
    
    // Add CSS animations
    if (!document.getElementById('easterEggStyles')) {
        const style = document.createElement('style');
        style.id = 'easterEggStyles';
        style.textContent = `
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            @keyframes scaleIn {
                from { transform: scale(0.5); opacity: 0; }
                to { transform: scale(1); opacity: 1; }
            }
            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.05); }
            }
            @keyframes bounce {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-20px); }
            }
        `;
        document.head.appendChild(style);
    }
    
    container.appendChild(gif);
    container.appendChild(message);
    container.appendChild(subMessage);
    container.appendChild(closeBtn);
    overlay.appendChild(container);
    document.body.appendChild(overlay);
    
    // Auto-close after 10 seconds
    setTimeout(() => {
        if (document.body.contains(overlay)) {
            overlay.remove();
            document.getElementById('easterEggStyles')?.remove();
        }
        }, 10000);
}

// ==================== POSEIDON VOICE ASSISTANT ====================

let poseidonActive = false;
let poseidonPaused = false;
let recognition = null;
let synthesis = null;
let currentVoice = null;
let voiceSettings = {
    accent: 'en-US',
    gender: 'male'
};
let poseidonOverlay = null;
let poseidonVisualizer = null;
let poseidonStatusIndicator = null;
let poseidonStatusText = null;
let poseidonUserTranscript = null;
let poseidonAssistantTranscript = null;
let silenceTimeout = null;
let lastSpeechTime = null;
let audioContext = null;
let analyser = null;
let microphone = null;
let audioLevelCheckInterval = null;
let recognitionRestartTimeout = null;
let pendingTranscript = '';
let transcriptProcessing = false;
let recognitionState = 'idle'; // 'idle', 'starting', 'listening', 'processing', 'stopped'
let speechDetected = false;
let consecutiveNoSpeechCount = 0;
const SILENCE_TIMEOUT_MS = 2500; // Process after 2.5 seconds of silence
const MIN_SPEECH_DURATION_MS = 300; // Minimum speech duration to process
const MAX_NO_SPEECH_COUNT = 3; // Max consecutive no-speech events before restart
const AUDIO_CHECK_INTERVAL_MS = 100; // Check audio levels every 100ms

// Initialize Poseidon
function initializePoseidon() {
    console.log('[Poseidon] Initializing...');
    
    // Backend check 1: Verify browser support
    const hasSpeechRecognition = 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
    const hasSpeechSynthesis = 'speechSynthesis' in window;
    const hasMediaDevices = 'mediaDevices' in navigator && 'getUserMedia' in navigator.mediaDevices;
    
    console.log('[Poseidon] Browser support check:', {
        speechRecognition: hasSpeechRecognition,
        speechSynthesis: hasSpeechSynthesis,
        mediaDevices: hasMediaDevices
    });
    
    if (!hasSpeechRecognition) {
        console.error('[Poseidon] Speech recognition not supported');
        const poseidonLaunchBtn = document.getElementById('poseidonLaunchBtn');
        if (poseidonLaunchBtn) {
            poseidonLaunchBtn.disabled = true;
            poseidonLaunchBtn.title = 'Voice assistant not supported in this browser';
        }
        return;
    }
    
    if (!hasSpeechSynthesis) {
        console.warn('[Poseidon] Speech synthesis not supported');
    }
    
    if (!hasMediaDevices) {
        console.error('[Poseidon] MediaDevices API not available');
        return;
    }
    
    // Backend check 2: Verify secure context
    const isSecure = window.isSecureContext || location.protocol === 'https:' || 
                     location.hostname === 'localhost' || location.hostname === '127.0.0.1';
    console.log('[Poseidon] Secure context:', isSecure, location.protocol, location.hostname);
    
    if (!isSecure) {
        console.warn('[Poseidon] Not in secure context - may have limited functionality');
    }
    
    // Backend check 3: Load and validate saved voice settings
    const savedAccent = localStorage.getItem('poseidonAccent') || 'en-US';
    const savedGender = localStorage.getItem('poseidonGender') || 'male';
    
    // Validate accent
    const validAccents = ['en-US', 'en-GB', 'en-AU', 'en-IN'];
    voiceSettings.accent = validAccents.includes(savedAccent) ? savedAccent : 'en-US';
    
    // Validate gender
    voiceSettings.gender = (savedGender === 'male' || savedGender === 'female') ? savedGender : 'male';
    
    console.log('[Poseidon] Voice settings:', voiceSettings);
    
    // Update UI
    const accentSelect = document.getElementById('voiceAccent');
    const genderSelect = document.getElementById('voiceGender');
    if (accentSelect) {
        accentSelect.value = voiceSettings.accent;
        accentSelect.addEventListener('change', (e) => {
            const newAccent = e.target.value;
            if (validAccents.includes(newAccent)) {
                voiceSettings.accent = newAccent;
                localStorage.setItem('poseidonAccent', newAccent);
                updateVoiceSelection();
                // Update recognition language if active
                if (recognition && poseidonActive) {
                    recognition.lang = newAccent;
                }
            }
        });
    }
    if (genderSelect) {
        genderSelect.value = voiceSettings.gender;
        genderSelect.addEventListener('change', (e) => {
            const newGender = e.target.value;
            if (newGender === 'male' || newGender === 'female') {
                voiceSettings.gender = newGender;
                localStorage.setItem('poseidonGender', newGender);
                updateVoiceSelection();
            }
        });
    }
    
    // Backend check 4: Verify DOM elements exist
    const requiredElements = {
        poseidonLaunchBtn: document.getElementById('poseidonLaunchBtn'),
        poseidonOverlay: document.getElementById('poseidonOverlay'),
        poseidonStatusText: document.getElementById('poseidonStatusText'),
        poseidonUserTranscript: document.getElementById('poseidonUserTranscript'),
        poseidonAssistantTranscript: document.getElementById('poseidonAssistantTranscript')
    };
    
    const missingElements = Object.entries(requiredElements)
        .filter(([name, el]) => !el)
        .map(([name]) => name);
    
    if (missingElements.length > 0) {
        console.warn('[Poseidon] Missing DOM elements:', missingElements);
    } else {
        console.log('[Poseidon] All required DOM elements found');
    }
    
    // Setup speech synthesis
    updateVoiceSelection();
    
    console.log('[Poseidon] Initialization complete');
    
    // Setup launch button
    const poseidonLaunchBtn = document.getElementById('poseidonLaunchBtn');
    if (poseidonLaunchBtn) {
        poseidonLaunchBtn.addEventListener('click', openPoseidonOverlay);
    }
    
    // Setup overlay elements
    poseidonOverlay = document.getElementById('poseidonOverlay');
    poseidonVisualizer = document.getElementById('poseidonVisualizer');
    poseidonStatusIndicator = document.getElementById('poseidonStatusIndicator');
    poseidonStatusText = document.getElementById('poseidonStatusText');
    poseidonUserTranscript = document.getElementById('poseidonUserTranscript');
    poseidonAssistantTranscript = document.getElementById('poseidonAssistantTranscript');
    
    // Setup overlay controls
    const poseidonCloseBtn = document.getElementById('poseidonCloseBtn');
    const poseidonHoldBtn = document.getElementById('poseidonHoldBtn');
    const poseidonEndBtn = document.getElementById('poseidonEndBtn');
    
    if (poseidonCloseBtn) {
        poseidonCloseBtn.addEventListener('click', closePoseidonOverlay);
    }
    if (poseidonHoldBtn) {
        poseidonHoldBtn.addEventListener('click', togglePoseidonPause);
    }
    if (poseidonEndBtn) {
        poseidonEndBtn.addEventListener('click', closePoseidonOverlay);
    }
}

function updateVoiceSelection() {
    if (!('speechSynthesis' in window)) {
        console.warn('Speech synthesis not supported');
        return;
    }
    
    // Wait for voices to load
    const loadVoices = () => {
        const voices = speechSynthesis.getVoices();
        if (voices.length === 0) {
            setTimeout(loadVoices, 100);
            return;
        }
        
        // Filter voices by accent and gender
        const accentMap = {
            'en-US': ['en-US', 'en_US'],
            'en-GB': ['en-GB', 'en_GB'],
            'en-AU': ['en-AU', 'en_AU'],
            'en-IN': ['en-IN', 'en_IN']
        };
        
        const targetLocales = accentMap[voiceSettings.accent] || ['en-US'];
        const targetGender = voiceSettings.gender === 'male' ? 'male' : 'female';
        
        // Find matching voice
        let selectedVoice = null;
        
        // First try exact locale match
        for (const voice of voices) {
            const voiceLocale = voice.lang.toLowerCase();
            if (targetLocales.some(locale => voiceLocale.startsWith(locale.toLowerCase()))) {
                // Check gender (some voices have gender info in name)
                const voiceName = voice.name.toLowerCase();
                const isMale = voiceName.includes('male') || voiceName.includes('david') || 
                              voiceName.includes('daniel') || voiceName.includes('james') ||
                              voiceName.includes('thomas') || voiceName.includes('mark');
                const isFemale = voiceName.includes('female') || voiceName.includes('samantha') ||
                                voiceName.includes('karen') || voiceName.includes('susan') ||
                                voiceName.includes('victoria') || voiceName.includes('zira');
                
                if (targetGender === 'male' && (isMale || (!isFemale && !isMale))) {
                    selectedVoice = voice;
                    break;
                } else if (targetGender === 'female' && isFemale) {
                    selectedVoice = voice;
                    break;
                }
            }
        }
        
        // Fallback: any voice with matching locale
        if (!selectedVoice) {
            for (const voice of voices) {
                const voiceLocale = voice.lang.toLowerCase();
                if (targetLocales.some(locale => voiceLocale.startsWith(locale.toLowerCase()))) {
                    selectedVoice = voice;
                    break;
                }
            }
        }
        
        // Final fallback: default voice
        if (!selectedVoice && voices.length > 0) {
            selectedVoice = voices[0];
        }
        
        currentVoice = selectedVoice;
        console.log('Poseidon: Selected voice:', selectedVoice ? selectedVoice.name : 'none');
    };
    
    loadVoices();
    speechSynthesis.onvoiceschanged = loadVoices;
}

function speakText(text) {
    if (!('speechSynthesis' in window) || !currentVoice) {
        console.warn('Speech synthesis not available');
        return;
    }
    
    // Stop any ongoing speech
    speechSynthesis.cancel();
    
    // Clean text for speech (remove markdown formatting)
    const cleanText = text
        .replace(/\*\*(.*?)\*\*/g, '$1') // Remove bold
        .replace(/\*(.*?)\*/g, '$1') // Remove italic
        .replace(/`(.*?)`/g, '$1') // Remove code
        .replace(/#{1,6}\s+/g, '') // Remove headers
        .replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1') // Remove links
        .replace(/\n{2,}/g, '. ') // Replace multiple newlines with period
        .replace(/\n/g, ' ') // Replace single newlines with space
        .trim();
    
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.voice = currentVoice;
    utterance.rate = 1.0;
    utterance.pitch = 1.0;
    utterance.volume = 1.0;
    
    utterance.onstart = () => {
        console.log('Poseidon: Speaking...');
        updatePoseidonStatus('speaking', 'Speaking...');
    };
    
    utterance.onend = () => {
        console.log('Poseidon: Finished speaking');
        if (poseidonActive && !poseidonPaused) {
            updatePoseidonStatus('ready', 'Ready');
            // Auto-restart listening
            setTimeout(() => {
                if (poseidonActive && !poseidonPaused && recognition) {
                    recognition.start();
                }
            }, 500);
        } else {
            updatePoseidonStatus('ready', 'Ready');
        }
    };
    
    utterance.onerror = (event) => {
        console.error('Poseidon: Speech error:', event.error);
        updatePoseidonStatus('ready', 'Ready');
        if (!poseidonPaused && poseidonActive) {
            // Try to continue listening
            setTimeout(() => {
                if (poseidonActive && !poseidonPaused && recognition) {
                    recognition.start();
                }
            }, 500);
        }
    };
    
    speechSynthesis.speak(utterance);
}

async function openPoseidonOverlay() {
    console.log('[Poseidon] Opening overlay...');
    
    // Check browser support
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
        alert('Voice assistant is not supported in this browser. Please use Chrome, Edge, or Safari.');
        return;
    }
    
    // Check secure context
    const isSecure = window.isSecureContext || location.protocol === 'https:' || 
                     location.hostname === 'localhost' || location.hostname === '127.0.0.1';
    if (!isSecure) {
        alert('Poseidon requires a secure connection (HTTPS) or localhost. Please access the site via HTTPS or localhost.');
        return;
    }
    
    // Request microphone permission and set up audio monitoring
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            } 
        });
        
        // Set up audio context for level monitoring
        try {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            analyser = audioContext.createAnalyser();
            microphone = audioContext.createMediaStreamSource(stream);
            analyser.fftSize = 256;
            analyser.smoothingTimeConstant = 0.8;
            microphone.connect(analyser);
            
            // Start audio level monitoring
            startAudioLevelMonitoring();
        } catch (audioErr) {
            console.error('[Poseidon] ERROR setting up audio context:', audioErr);
            console.error('[Poseidon] Audio context error details:', {
                name: audioErr?.name,
                message: audioErr?.message,
                stack: audioErr?.stack,
                hasAudioContext: !!window.AudioContext,
                hasWebkitAudioContext: !!window.webkitAudioContext,
                hasMediaDevices: !!navigator.mediaDevices,
                hasGetUserMedia: !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia)
            });
        }
        
        if (poseidonOverlay) {
            poseidonOverlay.style.display = 'flex';
            poseidonActive = true;
            poseidonPaused = false;
            recognitionState = 'starting';
            
            // Reset all state
            pendingTranscript = '';
            transcriptProcessing = false;
            speechDetected = false;
            consecutiveNoSpeechCount = 0;
            lastSpeechTime = Date.now();
            clearTimeout(silenceTimeout);
            clearTimeout(recognitionRestartTimeout);
            
            // Create or recreate recognition instance
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            
            // Always create a fresh instance for reliability
            if (recognition) {
                try {
                    console.log('[Poseidon] Stopping existing recognition instance');
                    recognition.stop();
                } catch (e) {
                    console.warn('[Poseidon] Error stopping existing recognition (non-critical):', e);
                }
            }
            
            try {
                recognition = new SpeechRecognition();
                console.log('[Poseidon] Created new SpeechRecognition instance');
            } catch (createErr) {
                console.error('[Poseidon] ERROR creating SpeechRecognition instance:', createErr);
                console.error('[Poseidon] Recognition creation error details:', {
                    name: createErr?.name,
                    message: createErr?.message,
                    hasSpeechRecognition: !!window.SpeechRecognition,
                    hasWebkitSpeechRecognition: !!window.webkitSpeechRecognition
                });
                throw createErr;
            }
            
            // Setup handlers BEFORE configuring
            try {
                setupRecognitionHandlers();
                console.log('[Poseidon] Recognition handlers setup complete');
            } catch (handlerErr) {
                console.error('[Poseidon] ERROR setting up recognition handlers:', handlerErr);
                console.error('[Poseidon] Handler setup error details:', {
                    name: handlerErr?.name,
                    message: handlerErr?.message,
                    stack: handlerErr?.stack
                });
                throw handlerErr;
            }
            
            // Configure recognition - use CONTINUOUS mode for better speech detection
            recognition.continuous = true;  // Continuous mode for better detection
            recognition.interimResults = true;  // Show interim results
            recognition.lang = voiceSettings.accent;
            recognition.maxAlternatives = 1;
            
            console.log('[Poseidon] Recognition configured:', {
                continuous: recognition.continuous,
                interimResults: recognition.interimResults,
                lang: recognition.lang,
                maxAlternatives: recognition.maxAlternatives
            });
            
            // Start recognition with retry logic
            startRecognitionWithRetry();
        }
    } catch (error) {
        console.error('[Poseidon] Microphone permission denied:', error);
        alert('Microphone permission is required to use Poseidon. Please enable it in your browser settings and try again.');
        updatePoseidonStatus('ready', 'Permission Required');
        recognitionState = 'idle';
    }
}

function startRecognitionWithRetry(maxRetries = 3) {
    if (!recognition || !poseidonActive) return;
    
    let retryCount = 0;
    
    const attemptStart = () => {
        if (!poseidonActive || poseidonPaused) {
            recognitionState = 'idle';
            return;
        }
        
        try {
            console.log(`[Poseidon] Starting recognition attempt ${retryCount + 1}...`);
            recognitionState = 'starting';
            recognition.start();
            console.log('[Poseidon] Recognition.start() called successfully');
            
            // Verify it started
            setTimeout(() => {
                if (recognitionState === 'starting' && poseidonActive) {
                    console.log('[Poseidon] Recognition appears to have started - state verified');
                    recognitionState = 'listening';
                } else {
                    console.warn('[Poseidon] Recognition state check - state:', recognitionState, 'active:', poseidonActive);
                    if (recognitionState !== 'listening' && poseidonActive) {
                        console.error('[Poseidon] WARNING: Recognition may not have started properly');
                    }
                }
            }, 500);
            
        } catch (err) {
            console.error(`[Poseidon] Error starting recognition (attempt ${retryCount + 1}):`, err);
            
            if (err.name === 'InvalidStateError') {
                // Recognition might already be running, try to stop and restart
                try {
                    recognition.stop();
                    console.log('[Poseidon] Stopped existing recognition, will retry...');
                } catch (stopErr) {
                    console.error('[Poseidon] ERROR stopping recognition:', stopErr);
                    console.error('[Poseidon] Stop error details:', {
                        name: stopErr?.name,
                        message: stopErr?.message,
                        recognitionState: recognitionState
                    });
                }
                
                if (retryCount < maxRetries) {
                    retryCount++;
                    const delay = 200 * retryCount;
                    console.log(`[Poseidon] Retrying in ${delay}ms (attempt ${retryCount + 1}/${maxRetries + 1})`);
                    setTimeout(attemptStart, delay); // Exponential backoff
                } else {
                    console.error('[Poseidon] ERROR: Max retries reached, giving up');
                    console.error('[Poseidon] Final retry error details:', {
                        maxRetries: maxRetries,
                        finalError: err,
                        errorName: err?.name,
                        errorMessage: err?.message,
                        recognitionState: recognitionState,
                        poseidonActive: poseidonActive,
                        poseidonPaused: poseidonPaused
                    });
                    updatePoseidonStatus('ready', 'Error starting');
                    recognitionState = 'idle';
                }
            } else {
                updatePoseidonStatus('ready', 'Error: ' + err.message);
                recognitionState = 'idle';
            }
        }
    };
    
    attemptStart();
}

function startAudioLevelMonitoring() {
    if (!analyser) {
        console.error('[Poseidon] ERROR: Cannot start audio monitoring - analyser is null');
        return;
    }
    
    if (audioLevelCheckInterval) {
        console.warn('[Poseidon] Audio level monitoring already running');
        return;
    }
    
    console.log('[Poseidon] Starting audio level monitoring');
    
    try {
        const dataArray = new Uint8Array(analyser.frequencyBinCount);
        
        audioLevelCheckInterval = setInterval(() => {
            if (!analyser || !poseidonActive || poseidonPaused) return;
            
            try {
                analyser.getByteFrequencyData(dataArray);
                const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
                const audioLevel = average / 255;
        
        // Update visualizer if available
        if (poseidonVisualizer) {
            const level = Math.min(audioLevel * 100, 100);
            poseidonVisualizer.style.setProperty('--audio-level', `${level}%`);
        }
        
        // Detect speech based on audio level
        if (audioLevel > 0.05) { // Threshold for speech detection
            if (!speechDetected) {
                speechDetected = true;
                lastSpeechTime = Date.now();
                consecutiveNoSpeechCount = 0;
                console.log('[Poseidon] Speech detected via audio level');
            }
            lastSpeechTime = Date.now();
        } else {
            if (speechDetected) {
                const silenceDuration = Date.now() - lastSpeechTime;
                if (silenceDuration > SILENCE_TIMEOUT_MS) {
                    speechDetected = false;
                    console.log('[Poseidon] Speech ended (silence detected)');
                    // Process pending transcript if any
                    if (pendingTranscript && pendingTranscript.trim().length > 0 && !transcriptProcessing) {
                        console.log('[Poseidon] Processing pending transcript after silence:', pendingTranscript);
                        handlePoseidonTranscript(pendingTranscript.trim());
                        pendingTranscript = '';
                    }
                }
            } catch (audioErr) {
                console.error('[Poseidon] ERROR in audio level monitoring:', audioErr);
                console.error('[Poseidon] Audio monitoring error details:', {
                    name: audioErr?.name,
                    message: audioErr?.message,
                    hasAnalyser: !!analyser,
                    poseidonActive: poseidonActive,
                    poseidonPaused: poseidonPaused
                });
            }
        }, AUDIO_CHECK_INTERVAL_MS);
        
        console.log('[Poseidon] Audio level monitoring started successfully');
    } catch (startErr) {
        console.error('[Poseidon] ERROR starting audio level monitoring:', startErr);
        console.error('[Poseidon] Start monitoring error details:', {
            name: startErr?.name,
            message: startErr?.message,
            hasAnalyser: !!analyser,
            hasAudioContext: !!audioContext
        });
    }
}

function stopAudioLevelMonitoring() {
    console.log('[Poseidon] Stopping audio level monitoring');
    
    if (audioLevelCheckInterval) {
        clearInterval(audioLevelCheckInterval);
        audioLevelCheckInterval = null;
        console.log('[Poseidon] Audio level check interval cleared');
    }
    
    if (microphone) {
        try {
            microphone.disconnect();
            console.log('[Poseidon] Microphone disconnected');
        } catch (e) {
            console.error('[Poseidon] ERROR disconnecting microphone:', e);
        }
        microphone = null;
    }
    
    if (analyser) {
        analyser = null;
        console.log('[Poseidon] Analyser cleared');
    }
    
    if (audioContext) {
        try {
            if (audioContext.state !== 'closed') {
                audioContext.close().then(() => {
                    console.log('[Poseidon] Audio context closed');
                }).catch((closeErr) => {
                    console.error('[Poseidon] ERROR closing audio context:', closeErr);
                });
            }
        } catch (e) {
            console.error('[Poseidon] ERROR handling audio context close:', e);
        }
        audioContext = null;
    }
}

// Helper function to process transcript (accessible from recognition handlers)
async function handlePoseidonTranscript(transcript) {
    if (!transcript || transcript.trim().length === 0) {
        console.log('[Poseidon] Empty transcript, skipping');
        return;
    }
    
    // Prevent duplicate processing
    if (transcriptProcessing) {
        console.log('[Poseidon] Already processing transcript, skipping:', transcript);
        return;
    }
    
    // Validate transcript length
    const trimmed = transcript.trim();
    if (trimmed.length < 2) {
        console.log('[Poseidon] Transcript too short, skipping:', trimmed);
        return;
    }
    
    console.log('[Poseidon] Processing transcript:', trimmed);
    transcriptProcessing = true;
    recognitionState = 'processing';
    
    // Update UI to show we're processing the transcript
    if (poseidonUserTranscript) {
        poseidonUserTranscript.textContent = trimmed;
    }
    
    // Don't stop recognition in continuous mode - just mark as processing
    clearTimeout(silenceTimeout);
    clearTimeout(recognitionRestartTimeout);
    updatePoseidonStatus('processing', 'Processing your request...');
    
    // Send to chat API
    try {
        const requestBody = {
            message: transcript,
            chat_id: currentChatId,
            task: 'text_generation',
            think_deeper: thinkDeeperMode,
            model: currentModel,
            tone: getEffectiveTone(),
        };
        
        if (currentModel === 'gem:preview' && activeGemDraft) {
            requestBody.gem_draft = activeGemDraft;
        }
        
        console.log('[Poseidon] Sending request to /api/chat:', {
            transcript: transcript,
            transcriptLength: transcript.length,
            chatId: currentChatId,
            model: currentModel,
            hasGemDraft: !!(currentModel === 'gem:preview' && activeGemDraft)
        });
        
        let response;
        try {
            response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });
            console.log('[Poseidon] Received response:', {
                ok: response.ok,
                status: response.status,
                statusText: response.statusText,
                headers: Object.fromEntries(response.headers.entries())
            });
        } catch (fetchErr) {
            console.error('[Poseidon] ERROR in fetch request:', fetchErr);
            console.error('[Poseidon] Fetch error details:', {
                name: fetchErr?.name,
                message: fetchErr?.message,
                stack: fetchErr?.stack,
                requestUrl: '/api/chat',
                requestMethod: 'POST'
            });
            throw new Error(`Network error: ${fetchErr.message}`);
        }
        
        if (!response.ok) {
            const errorText = await response.text().catch(() => 'Unable to read error response');
            console.error('[Poseidon] HTTP error response:', {
                status: response.status,
                statusText: response.statusText,
                errorText: errorText,
                url: response.url
            });
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        let data;
        try {
            data = await response.json();
            console.log('[Poseidon] Parsed response data:', {
                hasResponse: !!data.response,
                responseLength: data.response?.length || 0,
                chatId: data.chat_id,
                hasError: !!data.error
            });
        } catch (jsonErr) {
            console.error('[Poseidon] ERROR parsing JSON response:', jsonErr);
            console.error('[Poseidon] JSON parse error details:', {
                name: jsonErr?.name,
                message: jsonErr?.message,
                responseStatus: response.status,
                responseText: await response.text().catch(() => 'Unable to read response')
            });
            throw new Error(`Failed to parse response: ${jsonErr.message}`);
        }
        currentChatId = data.chat_id;
        
        // Add messages to UI
        try {
            addMessageToUI('user', transcript);
            console.log('[Poseidon] Added user message to UI');
        } catch (uiErr) {
            console.error('[Poseidon] ERROR adding user message to UI:', uiErr);
        }
        
        const responseText = data.response || 'No response received';
        console.log('[Poseidon] Response text:', {
            length: responseText.length,
            preview: responseText.substring(0, 100)
        });
        
        try {
            addMessageToUI('assistant', responseText);
            console.log('[Poseidon] Added assistant message to UI');
        } catch (uiErr) {
            console.error('[Poseidon] ERROR adding assistant message to UI:', uiErr);
        }
        
        // Update assistant transcript
        try {
            if (poseidonAssistantTranscript) {
                poseidonAssistantTranscript.textContent = responseText.substring(0, 200) + (responseText.length > 200 ? '...' : '');
                console.log('[Poseidon] Updated assistant transcript display');
            } else {
                console.warn('[Poseidon] poseidonAssistantTranscript element not found');
            }
        } catch (transcriptErr) {
            console.error('[Poseidon] ERROR updating assistant transcript:', transcriptErr);
        }
        
        // Speak the response
        try {
            speakText(responseText);
            console.log('[Poseidon] Started speaking response');
        } catch (speakErr) {
            console.error('[Poseidon] ERROR speaking response:', speakErr);
            console.error('[Poseidon] Speak error details:', {
                name: speakErr?.name,
                message: speakErr?.message,
                responseLength: responseText.length
            });
        }
        
    } catch (error) {
        console.error('[Poseidon] ERROR in handlePoseidonTranscript:', error);
        console.error('[Poseidon] Error details:', {
            name: error?.name,
            message: error?.message,
            stack: error?.stack,
            transcript: transcript,
            transcriptLength: transcript?.length,
            poseidonActive: poseidonActive,
            poseidonPaused: poseidonPaused,
            recognitionState: recognitionState,
            transcriptProcessing: transcriptProcessing
        });
        
        const errorMsg = 'Sorry, I encountered an error processing your request.';
        if (poseidonAssistantTranscript) {
            poseidonAssistantTranscript.textContent = errorMsg;
        }
        
        try {
            speakText(errorMsg);
        } catch (speakErr) {
            console.error('[Poseidon] ERROR speaking error message:', speakErr);
        }
        
        try {
            addMessageToUI('assistant', errorMsg);
        } catch (uiErr) {
            console.error('[Poseidon] ERROR adding error message to UI:', uiErr);
        }
        
        updatePoseidonStatus('ready', 'Error occurred');
    } finally {
        transcriptProcessing = false;
        
        // In continuous mode, recognition should still be running
        // Just reset state and continue listening
        if (poseidonActive && !poseidonPaused) {
            recognitionState = 'listening';
            updatePoseidonStatus('listening', 'Listening...');
            lastSpeechTime = Date.now();
            pendingTranscript = '';
            
            // Ensure recognition is still running
            if (recognition) {
                try {
                    // Check if recognition is still active
                    // In continuous mode, it should be
                    console.log('[Poseidon] Continuing to listen after processing');
                } catch (err) {
                    console.warn('[Poseidon] Recognition may have stopped, restarting...');
                    setTimeout(() => {
                        if (poseidonActive && !poseidonPaused) {
                            startRecognitionWithRetry();
                        }
                    }, 500);
                }
            }
        } else {
            recognitionState = 'idle';
        }
    }
}

// Setup recognition handlers (called when overlay opens)
function setupRecognitionHandlers() {
    if (!recognition) {
        console.error('[Poseidon] Cannot setup handlers - recognition is null');
        return;
    }
    
    console.log('[Poseidon] Setting up recognition handlers...');
    
    recognition.onstart = () => {
        console.log('[Poseidon] Recognition started - onstart fired');
        recognitionState = 'listening';
        updatePoseidonStatus('listening', 'Listening...');
        lastSpeechTime = Date.now();
        speechDetected = false;
        consecutiveNoSpeechCount = 0;
        clearTimeout(silenceTimeout);
        clearTimeout(recognitionRestartTimeout);
        
        // Clear previous transcript
        if (poseidonUserTranscript) {
            poseidonUserTranscript.textContent = '';
        }
        pendingTranscript = '';
        
        // Set up comprehensive silence detection
        resetSilenceTimeout();
    };
    
    recognition.onresult = (event) => {
        console.log('[Poseidon] onresult fired - resultIndex:', event.resultIndex, 'results.length:', event.results.length);
        
        // Update last speech time - user is speaking
        lastSpeechTime = Date.now();
        speechDetected = true;
        consecutiveNoSpeechCount = 0;
        clearTimeout(silenceTimeout);
        
        // Process all results
        let finalTranscript = '';
        let interimTranscript = '';
        let hasFinal = false;
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const result = event.results[i];
            const transcript = result[0].transcript;
            const isFinal = result.isFinal;
            const confidence = result[0].confidence || 0;
            
            console.log(`[Poseidon] Result ${i}: isFinal=${isFinal}, transcript="${transcript}", confidence=${confidence}`);
            
            if (isFinal) {
                finalTranscript += transcript + ' ';
                hasFinal = true;
            } else {
                interimTranscript += transcript;
            }
        }
        
        // Combine transcripts
        const combinedFinal = finalTranscript.trim();
        const combinedInterim = interimTranscript.trim();
        const displayText = combinedFinal || combinedInterim;
        
        console.log('[Poseidon] Processed results - final:', combinedFinal, 'interim:', combinedInterim);
        
        // Update UI with current transcript
        if (poseidonUserTranscript) {
            poseidonUserTranscript.textContent = displayText;
        }
        
        // Store pending transcript
        if (displayText && displayText.length > 0) {
            pendingTranscript = displayText;
        }
        
        // If we have a final transcript, process it immediately
        if (hasFinal && combinedFinal.length > 0) {
            console.log('[Poseidon] Final transcript received, processing:', combinedFinal);
            // Small delay to ensure all final results are captured
            setTimeout(() => {
                if (!transcriptProcessing && poseidonActive) {
                    handlePoseidonTranscript(combinedFinal);
                    pendingTranscript = '';
                }
            }, 100);
        } else if (combinedInterim.length > 0) {
            // We have interim results but no final yet
            // Set up timeout to process interim if no final comes
            resetSilenceTimeout();
        }
    };
    
    recognition.onspeechstart = () => {
        console.log('[Poseidon] Speech start detected');
        speechDetected = true;
        lastSpeechTime = Date.now();
        consecutiveNoSpeechCount = 0;
        clearTimeout(silenceTimeout);
    };
    
    recognition.onspeechend = () => {
        console.log('[Poseidon] Speech end detected');
        // Don't immediately process - wait a bit for final results
        setTimeout(() => {
            if (pendingTranscript && pendingTranscript.trim().length > 0 && !transcriptProcessing) {
                console.log('[Poseidon] Processing transcript after speech end:', pendingTranscript);
                handlePoseidonTranscript(pendingTranscript.trim());
                pendingTranscript = '';
            }
        }, 500);
    };
    
    recognition.onsoundstart = () => {
        console.log('[Poseidon] Sound detected');
        speechDetected = true;
        lastSpeechTime = Date.now();
    };
    
    recognition.onsoundend = () => {
        console.log('[Poseidon] Sound ended');
    };
    
    recognition.onaudiostart = () => {
        console.log('[Poseidon] Audio input started');
    };
    
    recognition.onaudioend = () => {
        console.log('[Poseidon] Audio input ended');
    };
    
    recognition.onnomatch = () => {
        console.log('[Poseidon] No speech match found');
        consecutiveNoSpeechCount++;
        
        // If we have pending transcript, process it
        if (pendingTranscript && pendingTranscript.trim().length > 0 && !transcriptProcessing) {
            console.log('[Poseidon] Processing pending transcript on nomatch:', pendingTranscript);
            handlePoseidonTranscript(pendingTranscript.trim());
            pendingTranscript = '';
        } else if (consecutiveNoSpeechCount >= MAX_NO_SPEECH_COUNT) {
            console.log('[Poseidon] Too many no-match events, restarting recognition');
            restartRecognition();
        }
    };
    
    function resetSilenceTimeout() {
        clearTimeout(silenceTimeout);
        silenceTimeout = setTimeout(() => {
            if (poseidonActive && !poseidonPaused && !transcriptProcessing) {
                const currentTranscript = poseidonUserTranscript?.textContent?.trim() || pendingTranscript.trim();
                if (currentTranscript && currentTranscript.length > 0) {
                    console.log('[Poseidon] Silence timeout - processing transcript:', currentTranscript);
                    handlePoseidonTranscript(currentTranscript);
                    pendingTranscript = '';
                } else {
                    console.log('[Poseidon] Silence timeout - no transcript to process');
                }
            }
        }, SILENCE_TIMEOUT_MS);
    }
    
    recognition.onend = () => {
        console.log('[Poseidon] Recognition ended - state was:', recognitionState);
        clearTimeout(silenceTimeout);
        recognitionState = 'stopped';
        
        if (!poseidonActive || poseidonPaused) {
            console.log('[Poseidon] Not restarting - inactive or paused');
            updatePoseidonStatus('ready', 'Ready');
            recognitionState = 'idle';
            return;
        }
        
        // Process any pending transcript before restarting
        if (pendingTranscript && pendingTranscript.trim().length > 0 && !transcriptProcessing) {
            console.log('[Poseidon] Processing pending transcript before restart:', pendingTranscript);
            handlePoseidonTranscript(pendingTranscript.trim());
            pendingTranscript = '';
        }
        
        // Auto-restart if still active (continuous mode should keep running)
        if (poseidonActive && !poseidonPaused) {
            clearTimeout(recognitionRestartTimeout);
            recognitionRestartTimeout = setTimeout(() => {
                if (poseidonActive && !poseidonPaused && recognition) {
                    console.log('[Poseidon] Auto-restarting recognition...');
                    startRecognitionWithRetry();
                }
            }, 500); // Wait before restarting
        }
    };
    
    function restartRecognition() {
        if (!poseidonActive || poseidonPaused || transcriptProcessing) {
            console.warn('[Poseidon] Cannot restart recognition - conditions not met:', {
                poseidonActive: poseidonActive,
                poseidonPaused: poseidonPaused,
                transcriptProcessing: transcriptProcessing
            });
            return;
        }
        
        console.log('[Poseidon] Restarting recognition...');
        try {
            if (recognition) {
                recognition.stop();
                console.log('[Poseidon] Recognition stopped for restart');
            } else {
                console.error('[Poseidon] ERROR: Cannot restart - recognition is null');
            }
        } catch (e) {
            console.error('[Poseidon] ERROR stopping recognition for restart:', e);
        }
        
        clearTimeout(recognitionRestartTimeout);
        recognitionRestartTimeout = setTimeout(() => {
            if (poseidonActive && !poseidonPaused) {
                console.log('[Poseidon] Executing delayed restart');
                startRecognitionWithRetry();
            } else {
                console.warn('[Poseidon] Restart cancelled - conditions changed:', {
                    poseidonActive: poseidonActive,
                    poseidonPaused: poseidonPaused
                });
            }
        }, 300);
    }
    
    recognition.onerror = (event) => {
        console.error('[Poseidon] ERROR: Recognition error event fired');
        console.error('[Poseidon] Error event details:', {
            error: event.error,
            message: event.message,
            type: event.type,
            timeStamp: event.timeStamp,
            recognitionState: recognitionState,
            poseidonActive: poseidonActive,
            poseidonPaused: poseidonPaused,
            transcriptProcessing: transcriptProcessing,
            hasRecognition: !!recognition
        });
        console.error('[Poseidon] Full error event object:', event);
        
        let errorMsg = '';
        let shouldSpeak = true;
        let shouldRestart = false;
        
        if (event.error === 'no-speech') {
            console.log('[Poseidon] No speech detected (normal - will restart silently)');
            shouldSpeak = false;
            shouldRestart = true;
        } else if (event.error === 'not-allowed') {
            console.error('[Poseidon] ERROR: Microphone permission denied');
            errorMsg = 'Microphone permission denied. Please enable microphone access.';
            alert('Please enable microphone access in your browser settings to use Poseidon.');
            updatePoseidonStatus('ready', 'Permission Required');
        } else if (event.error === 'network') {
            console.error('[Poseidon] ERROR: Network error in recognition');
            errorMsg = 'Network error. Please check your connection.';
            shouldRestart = true;
        } else if (event.error === 'aborted') {
            // Recognition was stopped, don't show error
            console.log('[Poseidon] Recognition aborted (normal operation)');
            return;
        } else if (event.error === 'audio-capture') {
            console.error('[Poseidon] ERROR: No microphone found');
            errorMsg = 'No microphone found. Please connect a microphone.';
        } else if (event.error === 'service-not-allowed') {
            console.error('[Poseidon] ERROR: Service not allowed');
            // Service not available - check if we're on secure context
            const isSecure = window.isSecureContext || location.protocol === 'https:' || location.hostname === 'localhost' || location.hostname === '127.0.0.1';
            if (!isSecure) {
                errorMsg = 'Speech recognition requires HTTPS or localhost. Please use a secure connection.';
                updatePoseidonStatus('ready', 'HTTPS Required');
            } else {
                // Service might be temporarily unavailable - try to recreate
                console.warn('Poseidon: Service not allowed, attempting to recreate recognition');
                try {
                    // Stop current recognition
                    if (recognition) {
                        recognition.stop();
                    }
                    // Create new instance
                    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                    recognition = new SpeechRecognition();
                    setupRecognitionHandlers();
                    // Wait a bit before restarting
                    setTimeout(() => {
                        if (poseidonActive && !poseidonPaused) {
                            try {
                                recognition.start();
                                console.log('Poseidon: Restarted recognition after service-not-allowed');
                                return; // Successfully restarted
                            } catch (startErr) {
                                console.error('Poseidon: Failed to start after recreation:', startErr);
                                errorMsg = 'Speech recognition service is unavailable. Please refresh the page or try again later.';
                                updatePoseidonStatus('ready', 'Service Unavailable');
                                if (poseidonAssistantTranscript) {
                                    poseidonAssistantTranscript.textContent = errorMsg;
                                }
                            }
                        }
                    }, 1000);
                    return; // Don't show error immediately, wait for retry
                } catch (err) {
                    console.error('[Poseidon] ERROR: Failed to recreate recognition:', err);
                    console.error('[Poseidon] Recreation error details:', {
                        name: err?.name,
                        message: err?.message,
                        stack: err?.stack,
                        hasSpeechRecognition: !!window.SpeechRecognition,
                        hasWebkitSpeechRecognition: !!window.webkitSpeechRecognition
                    });
                    errorMsg = 'Speech recognition service is not available. Please refresh the page or use a different browser.';
                    updatePoseidonStatus('ready', 'Service Unavailable');
                }
            }
        } else {
            console.error('[Poseidon] ERROR: Unknown recognition error:', event.error);
            errorMsg = `Recognition error: ${event.error}. Please try again.`;
            shouldRestart = true;
        }
        
        if (errorMsg && shouldSpeak) {
            console.log('[Poseidon] Displaying error message to user:', errorMsg);
            updatePoseidonStatus('ready', 'Ready');
            try {
                if (poseidonAssistantTranscript) {
                    poseidonAssistantTranscript.textContent = errorMsg;
                } else {
                    console.warn('[Poseidon] poseidonAssistantTranscript element not found for error display');
                }
            } catch (uiErr) {
                console.error('[Poseidon] ERROR updating error message in UI:', uiErr);
            }
            
            try {
                speakText(errorMsg);
            } catch (speakErr) {
                console.error('[Poseidon] ERROR speaking error message:', speakErr);
            }
        }
        
        if (shouldRestart && poseidonActive && !poseidonPaused) {
            console.log('[Poseidon] Scheduling recognition restart after error');
            setTimeout(() => {
                if (poseidonActive && !poseidonPaused && recognition) {
                    try {
                        console.log('[Poseidon] Attempting to restart recognition after error');
                        recognition.start();
                    } catch (err) {
                        console.error('[Poseidon] ERROR restarting recognition after error:', err);
                        console.error('[Poseidon] Restart error details:', {
                            name: err?.name,
                            message: err?.message,
                            recognitionState: recognitionState
                        });
                    }
                } else {
                    console.warn('[Poseidon] Cannot restart - conditions not met:', {
                        poseidonActive: poseidonActive,
                        poseidonPaused: poseidonPaused,
                        hasRecognition: !!recognition
                    });
                }
            }, 1000);
        }
    };
}

function closePoseidonOverlay() {
    console.log('[Poseidon] Closing overlay...');
    
    if (poseidonOverlay) {
        poseidonOverlay.style.display = 'none';
    }
    
    // Stop everything
    poseidonActive = false;
    poseidonPaused = false;
    transcriptProcessing = false;
    recognitionState = 'idle';
    
    clearTimeout(silenceTimeout);
    clearTimeout(recognitionRestartTimeout);
    
    // Stop audio monitoring
    stopAudioLevelMonitoring();
    
    // Stop recognition
    if (recognition) {
        try {
            recognition.stop();
        } catch (e) {
            // Ignore errors
        }
    }
    
    // Stop speech synthesis
    if (speechSynthesis) {
        speechSynthesis.cancel();
    }
    
    // Reset state
    lastSpeechTime = null;
    pendingTranscript = '';
    speechDetected = false;
    consecutiveNoSpeechCount = 0;
    
    updatePoseidonStatus('ready', 'Ready');
    
    // Clear transcripts
    if (poseidonUserTranscript) {
        poseidonUserTranscript.textContent = '';
    }
    if (poseidonAssistantTranscript) {
        poseidonAssistantTranscript.textContent = '';
    }
    
    console.log('[Poseidon] Overlay closed');
}

function togglePoseidonPause() {
    poseidonPaused = !poseidonPaused;
    
    if (poseidonPaused) {
        // Pause
        if (recognition) {
            recognition.stop();
        }
        if (speechSynthesis) {
            speechSynthesis.pause();
        }
        updatePoseidonStatus('paused', 'Paused');
    } else {
        // Resume
        console.log('[Poseidon] Resuming...');
        
        if (speechSynthesis && speechSynthesis.paused) {
            speechSynthesis.resume();
        }
        
        if (poseidonActive && recognition) {
            // Restart recognition
            startRecognitionWithRetry();
        }
        
        updatePoseidonStatus('listening', 'Listening...');
    }
}

function updatePoseidonStatus(status, text) {
    if (poseidonStatusIndicator) {
        poseidonStatusIndicator.className = 'poseidon-status-indicator';
        if (status === 'listening') {
            poseidonStatusIndicator.classList.add('listening');
        } else if (status === 'speaking') {
            poseidonStatusIndicator.classList.add('speaking');
        }
    }
    
    if (poseidonStatusText) {
        poseidonStatusText.textContent = text;
    }
    
    if (poseidonVisualizer) {
        poseidonVisualizer.className = 'poseidon-visualizer';
        if (status === 'listening') {
            poseidonVisualizer.classList.add('listening');
        } else if (status === 'speaking') {
            poseidonVisualizer.classList.add('speaking');
        }
    }
}
