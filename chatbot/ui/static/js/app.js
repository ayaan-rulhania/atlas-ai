// Atlas AI - Thor 1.1 Frontend
let currentChatId = null;
let isLoading = false;
let thinkDeeperMode = false;
let allChats = [];
let currentTheme = 'light';
let themePreference = 'system';
let currentModel = 'thor-1.1';
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
    // In stable mode, use Thor 1.0; otherwise use Thor 1.1
    const defaultModel = (systemMode === 'stable') ? 'thor-1.0' : 'thor-1.1';
    const savedModel = localStorage.getItem('selectedModel') || defaultModel;
    // If a gem is saved, keep it (for sidebar access) but default dropdown to Thor 1.1 (or 1.0 in stable)
    // Gems can still be selected via sidebar, just not shown in dropdown
    if (savedModel && savedModel.startsWith('gem:')) {
        currentModel = savedModel; // Keep gem selection for sidebar
    } else if (savedModel && (savedModel === 'thor-1.0' || savedModel === 'thor-1.1')) {
        // Respect saved model if it's a valid Thor model
        currentModel = savedModel;
    } else {
        // Use default based on system mode
        currentModel = defaultModel;
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
    const installBtn = document.getElementById('installBtn');
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
    if (installBtn) installBtn.addEventListener('click', () => {
        // Check if running in Electron app (macOS app)
        const isElectron = window.electronAPI !== undefined;
        if (isElectron) {
            window.location.href = '/update';
        } else {
            window.location.href = '/install';
        }
    });
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
        
        // Check Thor 1.1 model status (latest)
        const thor11Model = data.models?.['thor-1.1'];
        if (thor11Model) {
            if (!thor11Model.loaded) {
                console.warn('[Model Status] ⚠️ Thor 1.1 model is not loaded');
                
                // Show diagnostic information if available
                if (thor11Model.diagnostics) {
                    console.warn('[Model Status] Diagnostics:', thor11Model.diagnostics);
                    if (thor11Model.diagnostics.message) {
                        console.warn('[Model Status] Reason:', thor11Model.diagnostics.message);
                    }
                }
            } else {
                console.log('[Model Status] ✅ Thor 1.1 model is loaded and ready');
                if (thor11Model.available_tasks && thor11Model.available_tasks.length > 0) {
                    console.log('[Model Status] Available tasks:', thor11Model.available_tasks);
                }
            }
        }
        
        // Check Thor 1.0 model status (stable)
        const thor10Model = data.models?.['thor-1.0'];
        if (thor10Model) {
            if (!thor10Model.loaded) {
                console.warn('[Model Status] ⚠️ Thor 1.0 (stable) model is not loaded');
            } else {
                console.log('[Model Status] ✅ Thor 1.0 (stable) model is loaded and ready');
            }
        }
        
        if (data.fallback_available) {
            console.info('[Model Status] ✅ Chat will still work using research engine and knowledge base');
            console.info('[Model Status] This is normal in serverless deployments or lightweight setups');
        }
        
        // Show overall message if available
        if (data.message) {
            console.info('[Model Status]', data.message);
        }
    } catch (error) {
        console.error('[Model Status] Error checking model status:', error);
        console.warn('[Model Status] Continuing without model status check - app will still function');
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
    
    // Check for easter egg: "I am in C5." (case-insensitive, flexible punctuation)
    const easterEggPattern = /^i\s+am\s+in\s+c5\.?$/i;
    if (easterEggPattern.test(message)) {
        showEasterEgg();
        messageInput.value = '';
        return;
    }
    
    // Check for command shortcuts
    const messageLower = message.toLowerCase().trim();
    
    // Handle /emoji command
    if (messageLower.startsWith('/emoji ')) {
        const emojiRequest = message.substring(7).trim();
        if (emojiRequest) {
            messageInput.value = `Give me a ${emojiRequest} emoji`;
            autoResizeTextarea(messageInput);
            // Continue to send the message (don't return)
        }
    }
    // Handle /office command
    else if (messageLower === '/office' || messageLower.startsWith('/office ')) {
        messageInput.value = 'Load Office Suite';
        autoResizeTextarea(messageInput);
        // Continue to send the message (don't return)
    }
    // Handle /arcade command
    else if (messageLower === '/arcade' || messageLower.startsWith('/arcade ')) {
        messageInput.value = 'Load Game Suite';
        autoResizeTextarea(messageInput);
        // Continue to send the message (don't return)
    }
    // Handle /image command
    else if (messageLower.startsWith('/image ')) {
        const imageDesc = message.substring(7).trim();
        if (imageDesc) {
            messageInput.value = `Create an image of ${imageDesc}`;
            autoResizeTextarea(messageInput);
            // Continue to send the message (don't return)
        } else {
            return; // Invalid /image command
        }
    }
    
    // Get the final message value (may have been changed by commands above)
    const finalMessage = messageInput.value.trim();
    if (!finalMessage) return;
    
    // Use final message for sending (may have been transformed by commands)
    const messageToSend = finalMessage;
    
    isLoading = true;
    updateSendButton(true);
    
    // Hide welcome screen if showing
    const welcomeScreen = document.getElementById('welcomeScreen');
    const messagesContainer = document.getElementById('messagesContainer');
    
    if (welcomeScreen.style.display !== 'none') {
        welcomeScreen.style.display = 'none';
        messagesContainer.style.display = 'block';
    }
    
    // Add user message to UI (show the transformed command)
    addMessageToUI('user', messageToSend);
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
            message: messageToSend,
            chat_id: currentChatId,
            task: 'text_generation',
            think_deeper: thinkDeeperMode,
            model: currentModel,  // Include selected model
            tone: getEffectiveTone(),
            system_mode: systemMode,  // Include system mode (latest/stable)
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
        
        let response;
        try {
            // Create timeout controller for network error handling
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 minute timeout
            
            response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody),
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
        } catch (fetchError) {
            // Handle network errors (connection failures, timeouts, etc.)
            console.error('Network error during fetch:', fetchError);
            if (fetchError.name === 'AbortError' || fetchError.name === 'TimeoutError') {
                throw new Error('Request timed out. The server may be taking too long to respond. Please try again.');
            } else if (fetchError.name === 'TypeError' && fetchError.message.includes('Failed to fetch')) {
                throw new Error('Network error: Could not connect to the server. Please check your connection and ensure the server is running.');
            } else {
                throw new Error(`Network error: ${fetchError.message || 'Unknown error occurred'}`);
            }
        }
        
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
        // Switch to Thor 1.0 in stable mode
        if (currentModel === 'thor-1.1' || !currentModel.startsWith('gem:')) {
            currentModel = 'thor-1.0';
            localStorage.setItem('selectedModel', 'thor-1.0');
            updateModelDisplay();
            rebuildModelDropdown();
        }
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
        // Switch to Thor 1.1 in latest mode (unless gem is selected)
        if (currentModel === 'thor-1.0' || (!currentModel.startsWith('gem:') && currentModel !== 'thor-1.1')) {
            currentModel = 'thor-1.1';
            localStorage.setItem('selectedModel', 'thor-1.1');
            updateModelDisplay();
            rebuildModelDropdown();
        }
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
    // First, try to load from localStorage for instant display
    try {
        const cachedGems = localStorage.getItem('atlasGems');
        if (cachedGems) {
            const parsed = JSON.parse(cachedGems);
            if (Array.isArray(parsed)) {
                gems = parsed;
                // Update UI immediately with cached data
                rebuildModelDropdown();
                updateModelDisplay();
                renderGemsSidebar();
                renderGemsManageList();
            }
        }
    } catch (e) {
        console.warn('Error loading cached gems from localStorage:', e);
    }

    // Then fetch fresh data from API and update
    try {
        const res = await fetch('/api/gems');
        const data = await res.json();
        gems = Array.isArray(data.gems) ? data.gems : [];
        
        // Save to localStorage for next time
        try {
            localStorage.setItem('atlasGems', JSON.stringify(gems));
        } catch (e) {
            console.warn('Error saving gems to localStorage:', e);
        }

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
        console.error('Error loading gems from API:', e);
        // If API fails but we have cached gems, keep using them
        if (!gems || gems.length === 0) {
            gems = [];
            rebuildModelDropdown();
            updateModelDisplay();
            renderGemsSidebar();
            renderGemsManageList();
        }
    }
}

function getModelDisplayName(modelId) {
    if (!modelId) return 'Thor 1.1';
    if (modelId === 'thor-1.0') return 'Thor 1.0';
    if (modelId === 'thor-1.1') return 'Thor 1.1';
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

    // Show both Thor 1.1 (latest) and Thor 1.0 (stable) - Gems are accessible via sidebar
    if (systemMode === 'stable') {
        items.push({ id: 'thor-1.0', name: 'Thor 1.0', note: 'Stable mode' });
    } else {
        items.push({ id: 'thor-1.1', name: 'Thor 1.1', note: 'Latest model' });
        items.push({ id: 'thor-1.0', name: 'Thor 1.0', note: 'Stable version' });
    }

    dropdown.innerHTML = items.map(it => {
        // Mark as active if it matches current model and no gem is selected
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
        await loadGems(); // This will save to localStorage
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
        await loadGems(); // This will save updated gems to localStorage
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
let poseidon3D = null; // 3D animation instance
let poseidon3DEnabled = false; // 3D UI enabled setting (loaded from localStorage)
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
let serviceNotAllowedRetryCount = 0; // Track retries for service-not-allowed errors
let lastServiceNotAllowedTime = 0; // Track when last service-not-allowed occurred
let rapidErrorTimes = []; // Track recent error times for circuit breaker
let serviceNotAllowedDisabled = false; // Circuit breaker flag - stop retrying if too many rapid errors
let lastHighVolumeTime = 0; // Track when we last detected high volume
let currentAudioLevel = 0; // Current audio level (0-1)
let audioLevelHistory = []; // History of audio levels for trend analysis and adaptive sensitivity (v3.0.0)
const SILENCE_TIMEOUT_MS = 1500; // Process after 1.5 seconds of silence (reduced for faster response)
const MIN_SPEECH_DURATION_MS = 300; // Minimum speech duration to process
const MAX_NO_SPEECH_COUNT = 3; // Max consecutive no-speech events before restart
const MAX_SERVICE_NOT_ALLOWED_RETRIES = 2; // Max retries for service-not-allowed
const SERVICE_NOT_ALLOWED_COOLDOWN_MS = 10000; // Cooldown period between retries (10 seconds - increased to prevent loops)
const MAX_RAPID_ERRORS = 5; // Stop if we get this many errors in quick succession (circuit breaker)
const RAPID_ERROR_WINDOW_MS = 3000; // Time window for rapid error detection (3 seconds)
const AUDIO_CHECK_INTERVAL_MS = 100; // Check audio levels every 100ms
const AUDIO_LEVEL_THRESHOLD = 0.05; // Minimum audio level to consider as speech
const VOLUME_DECLINE_THRESHOLD = 0.02; // Volume must drop below this to trigger processing
const MIN_VOLUME_DECLINE_DURATION = 800; // How long volume must be low before processing (ms)
let isSpeaking = false; // Track if Poseidon is currently speaking
let lastSpokenText = ''; // Track the last text that Poseidon spoke (cleaned version)
let lastSpokenTime = 0; // Track when Poseidon last finished speaking
let lastAssistantResponse = ''; // Track last assistant response for repeat command
let voiceCommandHandlers = {}; // Voice command handlers
let audioQualityIndicator = null; // Audio quality indicator element

// Version 3.0.0: New features
let currentSpeechSpeed = 1.0; // Speech synthesis speed (0.5 - 2.0)
let currentSpeechVolume = 1.0; // Speech synthesis volume (0.0 - 1.0)
let currentLanguage = 'en-US'; // Current language setting
let interruptionEnabled = true; // Allow user to interrupt
let adaptiveSensitivity = 0.01; // Adaptive audio threshold
let conversationSummaries = []; // Store conversation summaries
let emotionHistory = []; // Track emotion history for adaptation
let canInterrupt = false; // Flag to enable interruption
const SPEECH_MATCH_WINDOW_MS = 20000; // Time window to check for matching speech (20 seconds - increased for Electron app echo issues)

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
    
    // Backend check 3: Load and validate saved voice settings (v3.0.0: Enhanced)
    const savedAccent = localStorage.getItem('poseidonAccent') || 'en-US';
    const savedGender = localStorage.getItem('poseidonGender') || 'male';
    const savedSpeed = localStorage.getItem('poseidonSpeechSpeed');
    const savedVolume = localStorage.getItem('poseidonSpeechVolume');
    
    // Version 3.0.0: Load saved settings
    if (savedSpeed) {
        currentSpeechSpeed = parseFloat(savedSpeed) || 1.0;
    }
    if (savedVolume) {
        currentSpeechVolume = parseFloat(savedVolume) || 1.0;
    }
    if (savedAccent) {
        currentLanguage = savedAccent;
    }
    
    // Validate accent (v3.x: Enhanced with new languages)
    const validAccents = ['en-US', 'en-GB', 'en-AU', 'en-IN', 'hi-IN', 'ta-IN', 'te-IN', 'es-ES', 'es-MX', 'fr-FR', 'zh-CN', 'de-DE', 'it-IT', 'pt-BR', 'ja-JP', 'ko-KR'];
    voiceSettings.accent = validAccents.includes(savedAccent) ? savedAccent : 'en-US';
    
    // Ensure currentLanguage is synced with voiceSettings.accent
    if (!currentLanguage || currentLanguage !== voiceSettings.accent) {
        currentLanguage = voiceSettings.accent;
    }
    
    // Validate gender
    voiceSettings.gender = (savedGender === 'male' || savedGender === 'female') ? savedGender : 'male';
    
    console.log('[Poseidon] Voice settings:', voiceSettings);
    
    // Update UI
    const accentSelect = document.getElementById('voiceAccent');
    const genderSelect = document.getElementById('voiceGender');
    const poseidon3DCheckbox = document.getElementById('poseidon3DEnabled');
    
    // Initialize 3D Poseidon setting (default: false) - use global variable
    poseidon3DEnabled = localStorage.getItem('poseidon3DEnabled') === 'true';
    if (poseidon3DCheckbox) {
        poseidon3DCheckbox.checked = poseidon3DEnabled;
        poseidon3DCheckbox.addEventListener('change', (e) => {
            poseidon3DEnabled = e.target.checked;
            localStorage.setItem('poseidon3DEnabled', poseidon3DEnabled);
            console.log('[Poseidon] 3D UI setting changed:', poseidon3DEnabled);
            // If disabling, clean up 3D instance if overlay is open
            if (!poseidon3DEnabled && poseidon3D) {
                try {
                    poseidon3D.dispose();
                    poseidon3D = null;
                } catch (error) {
                    console.error('[Poseidon] Error disposing 3D animation:', error);
                }
            }
        });
    }
    
    if (accentSelect) {
        accentSelect.value = voiceSettings.accent;
        accentSelect.addEventListener('change', async (e) => {
            const newAccent = e.target.value;
            if (validAccents.includes(newAccent)) {
                voiceSettings.accent = newAccent;
                currentLanguage = newAccent; // Update currentLanguage for speech synthesis
                localStorage.setItem('poseidonAccent', newAccent);
                
                console.log('[Poseidon] Language changed to:', newAccent);
                
                // Reload voices for new accent
                updateVoiceSelection();
                
                // Update recognition language - need to recreate instance for language change to work reliably
                // Many browsers require recreating the SpeechRecognition instance for language changes to take effect
                if (recognition && poseidonActive && !poseidonPaused) {
                    console.log('[Poseidon] Language changed to:', newAccent, '- recreating recognition instance for language change');
                    
                    // Store current state
                    const wasListening = (recognitionState === 'listening');
                    
                    try {
                        // Stop current recognition
                        if (wasListening) {
                            recognition.stop();
                            console.log('[Poseidon] Stopped recognition for language change');
                        }
                        
                        // Clear handlers and recreate recognition instance
                        recognition.onstart = null;
                        recognition.onend = null;
                        recognition.onresult = null;
                        recognition.onerror = null;
                        recognition.onnomatch = null;
                        recognition.onaudiostart = null;
                        recognition.onaudioend = null;
                        recognition.onsoundstart = null;
                        recognition.onsoundend = null;
                        recognition.onspeechstart = null;
                        recognition.onspeechend = null;
                        
                        recognition = null;
                        recognitionState = 'idle';
                        
                        // Recreate recognition instance with new language
                        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                        if (SpeechRecognition) {
                            setTimeout(async () => {
                                if (poseidonActive && !poseidonPaused) {
                                    try {
                                        recognition = new SpeechRecognition();
                                        recognition.continuous = true;
                                        recognition.interimResults = true;
                                        recognition.lang = newAccent; // Set the new language
                                        recognition.maxAlternatives = 1;
                                        
                                        console.log('[Poseidon] Recognition instance recreated with language:', recognition.lang);
                                        
                                        // Setup handlers again
                                        setupRecognitionHandlers();
                                        
                                        // Restart recognition if it was listening before
                                        if (wasListening) {
                                            setTimeout(() => {
                                                startRecognitionWithRetry();
                                            }, 500);
                                        }
                                    } catch (err) {
                                        console.error('[Poseidon] Error recreating recognition with new language:', err);
                                        // Try to continue with old instance if recreation fails
                                        if (!recognition) {
                                            recognition = new SpeechRecognition();
                                            recognition.lang = newAccent;
                                            setupRecognitionHandlers();
                                        }
                                    }
                                }
                            }, 500);
                        }
                    } catch (e) {
                        console.warn('[Poseidon] Error stopping recognition for language change:', e);
                        // Fallback: try to set language on existing instance
                        if (recognition) {
                            recognition.lang = newAccent;
                            console.log('[Poseidon] Set language on existing instance:', recognition.lang);
                        }
                    }
                } else if (recognition) {
                    // Just set the language for future use (will take effect when recognition starts)
                    recognition.lang = newAccent;
                    console.log('[Poseidon] Recognition language set to:', recognition.lang, '(not active, will use on next start)');
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
        console.log('[Poseidon] Launch button found, attaching click listener');
        poseidonLaunchBtn.addEventListener('click', (e) => {
            console.log('[Poseidon] Launch button clicked!');
            e.preventDefault();
            e.stopPropagation();
            openPoseidonOverlay();
        });
    } else {
        console.error('[Poseidon] Launch button NOT FOUND! Check HTML element ID.');
    }
    
    // Setup overlay elements
    poseidonOverlay = document.getElementById('poseidonOverlay');
    poseidonVisualizer = document.getElementById('poseidonVisualizer');
    poseidonStatusIndicator = document.getElementById('poseidonStatusIndicator');
    poseidonStatusText = document.getElementById('poseidonStatusText');
    poseidonUserTranscript = document.getElementById('poseidonUserTranscript');
    poseidonAssistantTranscript = document.getElementById('poseidonAssistantTranscript');
    
    // Load 3D Poseidon UI setting (default: false)
    poseidon3DEnabled = localStorage.getItem('poseidon3DEnabled') === 'true';
    console.log('[Poseidon] 3D UI enabled:', poseidon3DEnabled);
    
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
        
        // Filter voices by accent and gender (v3.x: Enhanced with new languages)
        const accentMap = {
            'en-US': ['en-US', 'en_US', 'en'],
            'en-GB': ['en-GB', 'en_GB'],
            'en-AU': ['en-AU', 'en_AU'],
            'en-IN': ['en-IN', 'en_IN'],
            'hi-IN': ['hi-IN', 'hi_IN', 'hi'],
            'ta-IN': ['ta-IN', 'ta_IN', 'ta'],
            'te-IN': ['te-IN', 'te_IN', 'te'],
            'es-ES': ['es-ES', 'es_ES', 'es', 'es-MX'],
            'es-MX': ['es-MX', 'es_MX', 'es'],
            'fr-FR': ['fr-FR', 'fr_FR', 'fr'],
            'de-DE': ['de-DE', 'de_DE', 'de'],
            'it-IT': ['it-IT', 'it_IT', 'it'],
            'pt-BR': ['pt-BR', 'pt_BR', 'pt'],
            'ja-JP': ['ja-JP', 'ja_JP', 'ja'],
            'ko-KR': ['ko-KR', 'ko_KR', 'ko'],
            'zh-CN': ['zh-CN', 'zh_CN', 'zh', 'cmn', 'zh-Hans-CN']  // v3.x: Mandarin
        };
        
        const targetLocales = accentMap[voiceSettings.accent] || [voiceSettings.accent] || ['en-US'];
        const targetGender = voiceSettings.gender === 'male' ? 'male' : 'female';
        
        // Find matching voice
        let selectedVoice = null;
        let matchedVoices = [];
        
        // First, collect all voices matching the language/locale
        for (const voice of voices) {
            const voiceLocale = voice.lang.toLowerCase();
            const voiceName = voice.name.toLowerCase();
            
            // Check if voice matches any of the target locales (using startsWith for partial matches)
            const matches = targetLocales.some(locale => {
                const localeLower = locale.toLowerCase();
                return voiceLocale === localeLower || voiceLocale.startsWith(localeLower + '-') || voiceLocale.startsWith(localeLower + '_');
            });
            
            if (matches) {
                matchedVoices.push(voice);
            }
        }
        
        // If we found matching voices, try to match gender preference
        if (matchedVoices.length > 0) {
            // Check gender (some voices have gender info in name)
            for (const voice of matchedVoices) {
                const voiceName = voice.name.toLowerCase();
                const isMale = voiceName.includes('male') || voiceName.includes('david') || 
                              voiceName.includes('daniel') || voiceName.includes('james') ||
                              voiceName.includes('thomas') || voiceName.includes('mark') ||
                              voiceName.includes('tom') || voiceName.includes('alex') ||
                              voiceName.includes('fred') || voiceName.includes('ralph');
                const isFemale = voiceName.includes('female') || voiceName.includes('samantha') ||
                                voiceName.includes('karen') || voiceName.includes('susan') ||
                                voiceName.includes('victoria') || voiceName.includes('zira') ||
                                voiceName.includes('sarah') || voiceName.includes('anna') ||
                                voiceName.includes('kate') || voiceName.includes('linda');
                
                if (targetGender === 'male' && isMale) {
                    selectedVoice = voice;
                    break;
                } else if (targetGender === 'female' && isFemale) {
                    selectedVoice = voice;
                    break;
                }
            }
            
            // If no gender match, use first matching voice
            if (!selectedVoice) {
                selectedVoice = matchedVoices[0];
            }
        }
        
        // Final fallback: any voice with matching locale (without gender preference)
        if (!selectedVoice) {
            for (const voice of voices) {
                const voiceLocale = voice.lang.toLowerCase();
                if (targetLocales.some(locale => {
                    const localeLower = locale.toLowerCase();
                    return voiceLocale === localeLower || voiceLocale.startsWith(localeLower + '-') || voiceLocale.startsWith(localeLower + '_');
                })) {
                    selectedVoice = voice;
                    break;
                }
            }
        }
        
        // Absolute fallback: use any voice if available
        if (!selectedVoice && voices.length > 0) {
            // Try to prefer a voice that at least matches the base language code
            const baseLang = voiceSettings.accent.split('-')[0].toLowerCase();
            for (const voice of voices) {
                if (voice.lang.toLowerCase().startsWith(baseLang)) {
                    selectedVoice = voice;
                    break;
                }
            }
            // If still no match, use first available voice
            if (!selectedVoice) {
                selectedVoice = voices[0];
            }
        }
        
        currentVoice = selectedVoice;
        
        if (selectedVoice) {
            console.log('[Poseidon] Voice selection:', {
                requestedAccent: voiceSettings.accent,
                targetLocales: targetLocales,
                matchedVoicesCount: matchedVoices.length,
                selectedVoice: {
                    name: selectedVoice.name,
                    lang: selectedVoice.lang,
                    accent: voiceSettings.accent
                }
            });
        } else {
            console.warn('[Poseidon] No voice selected for accent:', voiceSettings.accent);
        }
        
        // Ensure currentLanguage matches the selected accent
        if (voiceSettings.accent) {
            currentLanguage = voiceSettings.accent;
        }
    };
    
    loadVoices();
    speechSynthesis.onvoiceschanged = loadVoices;
}

// Version 3.0.0: Enhanced speakText with adaptive parameters and interruption support
function speakText(text, speed = null, volume = null) {
    if (!('speechSynthesis' in window) || !currentVoice) {
        console.warn('Speech synthesis not available');
        return;
    }
    
    // Version 3.0.0: Stop any ongoing speech (allows interruption)
    if (interruptionEnabled && isSpeaking) {
        console.log('[Poseidon] Interrupting current speech');
        speechSynthesis.cancel();
    }
    
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
    
    // Store the cleaned text that will be spoken (for filtering self-hearing)
    lastSpokenText = cleanText;
    console.log('[Poseidon] Storing spoken text for filtering:', cleanText.substring(0, 100) + (cleanText.length > 100 ? '...' : ''));
    
    // Note: We'll stop recognition in utterance.onstart when speech actually begins
    // This ensures recognition only stops when speech actually starts, not just when we queue it
    
    // Version 3.0.0: Use adaptive parameters
    const speechSpeed = speed !== null ? speed : currentSpeechSpeed;
    const speechVolume = volume !== null ? volume : currentSpeechVolume;
    
    // Version 3.x: Enhanced emotion-based adaptation with stress/tone variations
    // Creative Enhancement: Better emotion detection and Hindi-specific improvements
    const recentEmotions = emotionHistory.slice(-5);
    let emotionGuidance = { speed: 1.0, pitch: 1.0, tone: 'neutral' };
    if (recentEmotions.length > 0) {
        const dominantEmotion = getDominantEmotion(recentEmotions);
        emotionGuidance = getEmotionBasedGuidance(dominantEmotion);
        // Adjust speed based on emotion
        const adaptedSpeed = speechSpeed * emotionGuidance.speed;
        currentSpeechSpeed = Math.max(0.5, Math.min(2.0, adaptedSpeed));
    }
    
    // Version 3.x: Add stress and tone variations to make speech more human-like
    const enhancedText = addSpeechStressAndTone(cleanText, emotionGuidance);
    
    const utterance = new SpeechSynthesisUtterance(enhancedText);
    
    // Set voice first - this is critical for language support
    if (currentVoice) {
        utterance.voice = currentVoice;
        // If voice has a language, use it; otherwise use the selected accent
        utterance.lang = currentVoice.lang || voiceSettings.accent || currentLanguage;
        
        // Set rate and pitch for all languages
        utterance.rate = currentSpeechSpeed;
        utterance.pitch = emotionGuidance.pitch || 1.0;
        
        console.log('[Poseidon] Speech synthesis settings:', {
            voiceName: currentVoice.name,
            voiceLang: currentVoice.lang,
            utteranceLang: utterance.lang,
            selectedAccent: voiceSettings.accent,
            currentLanguage: currentLanguage,
            rate: utterance.rate,
            pitch: utterance.pitch
        });
    } else {
        // Fallback if no voice selected
        utterance.lang = voiceSettings.accent || currentLanguage || 'en-US';
        utterance.rate = currentSpeechSpeed;
        utterance.pitch = emotionGuidance.pitch || 1.0;
        console.warn('[Poseidon] No voice selected, using lang:', utterance.lang);
    }
    
    utterance.volume = currentSpeechVolume;
    
    // Version 3.x: Add pauses and emphasis for more natural speech
    // This is done through text processing since Web Speech API has limited SSML support
    // We'll adjust rate dynamically and add punctuation pauses
    
    // Version 3.0.0: Enable interruption detection
    canInterrupt = true;
    
    utterance.onstart = () => {
        console.log('[Poseidon] 🗣️ Speaking started');
        updatePoseidonStatus('speaking', 'Speaking...');
        isSpeaking = true;
        
        // Stop recognition BEFORE speaking to prevent hearing itself
        // CRITICAL: Must stop recognition BEFORE speech starts to prevent any queued results
        if (recognition) {
            try {
                const currentState = recognitionState;
                if (currentState === 'listening' || currentState === 'starting') {
                    console.log('[Poseidon] Stopping recognition BEFORE speaking to prevent self-hearing (state:', currentState, ')');
                    recognition.stop();
                    recognitionState = 'paused';
                    // Give recognition a moment to fully stop and clear any queued results
                    // Use setTimeout instead of await since this is in a callback
                    setTimeout(() => {
                        console.log('[Poseidon] Recognition should be fully stopped now');
                    }, 200);
                }
            } catch (e) {
                console.warn('[Poseidon] Error stopping recognition before speech:', e);
            }
        }
    };
    
    utterance.onend = () => {
        console.log('[Poseidon] ✅ Finished speaking');
        isSpeaking = false;
        lastSpokenTime = Date.now();
        // Stop 3D animation lip-sync (v3.x)
        if (poseidon3D && typeof poseidon3D.stop === 'function') {
            poseidon3D.stop();
        }
        console.log('[Poseidon] Marked speech as finished, will filter matching transcripts for', SPEECH_MATCH_WINDOW_MS, 'ms');
        
        // After speaking, wait longer before resuming recognition to prevent hearing echo
        // Increased delay for Electron app (more echo issues) and better self-hearing prevention
        if (poseidonActive && !poseidonPaused) {
            const isElectron = window.electronAPI !== undefined;
            // Use moderate delay to prevent echo - reduced from previous values for better responsiveness
            const resumeDelay = isElectron ? 1500 : 1000;
            
            console.log(`[Poseidon] Will resume recognition after ${resumeDelay}ms delay to prevent echo`);
            
            setTimeout(() => {
                if (poseidonActive && !poseidonPaused && !isSpeaking) {
                    restartRecognitionAfterSpeech();
                } else {
                    console.log('[Poseidon] Not restarting recognition:', {
                        poseidonActive,
                        poseidonPaused,
                        isSpeaking
                    });
                }
            }, resumeDelay);
        }
        
        // Helper function to restart recognition after speech
        function restartRecognitionAfterSpeech() {
            // Check circuit breaker first
            if (serviceNotAllowedDisabled) {
                console.warn('[Poseidon] Circuit breaker active - not restarting recognition after speech');
                return;
            }
            
            if (!recognition || !poseidonActive || poseidonPaused || isSpeaking) {
                console.log('[Poseidon] Cannot restart recognition - conditions not met:', {
                    hasRecognition: !!recognition,
                    poseidonActive: poseidonActive,
                    poseidonPaused: poseidonPaused,
                    isSpeaking: isSpeaking
                });
                return;
            }
            
            try {
                console.log('[Poseidon] Resuming recognition after speech ended');
                // Use startRecognitionWithRetry instead of direct start for better error handling
                // This ensures proper initialization and error handling
                startRecognitionWithRetry();
                console.log('[Poseidon] ✅ Recognition restart initiated after speech');
            } catch (e) {
                console.warn('[Poseidon] Error resuming recognition, will retry:', e);
                startRecognitionWithRetry();
            }
        }
    };
    
    utterance.onerror = (event) => {
        console.error('[Poseidon] ERROR in speech synthesis:', event);
        console.error('[Poseidon] Speech error details:', {
            error: event.error,
            charIndex: event.charIndex,
            type: event.type
        });
        isSpeaking = false;
        lastSpokenTime = Date.now();
        
        // Stop 3D animation on error
        if (poseidon3D && typeof poseidon3D.stop === 'function') {
            poseidon3D.stop();
        }
        
        // Return to listening on error, but only restart if not in circuit breaker mode
        if (poseidonActive && !poseidonPaused && !serviceNotAllowedDisabled) {
            // Schedule restart after a delay using startRecognitionWithRetry (has circuit breaker checks)
            setTimeout(() => {
                if (poseidonActive && !poseidonPaused && !isSpeaking) {
                    console.log('[Poseidon] Attempting to restart recognition after speech error');
                    startRecognitionWithRetry();
                }
            }, 1000);
        } else {
            updatePoseidonStatus('ready', 'Speech Error');
        }
    };
    
    speechSynthesis.speak(utterance);
}

async function openPoseidonOverlay() {
    console.log('[Poseidon] Opening overlay...');
    
    // Ensure overlay element exists
    if (!poseidonOverlay) {
        poseidonOverlay = document.getElementById('poseidonOverlay');
        if (!poseidonOverlay) {
            console.error('[Poseidon] ERROR: poseidonOverlay element not found in DOM!');
            alert('Poseidon overlay element not found. Please refresh the page.');
            return;
        }
        console.log('[Poseidon] Found overlay element on-demand');
    }
    
    // Show overlay immediately (before requesting permissions) for faster UI response
    poseidonOverlay.style.display = 'flex';
    poseidonOverlay.style.visibility = 'visible';
    poseidonOverlay.style.opacity = '1';
    poseidonOverlay.style.zIndex = '10000';
    poseidonOverlay.classList.add('active');
    updatePoseidonStatus('ready', 'Initializing...');
    
    // Reset circuit breaker for Electron apps - network errors shouldn't persist
    const isElectron = window.electronAPI !== undefined;
    if (isElectron && serviceNotAllowedDisabled) {
        console.log('[Poseidon] Electron: Resetting circuit breaker on overlay open');
        serviceNotAllowedDisabled = false;
        rapidErrorTimes = []; // Clear error tracking
        serviceNotAllowedRetryCount = 0;
        lastServiceNotAllowedTime = 0;
    }
    
    try {
        // Version 3.0.0: Initialize session
        window.poseidonSessionStart = Date.now();
        emotionHistory = [];
        conversationSummaries = [];
        
        // Initialize 3D animation if enabled in settings (Beta feature)
        if (poseidon3DEnabled && poseidonVisualizer && !poseidon3D && typeof Poseidon3D !== 'undefined' && typeof THREE !== 'undefined') {
            try {
                // Clear wave animation and set up 3D container
                poseidonVisualizer.innerHTML = '';
                poseidonVisualizer.style.width = '100%';
                poseidonVisualizer.style.height = '100%';
                poseidonVisualizer.style.position = 'relative';
                poseidonVisualizer.style.overflow = 'hidden';
                poseidonVisualizer.style.backgroundColor = 'transparent';
                poseidonVisualizer.classList.add('poseidon-3d-container');
                
                // Initialize 3D animation
                poseidon3D = new Poseidon3D(poseidonVisualizer);
                console.log('[Poseidon] 3D animation initialized (Beta)');
            } catch (error) {
                console.error('[Poseidon] Failed to initialize 3D animation (falling back to wave):', error);
                poseidon3D = null;
                poseidon3DEnabled = false;
                // Restore wave animation on error
                if (poseidonVisualizer) {
                    poseidonVisualizer.innerHTML = '<div class="poseidon-wave"><div class="wave-bar"></div><div class="wave-bar"></div><div class="wave-bar"></div><div class="wave-bar"></div><div class="wave-bar"></div></div>';
                    poseidonVisualizer.classList.remove('poseidon-3d-container');
                    poseidonVisualizer.style = '';
                }
            }
        } else if (poseidon3DEnabled && (typeof THREE === 'undefined' || typeof Poseidon3D === 'undefined')) {
            console.warn('[Poseidon] 3D UI enabled but Three.js or Poseidon3D not available');
            poseidon3DEnabled = false;
            localStorage.setItem('poseidon3DEnabled', 'false');
            const checkbox = document.getElementById('poseidon3DEnabled');
            if (checkbox) {
                checkbox.checked = false;
            }
        } else if (!poseidon3DEnabled && poseidonVisualizer) {
            // Ensure wave animation is shown when 3D is disabled
            if (!poseidonVisualizer.querySelector('.poseidon-wave')) {
                poseidonVisualizer.innerHTML = '<div class="poseidon-wave"><div class="wave-bar"></div><div class="wave-bar"></div><div class="wave-bar"></div><div class="wave-bar"></div><div class="wave-bar"></div></div>';
            }
            poseidonVisualizer.classList.remove('poseidon-3d-container');
            // Reset inline styles to allow CSS to control styling
            poseidonVisualizer.removeAttribute('style');
        }
    } catch (initError) {
        console.error('[Poseidon] Error in overlay initialization (continuing):', initError);
    }
    
    // Detect browser
    const isSafari = /Safari/.test(navigator.userAgent) && !/Chrome/.test(navigator.userAgent);
    const isChrome = /Chrome/.test(navigator.userAgent) && /Google Inc/.test(navigator.vendor);
    const isEdge = /Edg/.test(navigator.userAgent);
    
    console.log('[Poseidon] Browser detection:', {
        isSafari: isSafari,
        isChrome: isChrome,
        isEdge: isEdge,
        userAgent: navigator.userAgent
    });
    
    // Check browser support
    const hasWebkitSpeech = 'webkitSpeechRecognition' in window;
    const hasSpeech = 'SpeechRecognition' in window;
    
    if (!hasWebkitSpeech && !hasSpeech) {
        alert('Voice assistant is not supported in this browser. Please use Chrome, Edge, or Safari.');
        return;
    }
    
    // Safari-specific: Must use webkitSpeechRecognition and check if it actually works
    if (isSafari) {
        if (!hasWebkitSpeech) {
            alert('Safari requires webkitSpeechRecognition. Please use Safari 14.1 or later.');
            return;
        }
        
        // Safari speech recognition has very limited support
        // Test if we can actually create an instance
        try {
            const testRecognition = new window.webkitSpeechRecognition();
            console.log('[Poseidon] Safari: Successfully created test recognition instance');
            // Clean up test instance
            if (testRecognition) {
                try {
                    testRecognition.abort();
                } catch (e) {
                    // Ignore
                }
            }
        } catch (testErr) {
            console.error('[Poseidon] Safari: Cannot create speech recognition instance:', testErr);
            alert('⚠️ Safari Speech Recognition Not Available\n\n' +
                  'Safari speech recognition is not available on this system.\n\n' +
                  'Safari has very limited and unreliable support for speech recognition.\n' +
                  'The Web Speech API in Safari is experimental and may not work.\n\n' +
                  'For the best experience, please use:\n' +
                  '• Chrome (recommended)\n' +
                  '• Edge\n\n' +
                  'If you must use Safari, ensure:\n' +
                  '1. Safari 14.1 or later\n' +
                  '2. Using HTTPS (not HTTP)\n' +
                  '3. Microphone permissions allowed\n\n' +
                  'Even with these settings, Safari speech recognition may not work.');
            return;
        }
        
        console.log('[Poseidon] Safari: Speech recognition appears to be available (but may still not work)');
        console.warn('[Poseidon] Safari: Even if available, speech recognition may fail due to Safari limitations');
    }
    
    // Check secure context
    const isSecure = window.isSecureContext || location.protocol === 'https:' || 
                     location.hostname === 'localhost' || location.hostname === '127.0.0.1';
    if (!isSecure) {
        alert('Poseidon requires a secure connection (HTTPS) or localhost. Please access the site via HTTPS or localhost.');
        return;
    }
    
    // Safari-specific: Additional security check
    if (isSafari && location.protocol !== 'https:' && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
        alert('Safari requires HTTPS for speech recognition. Please use HTTPS or localhost.');
        return;
    }
    
    // Safari warning: Speech recognition support is very limited
    if (isSafari) {
        console.warn('[Poseidon] ⚠️ Safari detected - speech recognition support is very limited and unreliable');
        console.warn('[Poseidon] Safari may not support continuous recognition or may have other limitations');
        console.warn('[Poseidon] For best results, use Chrome or Edge');
    }
    
    // Request microphone permission and set up audio monitoring
    try {
        console.log('[Poseidon] Requesting microphone permission...');
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true
            } 
        });
        console.log('[Poseidon] Microphone permission granted');
        
        // IMPORTANT: Keep the stream alive for speech recognition to work
        // Don't stop it immediately - speech recognition needs active microphone access
        // Store it globally so it doesn't get garbage collected
        window.poseidonAudioStream = stream;
        
        // CRITICAL: Ensure stream stays active - prevent garbage collection
        // Keep a reference to at least one track to prevent it from being stopped
        const audioTracks = stream.getAudioTracks();
        if (audioTracks.length > 0) {
            // Ensure track is enabled and not muted
            audioTracks[0].enabled = true;
            audioTracks[0].muted = false;
            console.log('[Poseidon] Stream track ensured active:', {
                label: audioTracks[0].label,
                readyState: audioTracks[0].readyState,
                enabled: audioTracks[0].enabled,
                muted: audioTracks[0].muted
            });
        }
        
        if (poseidonOverlay) {
            // Overlay already shown at the start of function
            poseidonActive = true;
            console.log('[Poseidon] Overlay visible, setting poseidonActive=true');
            poseidonPaused = false;
            recognitionState = 'starting';
            
            // Reset all state
            pendingTranscript = '';
            transcriptProcessing = false;
            speechDetected = false;
            consecutiveNoSpeechCount = 0;
            serviceNotAllowedRetryCount = 0; // Reset retry counter
            lastServiceNotAllowedTime = 0;
            rapidErrorTimes = []; // Reset rapid error tracking
            serviceNotAllowedDisabled = false; // Reset circuit breaker
            lastSpeechTime = Date.now();
            clearTimeout(silenceTimeout);
            clearTimeout(recognitionRestartTimeout);
            
            // CRITICAL: Start recognition IMMEDIATELY after permission
            // Browsers require speech recognition to start in direct response to user action
            // Don't delay - start right away while we still have the user gesture context
            console.log('[Poseidon] Starting recognition immediately after permission...');
            
            // Verify stream is active
            if (stream && stream.active) {
                console.log('[Poseidon] Audio stream is active');
                const audioTracks = stream.getAudioTracks();
                if (audioTracks.length > 0 && audioTracks[0].readyState === 'live') {
                    console.log('[Poseidon] Audio track is live');
                }
            }
            
            // Create or recreate recognition instance
            // Safari requires webkitSpeechRecognition specifically - MUST use webkit prefix
            let SpeechRecognition;
            if (isSafari) {
                // Safari MUST use webkitSpeechRecognition
                if (!window.webkitSpeechRecognition) {
                    throw new Error('Safari requires webkitSpeechRecognition API. Please use Safari 14.1 or later.');
                }
                SpeechRecognition = window.webkitSpeechRecognition;
                console.log('[Poseidon] Safari detected - using webkitSpeechRecognition (required)');
            } else {
                // Chrome/Edge can use either
                SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            }
            
            if (!SpeechRecognition) {
                throw new Error('SpeechRecognition API not available');
            }
            
            console.log('[Poseidon] Using SpeechRecognition:', {
                hasSpeechRecognition: !!window.SpeechRecognition,
                hasWebkitSpeechRecognition: !!window.webkitSpeechRecognition,
                using: isSafari ? 'webkitSpeechRecognition (Safari)' : (window.SpeechRecognition ? 'SpeechRecognition' : 'webkitSpeechRecognition'),
                isSafari: isSafari
            });
            
            // Always create a fresh instance for reliability
            if (recognition) {
                try {
                    console.log('[Poseidon] Stopping existing recognition instance');
                    recognition.stop();
                    // Safari needs a moment to fully stop
                    if (isSafari) {
                        await new Promise(resolve => setTimeout(resolve, 100));
                    }
                } catch (e) {
                    // Ignore - might not be running
                }
            }
            
            try {
                recognition = new SpeechRecognition();
                console.log('[Poseidon] Created new SpeechRecognition instance');
                
                // CRITICAL: Configure IMMEDIATELY after creation
                // Safari-specific: May need different configuration
                recognition.continuous = true;
                recognition.interimResults = true;
                // MAJOR ENHANCEMENT: Explicit Hindi recognition language
                if (voiceSettings.accent === 'hi-IN' || currentLanguage === 'hi-IN') {
                    recognition.lang = 'hi-IN';
                    console.log('[Poseidon Hindi] Recognition language explicitly set to Hindi (hi-IN)');
                } else {
                    recognition.lang = voiceSettings.accent || currentLanguage || 'en-US';
                }
                recognition.maxAlternatives = 1;
                
                // Safari-specific: Some versions may need serviceURI set
                if (isSafari && 'serviceURI' in recognition) {
                    // Don't set serviceURI - let Safari use default
                    console.log('[Poseidon] Safari detected - using default serviceURI');
                }
                
                console.log('[Poseidon] Configuration set:', {
                    continuous: recognition.continuous,
                    interimResults: recognition.interimResults,
                    lang: recognition.lang,
                    isSafari: isSafari
                });
            } catch (createErr) {
                console.error('[Poseidon] ERROR creating SpeechRecognition instance:', createErr);
                throw createErr;
            }
            
            // Setup handlers BEFORE starting (Safari requirement)
            try {
                setupRecognitionHandlers();
                console.log('[Poseidon] Recognition handlers setup complete');
            } catch (handlerErr) {
                console.error('[Poseidon] ERROR setting up recognition handlers:', handlerErr);
                throw handlerErr;
            }
            
            // RE-CONFIGURE to ensure settings persist (especially important for Safari)
            recognition.continuous = true;
            recognition.interimResults = true;
            // MAJOR ENHANCEMENT: Explicit Hindi recognition language
            if (voiceSettings.accent === 'hi-IN' || currentLanguage === 'hi-IN') {
                recognition.lang = 'hi-IN';
                console.log('[Poseidon Hindi] Recognition language explicitly set to Hindi (hi-IN) in onstart');
            } else {
                // MAJOR ENHANCEMENT: Explicit Hindi recognition language
                if (voiceSettings.accent === 'hi-IN' || currentLanguage === 'hi-IN') {
                    recognition.lang = 'hi-IN';
                    console.log('[Poseidon Hindi] Recognition language explicitly set to Hindi (hi-IN)');
                } else {
                    recognition.lang = voiceSettings.accent || currentLanguage || 'en-US';
                }
            }
            recognition.maxAlternatives = 1;
            
            // CRITICAL: Start recognition IMMEDIATELY - no delays!
            // Web Speech API requires recognition.start() to be called in direct response to user gesture
            // Any setTimeout breaks the user gesture context and causes service-not-allowed errors
            console.log('[Poseidon] Starting recognition IMMEDIATELY (must be in user gesture context)...');
            
            // Verify stream is active
            if (!stream.active) {
                console.error('[Poseidon] ERROR: Stream not active before starting recognition');
                updatePoseidonStatus('ready', 'Error: Stream not active');
                return;
            }
            
            const streamTracks = stream.getAudioTracks();
            const activeTracks = streamTracks.filter(t => t.readyState === 'live' && t.enabled && !t.muted);
            if (activeTracks.length === 0) {
                console.error('[Poseidon] ERROR: No active tracks before starting recognition');
                updatePoseidonStatus('ready', 'Error: No active tracks');
                return;
            }
            
            console.log('[Poseidon] Stream verified active, starting recognition NOW...');
            
            // START IMMEDIATELY - this must happen in the user gesture context
            // Safari is especially strict about this - no delays allowed
            try {
                // Safari-specific: Ensure we're still in user gesture context
                if (isSafari) {
                    console.log('[Poseidon] Safari detected - starting recognition synchronously in user gesture context');
                    console.log('[Poseidon] Safari: Pre-start check:', {
                        hasRecognition: !!recognition,
                        continuous: recognition?.continuous,
                        interimResults: recognition?.interimResults,
                        lang: recognition?.lang,
                        streamActive: stream?.active,
                        hasStream: !!stream
                    });
                    
                    // Double-check configuration for Safari
                    recognition.continuous = true;
                    recognition.interimResults = true;
                    // MAJOR ENHANCEMENT: Explicit Hindi recognition language
                if (voiceSettings.accent === 'hi-IN' || currentLanguage === 'hi-IN') {
                    recognition.lang = 'hi-IN';
                    console.log('[Poseidon Hindi] Recognition language explicitly set to Hindi (hi-IN)');
                } else {
                    recognition.lang = voiceSettings.accent || currentLanguage || 'en-US';
                }
                    
                    // Safari may not support continuous mode - try without it if it fails
                    console.log('[Poseidon] Safari: Attempting to start with continuous mode');
                }
                
                recognition.start();
                console.log('[Poseidon] Recognition.start() called successfully', {
                    isSafari: isSafari,
                    continuous: recognition.continuous,
                    lang: recognition.lang
                });
                updatePoseidonStatus('listening', 'Listening...');
            } catch (startErr) {
                console.error('[Poseidon] ERROR starting recognition:', startErr);
                console.error('[Poseidon] Start error details:', {
                    name: startErr?.name,
                    message: startErr?.message,
                    streamActive: window.poseidonAudioStream?.active,
                    hasStream: !!window.poseidonAudioStream
                });
                
                // If it fails immediately, it's likely a permission or service issue
                // Safari: Don't try to recover - it's likely not supported
                if (isSafari) {
                    console.error('[Poseidon] Safari: Recognition.start() failed immediately:', startErr);
                    console.error('[Poseidon] Safari: This indicates Safari speech recognition is not available');
                    
                    const safariErrorMsg = 'Safari speech recognition is not available.\n\n' +
                                         'Safari has very limited support for the Web Speech API.\n\n' +
                                         'For the best experience, please use Chrome or Edge.\n\n' +
                                         'If you must use Safari:\n' +
                                         '1. Ensure Safari 14.1+\n' +
                                         '2. Use HTTPS (not HTTP)\n' +
                                         '3. Allow microphone in Safari Settings\n' +
                                         '4. Speech recognition may still not work due to Safari limitations';
                    
                    updatePoseidonStatus('ready', 'Safari Not Supported');
                    if (poseidonAssistantTranscript) {
                        poseidonAssistantTranscript.textContent = safariErrorMsg;
                    }
                    
                    // Try to speak the error
                    try {
                        speakText('Safari speech recognition is not available. Please use Chrome or Edge for better compatibility.');
                    } catch (speakErr) {
                        console.warn('[Poseidon] Could not speak error message:', speakErr);
                    }
                    
                    return; // Don't try to recover for Safari
                }
                
                // For Chrome/Edge: The error handler will try to recover automatically
                if (startErr.name === 'NotAllowedError' || startErr.message?.includes('permission') || startErr.message?.includes('service')) {
                    console.warn('[Poseidon] Initial start failed - error handler will attempt recovery');
                    updatePoseidonStatus('ready', 'Starting...');
                    // Don't show alert - let the error handler try to recover automatically
                    // The onerror handler will be triggered and attempt recovery
                } else {
                    updatePoseidonStatus('ready', 'Error starting: ' + (startErr.message || startErr.name));
                }
            }
            
            // Set up audio context AFTER starting recognition (non-blocking)
            setTimeout(() => {
                try {
                    audioContext = new (window.AudioContext || window.webkitAudioContext)();
                    analyser = audioContext.createAnalyser();
                    microphone = audioContext.createMediaStreamSource(stream);
                    analyser.fftSize = 256;
                    analyser.smoothingTimeConstant = 0.8;
                    microphone.connect(analyser);
                    startAudioLevelMonitoring();
                    console.log('[Poseidon] Audio context and monitoring setup complete');
                } catch (audioErr) {
                    console.warn('[Poseidon] Audio context setup failed (non-critical):', audioErr);
                }
            }, 100);
        }
    } catch (error) {
        console.error('[Poseidon] ERROR in openPoseidonOverlay:', error);
        console.error('[Poseidon] Error details:', {
            name: error?.name,
            message: error?.message,
            stack: error?.stack
        });
        
        if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
            alert('Microphone permission is required to use Poseidon. Please:\n\n1. Click the lock icon in your browser\'s address bar\n2. Allow microphone access\n3. Refresh the page and try again');
            updatePoseidonStatus('ready', 'Permission Required');
        } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
            alert('No microphone found. Please connect a microphone and try again.');
            updatePoseidonStatus('ready', 'No Microphone');
        } else {
            alert('Error starting Poseidon: ' + (error.message || 'Unknown error') + '\n\nPlease check your browser settings and try again.');
            updatePoseidonStatus('ready', 'Error');
        }
        recognitionState = 'idle';
    }
}

async function startRecognitionWithRetry(maxRetries = 3) {
    // CRITICAL: Check circuit breaker FIRST to prevent infinite loops
    // NOTE: Circuit breaker should NOT block Electron apps - network errors in Electron are often transient
    const isElectron = window.electronAPI !== undefined;
    if (serviceNotAllowedDisabled && !isElectron) {
        // Only apply circuit breaker to browser, not Electron
        console.warn('[Poseidon] 🛑 Circuit breaker is ACTIVE - stopping all recognition attempts to prevent infinite loop');
        updatePoseidonStatus('ready', 'Service Unavailable (Circuit Breaker Active)');
        if (poseidonAssistantTranscript) {
            poseidonAssistantTranscript.textContent = 'Speech recognition service is temporarily unavailable. Please close and reopen Poseidon to try again.';
        }
        return; // Exit immediately - do not attempt to start
    } else if (serviceNotAllowedDisabled && isElectron) {
        // Reset circuit breaker for Electron - network errors shouldn't trigger it
        console.log('[Poseidon] Electron: Resetting circuit breaker (network errors are transient in Electron)');
        serviceNotAllowedDisabled = false;
        rapidErrorTimes = []; // Clear error tracking
    }
    
    if (!recognition) {
        console.error('[Poseidon] ERROR: Cannot start recognition - recognition is null');
        updatePoseidonStatus('ready', 'Error: Recognition not initialized');
        return;
    }
    
    // CRITICAL: Ensure poseidonActive is true if overlay is open
    // This prevents the infinite listening issue where recognition can't start
    // This is the PRIMARY fix for the infinite listening problem
    // Check multiple ways to detect if overlay is open
    const overlayVisible = poseidonOverlay && (
        poseidonOverlay.style.display !== 'none' ||
        poseidonOverlay.style.display === 'flex' ||
        poseidonOverlay.offsetParent !== null || // Element is visible
        window.getComputedStyle(poseidonOverlay).display !== 'none'
    );
    
    if (overlayVisible) {
        poseidonActive = true;
        poseidonPaused = false;
        console.log('[Poseidon] ✅ Ensured poseidonActive=true (overlay is visible) - PRIMARY FIX for infinite listening');
    } else {
        console.warn('[Poseidon] ⚠️ Overlay check failed in startRecognitionWithRetry:', {
            overlayExists: !!poseidonOverlay,
            displayStyle: poseidonOverlay?.style?.display,
            computedDisplay: poseidonOverlay ? window.getComputedStyle(poseidonOverlay).display : 'N/A',
            offsetParent: poseidonOverlay?.offsetParent !== null
        });
    }
    
    // Double-check and force if needed
    if (!poseidonActive && poseidonOverlay && poseidonOverlay.style.display !== 'none') {
        console.error('[Poseidon] ❌ CRITICAL: poseidonActive is false but overlay is open! Forcing active...');
        poseidonActive = true;
        poseidonPaused = false;
    }
    
    if (!poseidonActive) {
        console.warn('[Poseidon] Cannot start recognition - Poseidon is not active', {
            overlayOpen: poseidonOverlay && poseidonOverlay.style.display !== 'none',
            overlayExists: !!poseidonOverlay
        });
        return;
    }
    
    // CRITICAL: Verify audio stream is active before starting recognition
    if (!window.poseidonAudioStream) {
        console.error('[Poseidon] ERROR: No audio stream available!');
        updatePoseidonStatus('ready', 'Error: No microphone access');
        return;
    }
    
    // Check stream and tracks
    const stream = window.poseidonAudioStream;
    const tracks = stream.getAudioTracks();
    const activeTracks = tracks.filter(t => t.readyState === 'live' && t.enabled && !t.muted);
    
    console.log('[Poseidon] Stream verification:', {
        streamActive: stream.active,
        totalTracks: tracks.length,
        activeTracks: activeTracks.length,
        tracksState: tracks.map(t => ({
            label: t.label,
            readyState: t.readyState,
            enabled: t.enabled,
            muted: t.muted
        }))
    });
    
    if (!stream.active || activeTracks.length === 0) {
        console.error('[Poseidon] ERROR: Audio stream is not active!');
        console.error('[Poseidon] Stream state:', {
            active: stream.active,
            activeTracks: activeTracks.length,
            allTracks: tracks.length
        });
        
        // Try to re-enable tracks first
        if (tracks.length > 0) {
            console.log('[Poseidon] Attempting to re-enable tracks...');
            tracks.forEach(track => {
                if (track.readyState !== 'ended') {
                    track.enabled = true;
                    track.muted = false;
                    console.log('[Poseidon] Re-enabled track:', track.label, 'state:', track.readyState);
                }
            });
            
            // Wait a moment and check again
            await new Promise(resolve => setTimeout(resolve, 500));
            const recheckTracks = stream.getAudioTracks().filter(t => t.readyState === 'live' && t.enabled && !t.muted);
            if (recheckTracks.length > 0 && stream.active) {
                console.log('[Poseidon] Stream recovered after re-enabling tracks');
            } else {
                console.error('[Poseidon] Stream still not active after re-enabling - re-requesting stream...');
                
                // Re-request the stream
                try {
                    // Stop old tracks
                    tracks.forEach(track => track.stop());
                    
                    const newStream = await navigator.mediaDevices.getUserMedia({ 
                        audio: {
                            echoCancellation: true,
                            noiseSuppression: true,
                            autoGainControl: true
                        }
                    });
                    
                    window.poseidonAudioStream = newStream;
                    
                    // Verify new stream
                    const newTracks = newStream.getAudioTracks();
                    const newActiveTracks = newTracks.filter(t => t.readyState === 'live' && t.enabled && !t.muted);
                    
                    if (!newStream.active || newActiveTracks.length === 0) {
                        console.error('[Poseidon] Re-requested stream is still not active!');
                        updatePoseidonStatus('ready', 'Error: Microphone not active');
                        return;
                    }
                    
                    console.log('[Poseidon] Stream re-requested and verified active');
                    
                    // Update audio context if needed
                    if (audioContext && audioContext.state !== 'closed') {
                        try {
                            if (microphone) {
                                microphone.disconnect();
                            }
                            microphone = audioContext.createMediaStreamSource(newStream);
                            analyser = audioContext.createAnalyser();
                            analyser.fftSize = 256;
                            analyser.smoothingTimeConstant = 0.8;
                            microphone.connect(analyser);
                        } catch (audioErr) {
                            console.warn('[Poseidon] Could not reconnect audio context:', audioErr);
                        }
                    }
                } catch (streamErr) {
                    console.error('[Poseidon] ERROR re-requesting stream:', streamErr);
                    updatePoseidonStatus('ready', 'Error: Microphone not active');
                    return;
                }
            }
        } else {
            console.error('[Poseidon] No tracks available - re-requesting stream...');
            try {
                const newStream = await navigator.mediaDevices.getUserMedia({ 
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    }
                });
                window.poseidonAudioStream = newStream;
                console.log('[Poseidon] Stream re-requested successfully');
            } catch (streamErr) {
                console.error('[Poseidon] ERROR re-requesting stream:', streamErr);
                updatePoseidonStatus('ready', 'Error: No microphone tracks');
                return;
            }
        }
    }
    
    console.log('[Poseidon] ✅ Audio stream verified -', activeTracks.length, 'active track(s) before starting recognition');
    
    let retryCount = 0;
    
    const attemptStart = async () => {
        if (!poseidonActive || poseidonPaused) {
            console.log('[Poseidon] Start attempt cancelled - inactive or paused');
            recognitionState = 'idle';
            return;
        }
        
        // CRITICAL: Verify and FORCE configuration before starting
        // Some browsers reset properties, so we must set them right before start
        let configChanged = false;
        
        if (recognition.continuous !== true) {
            console.warn('[Poseidon] Recognition continuous mode incorrect, fixing...', {
                current: recognition.continuous,
                expected: true
            });
            recognition.continuous = true;
            configChanged = true;
        }
        if (recognition.interimResults !== true) {
            console.warn('[Poseidon] Recognition interimResults incorrect, fixing...', {
                current: recognition.interimResults,
                expected: true
            });
            recognition.interimResults = true;
            configChanged = true;
        }
        if (recognition.lang !== voiceSettings.accent) {
            console.warn('[Poseidon] Recognition lang incorrect, fixing...', {
                current: recognition.lang,
                expected: voiceSettings.accent
            });
            // MAJOR ENHANCEMENT: Explicit Hindi recognition language
            if (voiceSettings.accent === 'hi-IN' || currentLanguage === 'hi-IN') {
                recognition.lang = 'hi-IN';
                console.log('[Poseidon Hindi] Recognition language explicitly set to Hindi (hi-IN) in onstart');
            } else {
                // MAJOR ENHANCEMENT: Explicit Hindi recognition language
                if (voiceSettings.accent === 'hi-IN' || currentLanguage === 'hi-IN') {
                    recognition.lang = 'hi-IN';
                    console.log('[Poseidon Hindi] Recognition language explicitly set to Hindi (hi-IN)');
                } else {
                    recognition.lang = voiceSettings.accent || currentLanguage || 'en-US';
                }
            }
            configChanged = true;
        }
        if (recognition.maxAlternatives !== 1) {
            recognition.maxAlternatives = 1;
            configChanged = true;
        }
        
        if (configChanged) {
            console.log('[Poseidon] Configuration was corrected before start');
        }
        
        // Set configuration one more time to be absolutely sure
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = voiceSettings.accent;
        recognition.maxAlternatives = 1;
        
        try {
            console.log(`[Poseidon] Starting recognition attempt ${retryCount + 1}/${maxRetries + 1}...`);
            
            // CRITICAL: Final verification - ensure audio stream is active before starting
            if (!window.poseidonAudioStream) {
                throw new Error('Audio stream is null - cannot start recognition');
            }
            
            if (!window.poseidonAudioStream.active) {
                console.error('[Poseidon] ERROR: Stream is not active before start!');
                throw new Error('Audio stream is not active - cannot start recognition');
            }
            
            const finalTracks = window.poseidonAudioStream.getAudioTracks();
            const finalActiveTracks = finalTracks.filter(t => t.readyState === 'live' && t.enabled && !t.muted);
            
            if (finalActiveTracks.length === 0) {
                console.error('[Poseidon] ERROR: No active tracks before start!');
                throw new Error('No active audio tracks - cannot start recognition');
            }
            
            console.log('[Poseidon] Recognition state before start:', {
                continuous: recognition.continuous,
                interimResults: recognition.interimResults,
                lang: recognition.lang,
                maxAlternatives: recognition.maxAlternatives,
                hasAudioStream: !!window.poseidonAudioStream,
                audioStreamActive: window.poseidonAudioStream.active,
                activeTracks: finalActiveTracks.length,
                totalTracks: finalTracks.length
            });
            
            console.log('[Poseidon] Audio tracks status:', finalTracks.map(t => ({
                label: t.label,
                readyState: t.readyState,
                enabled: t.enabled,
                muted: t.muted
            })));
            
            recognitionState = 'starting';
            
            // Start immediately - no delay, we need to maintain user gesture context
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
            console.error(`[Poseidon] ERROR starting recognition (attempt ${retryCount + 1}):`, err);
            console.error('[Poseidon] Start error details:', {
                name: err?.name,
                message: err?.message,
                stack: err?.stack,
                recognitionState: recognitionState,
                hasRecognition: !!recognition,
                recognitionConfig: recognition ? {
                    continuous: recognition.continuous,
                    interimResults: recognition.interimResults,
                    lang: recognition.lang
                } : null
            });
            
            if (err.name === 'InvalidStateError') {
                // Recognition might already be running, try to stop and restart
                console.log('[Poseidon] InvalidStateError - recognition may already be running');
                try {
                    recognition.stop();
                    console.log('[Poseidon] Stopped existing recognition, will retry...');
                    // Wait for it to fully stop
                    await new Promise(resolve => setTimeout(resolve, 300));
                } catch (stopErr) {
                    console.error('[Poseidon] ERROR stopping recognition:', stopErr);
                    console.error('[Poseidon] Stop error details:', {
                        name: stopErr?.name,
                        message: stopErr?.message,
                        recognitionState: recognitionState
                    });
                }
                
                // CRITICAL: Don't retry if circuit breaker is active
                if (serviceNotAllowedDisabled) {
                    console.warn('[Poseidon] Circuit breaker active - not retrying recognition start');
                    updatePoseidonStatus('ready', 'Service Unavailable');
                    return;
                }
                
                if (retryCount < maxRetries) {
                    retryCount++;
                    const delay = 300 * retryCount; // Increased delay
                    console.log(`[Poseidon] Retrying in ${delay}ms (attempt ${retryCount + 1}/${maxRetries + 1})`);
                    setTimeout(() => {
                        // Check circuit breaker again before retry
                        if (!serviceNotAllowedDisabled && poseidonActive) {
                            attemptStart();
                        } else {
                            console.warn('[Poseidon] Retry cancelled - circuit breaker active or Poseidon inactive');
                        }
                    }, delay); // Exponential backoff
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
            } else if (err.name === 'NotAllowedError' || err.message?.includes('permission')) {
                console.error('[Poseidon] Permission error - user needs to grant microphone access');
                updatePoseidonStatus('ready', 'Permission Required');
                recognitionState = 'idle';
                alert('Microphone permission is required. Please allow microphone access and try again.');
            } else {
                console.error('[Poseidon] Unknown error starting recognition');
                updatePoseidonStatus('ready', 'Error: ' + (err.message || 'Unknown'));
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
    
    console.log('[Poseidon] Starting audio level monitoring with volume decline detection');
    
    // Reset audio tracking
    lastHighVolumeTime = Date.now();
    currentAudioLevel = 0;
    audioLevelHistory = [];
    
    try {
        const dataArray = new Uint8Array(analyser.frequencyBinCount);
        let volumeDeclineStartTime = null;
        let wasSpeaking = false;
        
        audioLevelCheckInterval = setInterval(() => {
            if (!analyser || !poseidonActive || poseidonPaused) return;
            
            try {
                analyser.getByteFrequencyData(dataArray);
                const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
                const audioLevel = average / 255;
                currentAudioLevel = audioLevel;
                
                // Keep history (last 20 samples = ~2 seconds) - v3.0.0: Enhanced
                audioLevelHistory.push(audioLevel);
                if (audioLevelHistory.length > 20) {
                    audioLevelHistory.shift();
                }
                
                // Version 3.0.0: Adaptive sensitivity
                if (audioLevelHistory.length >= 10) {
                    adaptListeningSensitivity(audioLevelHistory);
                }
                
                // Update visualizer if available
                if (poseidonVisualizer) {
                    const level = Math.min(audioLevel * 100, 100);
                    poseidonVisualizer.style.setProperty('--audio-level', `${level}%`);
                }
                
                // Detect speech and volume decline
                const isSpeaking = audioLevel > AUDIO_LEVEL_THRESHOLD;
                const isSilent = audioLevel < VOLUME_DECLINE_THRESHOLD;
                
                if (isSpeaking) {
                    // High volume detected - user is speaking
                    if (!wasSpeaking) {
                        wasSpeaking = true;
                        speechDetected = true;
                        lastHighVolumeTime = Date.now();
                        lastSpeechTime = Date.now();
                        volumeDeclineStartTime = null;
                        consecutiveNoSpeechCount = 0;
                        console.log('[Poseidon] 🔊 Speech detected - volume:', audioLevel.toFixed(3));
                        updatePoseidonStatus('listening', 'Listening... (speaking detected)');
                        
                        // Version 3.0.0: Handle interruption
                        if (canInterrupt && isSpeaking && speechSynthesis.speaking) {
                            console.log('[Poseidon] 🛑 User interrupting - stopping speech');
                            speechSynthesis.cancel();
                            isSpeaking = false;
                            canInterrupt = false;
                            updatePoseidonStatus('listening', 'Listening... (interrupted)');
                        }
                    }
                    lastHighVolumeTime = Date.now();
                    lastSpeechTime = Date.now();
                } else if (wasSpeaking && isSilent) {
                    // Volume declined - user stopped speaking
                    if (volumeDeclineStartTime === null) {
                        volumeDeclineStartTime = Date.now();
                        console.log('[Poseidon] 🔇 Volume declined - starting silence timer');
                    }
                    
                    const silenceDuration = Date.now() - volumeDeclineStartTime;
                    const timeSinceLastSpeech = Date.now() - lastHighVolumeTime;
                    
                    // Process if silence has been sustained
                    if (silenceDuration >= MIN_VOLUME_DECLINE_DURATION && timeSinceLastSpeech >= MIN_VOLUME_DECLINE_DURATION) {
                        wasSpeaking = false;
                        speechDetected = false;
                        
                        // Check if we have a transcript to process
                        const currentTranscript = poseidonUserTranscript?.textContent?.trim() || pendingTranscript?.trim() || '';
                        
                        if (currentTranscript && currentTranscript.length > 0 && !transcriptProcessing) {
                            console.log('[Poseidon] 📊 Volume decline detected - processing transcript:', currentTranscript);
                            console.log('[Poseidon] Silence duration:', silenceDuration, 'ms, Time since speech:', timeSinceLastSpeech, 'ms');
                            
                            // Process the transcript
                            handlePoseidonTranscript(currentTranscript);
                            pendingTranscript = '';
                            volumeDeclineStartTime = null;
                        } else if (!transcriptProcessing) {
                            console.log('[Poseidon] Volume declined but no transcript available yet');
                        }
                    }
                } else if (!isSpeaking && !wasSpeaking) {
                    // Already silent, no action needed
                    volumeDeclineStartTime = null;
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

// Helper function to check if a transcript matches what Poseidon just spoke
function isTranscriptSelfSpeech(transcript) {
    // If we're currently speaking, ignore all transcripts
    if (isSpeaking) {
        console.log('[Poseidon] 🔇 Ignoring transcript - currently speaking:', transcript);
        return true;
    }
    
    // Check if we're within the time window where we should filter
    const timeSinceLastSpeech = Date.now() - lastSpokenTime;
    if (timeSinceLastSpeech > SPEECH_MATCH_WINDOW_MS) {
        return false; // Too much time has passed, treat as real user input
    }
    
    // Normalize both texts for comparison (lowercase, remove extra spaces, punctuation)
    const normalize = (text) => {
        return text.toLowerCase()
            .replace(/[^\w\s]/g, '') // Remove punctuation
            .replace(/\s+/g, ' ') // Normalize whitespace
            .trim();
    };
    
    const normalizedTranscript = normalize(transcript);
    const normalizedSpoken = normalize(lastSpokenText);
    
    // If either is empty, no match
    if (!normalizedTranscript || !normalizedSpoken) {
        return false;
    }
    
    // Check for exact match
    if (normalizedTranscript === normalizedSpoken) {
        console.log('[Poseidon] 🔇 Exact match detected - ignoring self-speech:', transcript.substring(0, 100));
        return true;
    }
    
    // Check if transcript is a substring of spoken text (common when speech is cut off)
    if (normalizedSpoken.includes(normalizedTranscript) && normalizedTranscript.length > 10) {
        console.log('[Poseidon] 🔇 Transcript is substring of spoken text - ignoring self-speech:', transcript.substring(0, 100));
        return true;
    }
    
    // Check if spoken text is a substring of transcript (common when recognition adds words)
    if (normalizedTranscript.includes(normalizedSpoken) && normalizedSpoken.length > 10) {
        console.log('[Poseidon] 🔇 Spoken text is substring of transcript - ignoring self-speech:', transcript.substring(0, 100));
        return true;
    }
    
    // Calculate similarity using simple word overlap
    const transcriptWords = new Set(normalizedTranscript.split(' ').filter(w => w.length > 2));
    const spokenWords = new Set(normalizedSpoken.split(' ').filter(w => w.length > 2));
    
    if (transcriptWords.size === 0 || spokenWords.size === 0) {
        return false;
    }
    
    // Count overlapping words
    let overlapCount = 0;
    for (const word of transcriptWords) {
        if (spokenWords.has(word)) {
            overlapCount++;
        }
    }
    
    // If more than 70% of words overlap, consider it a match
    const overlapRatio = overlapCount / Math.max(transcriptWords.size, spokenWords.size);
    if (overlapRatio > 0.7 && overlapCount >= 3) {
        console.log('[Poseidon] 🔇 High word overlap detected (' + Math.round(overlapRatio * 100) + '%) - ignoring self-speech:', transcript.substring(0, 100));
        return true;
    }
    
    return false;
}

// Voice command detection and handling (v3.0.0: Enhanced with parameters)
function detectVoiceCommand(transcript) {
    const lower = transcript.toLowerCase().trim();
    let params = {};
    
    // Wake words
    const wakeWords = ['hey poseidon', 'poseidon', 'wake up', 'activate', 'start listening'];
    for (const wake of wakeWords) {
        if (lower.includes(wake)) {
            const remaining = lower.replace(wake, '').trim();
            return { type: 'wake', remaining: remaining || null, params: null };
        }
    }
    
    // Version 3.0.0: Parameter-based commands
    // Speed command with value
    const speedMatch = lower.match(/\b(speed|faster|slower|talk (faster|slower))\s*(up|down|to)?\s*(\d+\.?\d*|slow|normal|fast)?/);
    if (speedMatch) {
        if (speedMatch[4]) {
            if (speedMatch[4] === 'slow') params.speed = 0.75;
            else if (speedMatch[4] === 'fast') params.speed = 1.5;
            else if (speedMatch[4] === 'normal') params.speed = 1.0;
            else params.speed = parseFloat(speedMatch[4]) || (lower.includes('faster') ? 1.5 : 0.75);
        } else {
            params.speed = lower.includes('faster') ? 1.5 : 0.75;
        }
        return { type: 'speed', remaining: null, params: params };
    }
    
    // Volume command with value
    const volumeMatch = lower.match(/\b(volume|louder|quieter|softer)\s*(up|down|to)?\s*(\d+\.?\d*|low|medium|high)?/);
    if (volumeMatch) {
        if (volumeMatch[3]) {
            if (volumeMatch[3] === 'low') params.volume = 0.5;
            else if (volumeMatch[3] === 'high') params.volume = 1.0;
            else if (volumeMatch[3] === 'medium') params.volume = 0.75;
            else params.volume = parseFloat(volumeMatch[3]) || (lower.includes('louder') ? 1.0 : 0.5);
        } else {
            params.volume = lower.includes('louder') ? 1.0 : 0.5;
        }
        return { type: 'volume', remaining: null, params: params };
    }
    
    // Language command (v3.x: Enhanced with new languages)
    const langMatch = lower.match(/\b(speak|use|change to|switch to|language)\s*(english|spanish|french|german|hindi|tamil|telugu|mandarin|chinese|italian|portuguese|japanese|korean)?/);
    if (langMatch) {
        const langMap = {
            'english': 'en-US', 'spanish': 'es-ES', 'french': 'fr-FR', 'german': 'de-DE',
            'hindi': 'hi-IN', 'tamil': 'ta-IN', 'telugu': 'te-IN', 'mandarin': 'zh-CN',
            'chinese': 'zh-CN', 'italian': 'it-IT', 'portuguese': 'pt-BR', 
            'japanese': 'ja-JP', 'korean': 'ko-KR'
        };
        if (langMatch[2] && langMap[langMatch[2].toLowerCase()]) {
            params.language = langMap[langMatch[2].toLowerCase()];
        }
        return { type: 'language', remaining: null, params: params };
    }
    
    // Settings command
    if (/\b(settings|configure|preferences|options)\b/.test(lower)) {
        return { type: 'settings', remaining: null, params: null };
    }
    
    // Basic command patterns
    if (/\b(pause|stop listening|hold on|wait|quiet|silence|shush)\b/.test(lower)) {
        return { type: 'pause', remaining: null, params: null };
    }
    if (/\b(resume|continue|keep going|go on|listen|start listening again)\b/.test(lower)) {
        return { type: 'resume', remaining: null, params: null };
    }
    if (/\b(stop|end|exit|close|shut down|that's enough|all done|finished)\b/.test(lower)) {
        return { type: 'stop', remaining: null, params: null };
    }
    if (/\b(repeat|say that again|what did you say|pardon|can you repeat|one more time)\b/.test(lower)) {
        return { type: 'repeat', remaining: null, params: null };
    }
    if (/\b(clear|reset|start over|forget|clear history|reset conversation)\b/.test(lower)) {
        return { type: 'clear', remaining: null, params: null };
    }
    if (/\b(help|what can you do|commands|assistance|how do i|what are|show me)\b/.test(lower)) {
        return { type: 'help', remaining: null, params: null };
    }
    
    return { type: 'none', remaining: null, params: null };
}

// Version 3.x: Mis-saying detection and correction
const misSayingCorrections = {
    'the': ['teh', 'da', 'de'],
    'to': ['two', 'too', 'tu'],
    'for': ['four', 'fore', 'fro'],
    'you': ['u', 'yu', 'ew'],
    'are': ['r', 'arr'],
    'your': ['ur', 'yore'],
    'their': ['there', 'they\'re'],
    'there': ['their', 'they\'re'],
    'they\'re': ['their', 'there'],
    'it\'s': ['its', 'itz'],
    'its': ['it\'s'],
    'can\'t': ['cant', 'can t', 'cannot'],
    'won\'t': ['wont', 'won t'],
    'don\'t': ['dont', 'don t'],
    'one': ['won', 'wan'],
    'two': ['to', 'too'],
    'four': ['for', 'fore'],
    'what': ['wut', 'wat'],
    'where': ['ware', 'wear'],
    'when': ['wen'],
    'why': ['y', 'wy'],
    'hello': ['hallo', 'helo'],
    'thanks': ['thx', 'thank'],
    'please': ['pls', 'pleas'],
    'sorry': ['sory', 'sore'],
    'okay': ['ok', 'o k'],
    'yes': ['yess', 'yas'],
    'no': ['know', 'noe']
};

function correctMisSayings(transcript) {
    const words = transcript.split(/\s+/);
    const correctedWords = [];
    
    for (let word of words) {
        const wordLower = word.toLowerCase().replace(/[.,!?;:]/g, '');
        let corrected = false;
        
        for (const [correct, misSayings] of Object.entries(misSayingCorrections)) {
            if (misSayings.includes(wordLower)) {
                // Preserve capitalization
                const isCapitalized = word[0] === word[0].toUpperCase();
                correctedWords.push(isCapitalized ? correct.charAt(0).toUpperCase() + correct.slice(1) : correct);
                corrected = true;
                break;
            }
        }
        
        if (!corrected) {
            correctedWords.push(word);
        }
    }
    
    return correctedWords.join(' ');
}

// Emotion detection
function detectEmotion(transcript) {
    const lower = transcript.toLowerCase();
    const emotions = {
        happy: /\b(great|awesome|wonderful|excellent|fantastic|amazing|love|happy|joy|thank you|thanks|appreciate|grateful)\b|!+/,
        excited: /\b(wow|yes|yeah|yay|woohoo|cool|neat|sweet|rad|epic)\b/,
        sad: /\b(sad|depressed|down|unhappy|disappointed|sorry|can't|unable|failed|wrong|bad)\b/,
        angry: /\b(angry|mad|furious|annoyed|frustrated|upset|stupid|idiot|hate|damn|hell)\b/,
        frustrated: /\b(why|how come|doesn't work|not working|broken|confused|don't understand|unclear)\b/,
        questioning: /\?+|\b(what|why|how|when|where|who|which|can you|will you|could you|would you)\b/,
        calm: /\b(okay|ok|sure|fine|alright|calm|relax|please|kindly|gently)\b/
    };
    
    let maxScore = 0;
    let detectedEmotion = 'neutral';
    
    for (const [emotion, pattern] of Object.entries(emotions)) {
        const matches = (lower.match(pattern) || []).length;
        if (matches > maxScore) {
            maxScore = matches;
            detectedEmotion = emotion;
        }
    }
    
    return detectedEmotion;
}

// Version 3.0.0: Helper functions for emotion-based adaptation
function getDominantEmotion(emotionHistory) {
    if (!emotionHistory || emotionHistory.length === 0) return 'neutral';
    const counts = {};
    emotionHistory.forEach(entry => {
        const emotion = typeof entry === 'string' ? entry : entry.emotion;
        counts[emotion] = (counts[emotion] || 0) + 1;
    });
    return Object.keys(counts).reduce((a, b) => counts[a] > counts[b] ? a : b, 'neutral');
}

function getEmotionBasedGuidance(emotion) {
    // Version 3.x: Enhanced with pitch variations for more human-like speech
    const guidanceMap = {
        'happy': { speed: 1.1, pitch: 1.15, tone: 'enthusiastic' },  // Higher pitch, faster
        'excited': { speed: 1.2, pitch: 1.2, tone: 'energetic' },   // Highest pitch, fastest
        'sad': { speed: 0.9, pitch: 0.85, tone: 'compassionate' },  // Lower pitch, slower
        'angry': { speed: 0.95, pitch: 0.9, tone: 'calm' },         // Lower pitch, slower (calming)
        'frustrated': { speed: 0.9, pitch: 0.88, tone: 'patient' }, // Lower pitch, slower
        'questioning': { speed: 1.0, pitch: 1.1, tone: 'clear' },   // Slightly higher (rising intonation)
        'calm': { speed: 1.0, pitch: 1.0, tone: 'gentle' },         // Neutral
        'neutral': { speed: 1.0, pitch: 1.0, tone: 'neutral' }
    };
    return guidanceMap[emotion] || guidanceMap['neutral'];
}

// Version 3.x: Add stress, pauses, and tone variations to make speech more human-like
function addSpeechStressAndTone(text, emotionGuidance) {
    let enhanced = text;
    
    // Add pauses after punctuation for more natural rhythm
    enhanced = enhanced.replace(/([.!?])\s+/g, '$1 ... ');  // Longer pause after sentences
    enhanced = enhanced.replace(/([,;:])\s+/g, '$1 .. ');   // Medium pause after commas
    
    // Add emphasis to important words (capitalized words, words with !, key phrases)
    const emphasisWords = /\b(IMPORTANT|CRITICAL|WARNING|NOTE|REMEMBER|CAREFUL|STOP|YES|NO|OKAY|SURE|EXACTLY|DEFINITELY)\b/gi;
    enhanced = enhanced.replace(emphasisWords, (match) => {
        // Add slight pause before and after for emphasis
        return '.. ' + match + ' ..';
    });
    
    // Adjust for question intonation (raise pitch indicator)
    if (enhanced.includes('?')) {
        // Questions naturally have rising intonation, handled by pitch
        // Add slight pause before question marks
        enhanced = enhanced.replace(/\s+([?])/g, ' ..$1');
    }
    
    // Exclamation emphasis (excited/urgent tone)
    if (enhanced.includes('!')) {
        // Add pause before exclamations for emphasis
        enhanced = enhanced.replace(/\s+([!])/g, ' ..$1');
    }
    
    // Add natural pauses in longer sentences (after ~15 words)
    const sentences = enhanced.split(/[.!?]+/);
    const processedSentences = sentences.map(sentence => {
        const words = sentence.trim().split(/\s+/);
        if (words.length > 15) {
            // Add pause in the middle
            const midPoint = Math.floor(words.length / 2);
            words.splice(midPoint, 0, '..');
            return words.join(' ');
        }
        return sentence;
    });
    enhanced = processedSentences.join('. ').replace(/\.\s*\./g, '.'); // Clean up double periods
    
    // Tone-specific adjustments
    if (emotionGuidance.tone === 'compassionate' || emotionGuidance.tone === 'patient') {
        // Slower, more deliberate pace - add more pauses
        enhanced = enhanced.replace(/\s+/g, ' ... ');  // Longer pauses between words
    } else if (emotionGuidance.tone === 'energetic' || emotionGuidance.tone === 'enthusiastic') {
        // Faster, more dynamic - fewer pauses but emphasize key words
        enhanced = enhanced.replace(/\.\.\.\s+/g, '. ');  // Shorter pauses
    }
    
    // Clean up excessive pauses
    enhanced = enhanced.replace(/(\.\s*){3,}/g, '... ');  // Max 3 dots for pause
    enhanced = enhanced.replace(/\s+/g, ' ');  // Normalize spaces
    
    return enhanced.trim();
}

// Version 3.0.0: Adaptive listening sensitivity
function adaptListeningSensitivity(levels) {
    if (!levels || levels.length < 10) return;
    
    const avgLevel = levels.reduce((a, b) => a + b, 0) / levels.length;
    const maxLevel = Math.max(...levels);
    
    // Adjust threshold based on environment
    if (avgLevel < 0.01) {
        // Very quiet environment - lower threshold
        adaptiveSensitivity = Math.max(0.005, adaptiveSensitivity * 0.9);
    } else if (avgLevel > 0.1) {
        // Noisy environment - raise threshold
        adaptiveSensitivity = Math.min(0.05, adaptiveSensitivity * 1.1);
    }
    
    // Update global threshold (if needed in future)
    console.log('[Poseidon] Adaptive sensitivity:', adaptiveSensitivity.toFixed(4), 'avg level:', avgLevel.toFixed(4));
}

// Version 3.0.0: Generate conversation summary
function generateConversationSummary() {
    const userMessages = emotionHistory.filter(e => e.role === 'user' || true).length;
    const emotions = emotionHistory.map(e => e.emotion || 'neutral');
    const emotionCounts = {};
    emotions.forEach(emo => {
        emotionCounts[emo] = (emotionCounts[emo] || 0) + 1;
    });
    
    const dominantEmotion = Object.keys(emotionCounts).reduce((a, b) => 
        emotionCounts[a] > emotionCounts[b] ? a : b, 'neutral');
    
    const summary = {
        timestamp: new Date().toISOString(),
        totalInteractions: emotionHistory.length,
        dominantEmotion: dominantEmotion,
        emotionDistribution: emotionCounts,
        sessionDuration: Date.now() - (window.poseidonSessionStart || Date.now()),
        settings: {
            speed: currentSpeechSpeed,
            volume: currentSpeechVolume,
            language: currentLanguage
        }
    };
    
    conversationSummaries.push(summary);
    if (conversationSummaries.length > 20) {
        conversationSummaries = conversationSummaries.slice(-20);
    }
    
    console.log('[Poseidon] Conversation summary generated:', summary);
    return summary;
}

// Handle voice commands (v3.0.0: Enhanced with parameters)
async function handleVoiceCommand(command) {
    console.log('[Poseidon] Voice command detected:', command.type, command.params);
    
    switch (command.type) {
        case 'pause':
            togglePoseidonPause();
            speakText('Paused. Say resume to continue.');
            break;
            
        case 'resume':
            if (poseidonPaused) {
                togglePoseidonPause();
                speakText('Resumed. I\'m listening.');
            }
            break;
            
        case 'stop':
            closePoseidonOverlay();
            speakText('Goodbye!');
            break;
            
        case 'repeat':
            if (lastAssistantResponse) {
                speakText(lastAssistantResponse);
            } else {
                speakText('I haven\'t said anything yet. Ask me something!');
            }
            break;
            
        case 'clear':
            if (poseidonUserTranscript) {
                poseidonUserTranscript.textContent = '';
            }
            if (poseidonAssistantTranscript) {
                poseidonAssistantTranscript.textContent = '';
            }
            lastAssistantResponse = '';
            emotionHistory = [];
            speakText('Conversation cleared.');
            break;
            
        case 'speed':
            if (command.params && command.params.speed !== undefined) {
                currentSpeechSpeed = Math.max(0.5, Math.min(2.0, command.params.speed));
                localStorage.setItem('poseidonSpeechSpeed', currentSpeechSpeed.toString());
                speakText(`Speech speed set to ${Math.round(currentSpeechSpeed * 100)}%`, currentSpeechSpeed);
            }
            break;
            
        case 'volume':
            if (command.params && command.params.volume !== undefined) {
                currentSpeechVolume = Math.max(0.0, Math.min(1.0, command.params.volume));
                localStorage.setItem('poseidonSpeechVolume', currentSpeechVolume.toString());
                speakText(`Volume set to ${Math.round(currentSpeechVolume * 100)}%`, currentSpeechSpeed, currentSpeechVolume);
            }
            break;
            
        case 'language':
            if (command.params && command.params.language) {
                currentLanguage = command.params.language;
                voiceSettings.accent = currentLanguage;
                localStorage.setItem('poseidonAccent', currentLanguage);
                if (recognition) {
                    recognition.lang = currentLanguage;
                }
                updateVoiceSelection();
                const langNames = {
                    'en-US': 'English', 'es-ES': 'Spanish', 'fr-FR': 'French', 'de-DE': 'German',
                    'hi-IN': 'Hindi', 'ta-IN': 'Tamil', 'te-IN': 'Telugu', 'zh-CN': 'Mandarin',
                    'it-IT': 'Italian', 'pt-BR': 'Portuguese', 'ja-JP': 'Japanese',
                    'ko-KR': 'Korean'
                };
                speakText(`Language changed to ${langNames[currentLanguage] || currentLanguage}`);
            }
            break;
            
        case 'settings':
            const settingsText = `Current settings: Speed ${Math.round(currentSpeechSpeed * 100)}%, Volume ${Math.round(currentSpeechVolume * 100)}%, Language ${currentLanguage}. Say "faster" or "slower" to adjust speed, "louder" or "quieter" for volume, or "speak English" to change language.`;
            speakText(settingsText);
            break;
            
        case 'help':
            const helpText = `Voice Commands: "pause" to pause, "resume" to continue, "stop" to end, "repeat" for last response, "clear" to reset. New in v3.0: "faster" or "slower" for speed, "louder" or "quieter" for volume, "speak English/Spanish/French" to change language, "settings" for current settings.`;
            speakText(helpText);
            break;
            
        case 'wake':
            if (command.remaining) {
                // Process the remaining text as a normal query
                return false; // Don't handle as command, process as normal
            }
            speakText('I\'m listening. How can I help you?');
            break;
    }
    
    return true; // Command was handled
}

// Language detection function - detects language from text
function detectLanguageFromText(text) {
    if (!text || text.trim().length === 0) {
        return voiceSettings.accent || 'en-US';
    }
    
    // Hindi (Devanagari script) - Unicode range: 0900-097F
    if (/[\u0900-\u097F]/.test(text)) {
        console.log('[Poseidon] Detected Hindi (Devanagari script)');
        return 'hi-IN';
    }
    
    // Tamil - Unicode range: 0B80-0BFF
    if (/[\u0B80-\u0BFF]/.test(text)) {
        console.log('[Poseidon] Detected Tamil');
        return 'ta-IN';
    }
    
    // Telugu - Unicode range: 0C00-0C7F
    if (/[\u0C00-\u0C7F]/.test(text)) {
        console.log('[Poseidon] Detected Telugu');
        return 'te-IN';
    }
    
    // Chinese/Mandarin - Unicode ranges: 4E00-9FFF (CJK Unified), 3400-4DBF (Extension A)
    if (/[\u4E00-\u9FFF\u3400-\u4DBF]/.test(text)) {
        console.log('[Poseidon] Detected Chinese/Mandarin');
        return 'zh-CN';
    }
    
    // Japanese - Unicode ranges: 3040-309F (Hiragana), 30A0-30FF (Katakana), 4E00-9FFF (Kanji)
    if (/[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]/.test(text)) {
        console.log('[Poseidon] Detected Japanese');
        return 'ja-JP';
    }
    
    // Korean - Unicode range: AC00-D7AF (Hangul Syllables), 1100-11FF (Hangul Jamo)
    if (/[\uAC00-\uD7AF\u1100-\u11FF]/.test(text)) {
        console.log('[Poseidon] Detected Korean');
        return 'ko-KR';
    }
    
    // Spanish - detect common Spanish words/patterns
    const spanishWords = ['hola', 'gracias', 'por favor', 'adiós', 'sí', 'no', 'qué', 'cómo', 'dónde', 'cuándo'];
    const textLower = text.toLowerCase();
    if (spanishWords.some(word => textLower.includes(word))) {
        console.log('[Poseidon] Detected Spanish');
        return 'es-ES';
    }
    
    // French - detect common French words/patterns
    const frenchWords = ['bonjour', 'merci', 's\'il vous plaît', 'au revoir', 'oui', 'non', 'comment', 'où', 'quand'];
    if (frenchWords.some(word => textLower.includes(word))) {
        console.log('[Poseidon] Detected French');
        return 'fr-FR';
    }
    
    // German - detect common German words
    const germanWords = ['hallo', 'danke', 'bitte', 'auf wiedersehen', 'ja', 'nein', 'wie', 'wo', 'wann'];
    if (germanWords.some(word => textLower.includes(word))) {
        console.log('[Poseidon] Detected German');
        return 'de-DE';
    }
    
    // Default to current language setting or English
    return voiceSettings.accent || currentLanguage || 'en-US';
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
    let trimmed = transcript.trim();
    if (trimmed.length < 2) {
        console.log('[Poseidon] Transcript too short, skipping:', trimmed);
        return;
    }
    
    // Version 3.x: Correct mis-sayings
    trimmed = correctMisSayings(trimmed);
    console.log('[Poseidon] After mis-saying correction:', trimmed);
    
    // Check if this transcript matches what Poseidon just spoke (self-hearing prevention)
    if (isTranscriptSelfSpeech(trimmed)) {
        console.log('[Poseidon] 🔇 Filtered out self-speech transcript:', trimmed.substring(0, 100));
        return;
    }
    
    // Detect voice command
    const command = detectVoiceCommand(trimmed);
    
    // If it's a wake word with remaining text, use the remaining text
    let textToProcess = trimmed;
    if (command.type === 'wake' && command.remaining) {
        textToProcess = command.remaining;
    }
    
    // Handle voice commands (except wake with remaining text)
    if (command.type !== 'none' && (!command.remaining || command.type !== 'wake')) {
        const handled = await handleVoiceCommand(command);
        if (handled) {
            transcriptProcessing = false;
            return; // Command was handled, don't process as normal query
        }
    }
    
    // Detect emotion (v3.0.0: Track history)
    const emotion = detectEmotion(textToProcess);
    console.log('[Poseidon] Detected emotion:', emotion);
    
    // Version 3.0.0: Track emotion history for adaptation
    emotionHistory.push({
        emotion: emotion,
        timestamp: Date.now()
    });
    if (emotionHistory.length > 50) {
        emotionHistory = emotionHistory.slice(-50);
    }
    
    // Update UI with emotion indicator (if element exists)
    if (poseidonUserTranscript) {
        const emotionEmoji = {
            happy: '😊',
            excited: '🎉',
            sad: '😢',
            angry: '😠',
            frustrated: '😤',
            questioning: '❓',
            calm: '😌',
            neutral: ''
        };
        const emoji = emotionEmoji[emotion] || '';
        poseidonUserTranscript.textContent = emoji ? `${emoji} ${textToProcess}` : textToProcess;
    }
    
    console.log('[Poseidon] Processing transcript:', textToProcess);
    transcriptProcessing = true;
    recognitionState = 'processing';
    
    // Don't stop recognition in continuous mode - just mark as processing
    clearTimeout(silenceTimeout);
    clearTimeout(recognitionRestartTimeout);
    
    // Update status to "Thinking" - we're analyzing the request
    updatePoseidonStatus('thinking', 'Thinking...');
    
    // Detect language from transcript and update current language
    const detectedLanguage = detectLanguageFromText(textToProcess);
    if (detectedLanguage && detectedLanguage !== currentLanguage) {
        console.log('[Poseidon] Language detected from transcript:', detectedLanguage, '(was:', currentLanguage, ')');
        currentLanguage = detectedLanguage;
        // Update voice settings to match detected language for speech synthesis
        voiceSettings.accent = detectedLanguage;
        // Update voice selection to get the right voice for this language
        updateVoiceSelection();
    }
    
    // Send to chat API
    try {
        const requestBody = {
            message: textToProcess, // Use processed text (after wake word removal)
            chat_id: currentChatId,
            task: 'text_generation',
            think_deeper: thinkDeeperMode,
            model: currentModel,
            tone: getEffectiveTone(),
            system_mode: systemMode,  // Include system mode (latest/stable)
            response_language: detectedLanguage,  // Tell backend to respond in this language
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
                requestMethod: 'POST',
                isElectron: window.electronAPI !== undefined,
                currentUrl: window.location.href
            });
            
            // Check if we're in Electron and retry with delay for server startup
            const isElectron = window.electronAPI !== undefined;
            if (isElectron && (fetchErr.message.includes('Failed to fetch') || fetchErr.message.includes('NetworkError') || fetchErr.message.includes('ECONNREFUSED') || fetchErr.name === 'TypeError')) {
                // For Electron, use full URL instead of relative path
                // Electron's fetch sometimes has issues with relative URLs
                const fullUrl = window.location.origin + '/api/chat';
                console.log('[Poseidon] Electron: Server connection failed, retrying with full URL:', fullUrl);
                await new Promise(resolve => setTimeout(resolve, 500)); // Brief delay
                try {
                    // Use AbortController for better timeout handling in Electron
                    const controller = new AbortController();
                    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
                    
                    response = await fetch(fullUrl, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify(requestBody),
                        signal: controller.signal
                    });
                    clearTimeout(timeoutId);
                    
                    if (response.ok) {
                        console.log('[Poseidon] Electron retry with full URL successful');
                    } else {
                        throw new Error(`Server returned error: ${response.status} ${response.statusText}`);
                    }
                } catch (retryErr) {
                    console.error('[Poseidon] Electron retry also failed:', retryErr);
                    // Check if it's a connection error
                    if (retryErr.name === 'AbortError' || retryErr.message.includes('Failed to fetch') || retryErr.message.includes('NetworkError')) {
                        throw new Error(`Cannot connect to server. Please ensure the Flask server is running (python3 chatbot/app.py) on port 5000.`);
                    }
                    throw new Error(`Network error: ${retryErr.message}. Please check if the Flask server is running.`);
                }
            } else if (isElectron) {
                throw new Error(`Network error in Electron app: ${fetchErr.message}. Please check if the Flask server is running.`);
            } else {
                // Browser: retry once with delay
                if (fetchErr.message.includes('Failed to fetch') || fetchErr.message.includes('NetworkError') || fetchErr.name === 'TypeError') {
                    console.log('[Poseidon] Browser network error detected, retrying in 1 second...');
                    await new Promise(resolve => setTimeout(resolve, 1000));
                    try {
                        response = await fetch('/api/chat', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify(requestBody)
                        });
                        if (response.ok) {
                            console.log('[Poseidon] Browser retry successful');
                        } else {
                            throw new Error(`Server returned error: ${response.status}`);
                        }
                    } catch (retryErr) {
                        console.error('[Poseidon] Browser retry also failed:', retryErr);
                        throw new Error(`Cannot connect to server. Please ensure the server is started (python3 chatbot/app.py) and running on port 5000.`);
                    }
                } else {
                    throw new Error(`Network error: ${fetchErr.message}`);
                }
            }
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
        
        // Status is already "Thinking" - now we have the response
        // Update to show we're preparing to speak
        updatePoseidonStatus('thinking', 'Got response, preparing to speak...');
        
        // Add messages to UI
        try {
            addMessageToUI('user', textToProcess); // Use processed text
            console.log('[Poseidon] Added user message to UI');
        } catch (uiErr) {
            console.error('[Poseidon] ERROR adding user message to UI:', uiErr);
        }
        
        let responseText = data.response || 'No response received';
        console.log('[Poseidon] Response text:', {
            length: responseText.length,
            preview: responseText.substring(0, 100)
        });
        
        // Check if we need to translate the response to match the detected language
        // Only translate if currentLanguage is set and not English
        const needsTranslation = currentLanguage && 
                                 currentLanguage !== 'en-US' && 
                                 currentLanguage !== 'en-GB' && 
                                 currentLanguage !== 'en-AU' && 
                                 currentLanguage !== 'en-IN';
        
        if (needsTranslation) {
            console.log('[Poseidon] Translating response to:', currentLanguage);
            try {
                const translateResponse = await fetch('/api/translate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        text: responseText,
                        target_language: currentLanguage
                    })
                });
                
                if (translateResponse.ok) {
                    const translateData = await translateResponse.json();
                    if (translateData.translated_text) {
                        console.log('[Poseidon] Translation successful:', {
                            original: responseText.substring(0, 50) + '...',
                            translated: translateData.translated_text.substring(0, 50) + '...'
                        });
                        responseText = translateData.translated_text;
                    } else {
                        console.warn('[Poseidon] Translation returned no translated_text, using original');
                    }
                } else {
                    console.warn('[Poseidon] Translation failed, using original response:', translateResponse.status);
                }
            } catch (translateErr) {
                console.error('[Poseidon] Error translating response:', translateErr);
                // Continue with original response if translation fails
            }
        }
        
        // Store response for repeat command
        lastAssistantResponse = responseText;
        
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
        
        // Speak the response - this will update status to "Speaking"
        try {
            speakText(responseText);
            // Start 3D animation lip-sync (v3.x)
            if (poseidon3D && typeof poseidon3D.speak === 'function') {
                poseidon3D.speak(responseText, responseText.length * 0.1);
            }
            console.log('[Poseidon] Started speaking response');
        } catch (speakErr) {
            console.error('[Poseidon] ERROR speaking response:', speakErr);
            console.error('[Poseidon] Speak error details:', {
                name: speakErr?.name,
                message: speakErr?.message,
                responseLength: responseText.length
            });
            // If speaking fails, go back to listening
            updatePoseidonStatus('listening', 'Listening...');
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
        
        // Provide more helpful error messages
        let errorMsg = 'Sorry, I encountered an error processing your request.';
        const isElectron = window.electronAPI !== undefined;
        
        if (error.message) {
            if (error.message.includes('Network error') || error.message.includes('Failed to fetch')) {
                if (isElectron) {
                    errorMsg = 'Server not ready. Please wait a moment and try again. If the problem persists, the Flask server may not be running.';
                } else {
                    errorMsg = 'Network error. Please check your connection and try again.';
                }
            } else if (error.message.includes('Server not ready')) {
                errorMsg = error.message; // Use the more specific message we set earlier
            } else {
                errorMsg = `Error: ${error.message}`;
            }
        }
        
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
        
        // CRITICAL: Verify and fix configuration in onstart
        // Some browsers reset properties when recognition actually starts
        if (recognition.continuous !== true || recognition.interimResults !== true) {
            console.warn('[Poseidon] Configuration reset detected in onstart, fixing...', {
                continuous: recognition.continuous,
                interimResults: recognition.interimResults,
                lang: recognition.lang
            });
            recognition.continuous = true;
            recognition.interimResults = true;
            // MAJOR ENHANCEMENT: Explicit Hindi recognition language
            if (voiceSettings.accent === 'hi-IN' || currentLanguage === 'hi-IN') {
                recognition.lang = 'hi-IN';
                console.log('[Poseidon Hindi] Recognition language explicitly set to Hindi (hi-IN) in onstart');
            } else {
                // MAJOR ENHANCEMENT: Explicit Hindi recognition language
                if (voiceSettings.accent === 'hi-IN' || currentLanguage === 'hi-IN') {
                    recognition.lang = 'hi-IN';
                    console.log('[Poseidon Hindi] Recognition language explicitly set to Hindi (hi-IN)');
                } else {
                    recognition.lang = voiceSettings.accent || currentLanguage || 'en-US';
                }
            }
            recognition.maxAlternatives = 1;
            console.log('[Poseidon] Configuration fixed in onstart');
        }
        
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
        console.log('[Poseidon] ===== onresult FIRED =====');
        console.log('[Poseidon] Event details:', {
            resultIndex: event.resultIndex,
            resultsLength: event.results.length,
            hasResults: event.results && event.results.length > 0
        });
        
        // Update last speech time - user is speaking
        lastSpeechTime = Date.now();
        speechDetected = true;
        consecutiveNoSpeechCount = 0;
        clearTimeout(silenceTimeout);
        
        // Process all results
        let finalTranscript = '';
        let interimTranscript = '';
        let hasFinal = false;
        
        if (!event.results || event.results.length === 0) {
            console.warn('[Poseidon] WARNING: onresult fired but no results in event!');
            return;
        }
        
        for (let i = event.resultIndex; i < event.results.length; i++) {
            const result = event.results[i];
            if (!result || !result[0]) {
                console.warn(`[Poseidon] WARNING: Result ${i} is invalid:`, result);
                continue;
            }
            
            let transcript = result[0].transcript || '';
            const isFinal = result.isFinal || false;
            const confidence = result[0].confidence || 0;
            
            // MAJOR ENHANCEMENT: Hindi-specific transcript processing
            if (voiceSettings.accent === 'hi-IN' || currentLanguage === 'hi-IN' || recognition.lang === 'hi-IN') {
                // Clean and normalize Hindi transcript
                transcript = transcript.trim();
                
                // Handle common Hindi recognition issues
                // Fix spacing issues in Hindi text
                transcript = transcript.replace(/\s+/g, ' ').trim();
                
                // Preserve Devanagari script characters properly
                // Ensure proper spacing around punctuation
                transcript = transcript
                    .replace(/\s+([।,।])/g, '$1') // Remove space before punctuation
                    .replace(/([।,।])\s+/g, '$1 ') // Add space after punctuation
                    .trim();
                
                console.log(`[Poseidon Hindi] Processed Hindi transcript: "${transcript}"`);
            }
            
            // DEBUG: Log what Poseidon hears
            console.log(`🎤 [Poseidon HEARD] Result ${i}: isFinal=${isFinal}, transcript="${transcript}", confidence=${confidence}, length=${transcript.length}`);
            if (transcript.trim().length > 0) {
                console.log(`🎤 [Poseidon HEARD] "${transcript}"`);
            }
            
            console.log(`[Poseidon] Result ${i}: isFinal=${isFinal}, transcript="${transcript}", confidence=${confidence}, length=${transcript.length}`);
            
            if (isFinal) {
                finalTranscript += transcript + ' ';
                hasFinal = true;
                console.log(`[Poseidon] Added to final transcript: "${transcript}"`);
            } else {
                interimTranscript += transcript;
                console.log(`[Poseidon] Added to interim transcript: "${transcript}"`);
            }
        }
        
        // Combine transcripts
        const combinedFinal = finalTranscript.trim();
        const combinedInterim = interimTranscript.trim();
        const displayText = combinedFinal || combinedInterim;
        
        // DEBUG: Log what Poseidon hears (clear summary)
        if (combinedFinal.length > 0) {
            console.log(`🎤 [Poseidon HEARD - FINAL] "${combinedFinal}"`);
        }
        if (combinedInterim.length > 0 && combinedFinal.length === 0) {
            console.log(`🎤 [Poseidon HEARD - INTERIM] "${combinedInterim}"`);
        }
        
        console.log('[Poseidon] ===== TRANSCRIPT SUMMARY =====');
        console.log('[Poseidon] Final transcript:', combinedFinal, `(${combinedFinal.length} chars)`);
        console.log('[Poseidon] Interim transcript:', combinedInterim, `(${combinedInterim.length} chars)`);
        console.log('[Poseidon] Display text:', displayText, `(${displayText.length} chars)`);
        console.log('[Poseidon] Has final:', hasFinal);
        
        // Update UI with current transcript
        if (poseidonUserTranscript) {
            poseidonUserTranscript.textContent = displayText;
            console.log('[Poseidon] Updated UI transcript display');
        } else {
            console.warn('[Poseidon] WARNING: poseidonUserTranscript element not found!');
        }
        
        // Store pending transcript
        if (displayText && displayText.length > 0) {
            pendingTranscript = displayText;
            console.log('[Poseidon] Stored pending transcript:', pendingTranscript);
        }
        
        // If we have a final transcript, process it immediately
        if (hasFinal && combinedFinal.length > 0) {
            console.log('[Poseidon] ===== PROCESSING FINAL TRANSCRIPT =====');
            console.log('[Poseidon] Final transcript to process:', combinedFinal);
            console.log('[Poseidon] Transcript processing flag:', transcriptProcessing);
            console.log('[Poseidon] Poseidon active:', poseidonActive);
            
            // Process immediately - don't delay
            if (!transcriptProcessing && poseidonActive) {
                console.log('[Poseidon] Calling handlePoseidonTranscript immediately');
                handlePoseidonTranscript(combinedFinal);
                pendingTranscript = '';
            } else {
                console.warn('[Poseidon] Cannot process - transcriptProcessing:', transcriptProcessing, 'poseidonActive:', poseidonActive);
                // Store for later processing
                pendingTranscript = combinedFinal;
            }
        } else if (combinedInterim.length > 0) {
            // We have interim results but no final yet
            console.log('[Poseidon] Interim results only - setting up silence timeout');
            console.log('[Poseidon] Interim transcript:', combinedInterim, 'length:', combinedInterim.length);
            
            // If interim is substantial (more than a few words), process it after a shorter timeout
            const wordCount = combinedInterim.split(/\s+/).filter(w => w.length > 0).length;
            console.log('[Poseidon] Interim word count:', wordCount);
            
            if (wordCount >= 3) {
                // Substantial interim - process after shorter timeout
                console.log('[Poseidon] Substantial interim detected, will process after shorter timeout');
                clearTimeout(silenceTimeout);
                silenceTimeout = setTimeout(() => {
                    if (poseidonActive && !poseidonPaused && !transcriptProcessing) {
                        const currentInterim = combinedInterim;
                        if (currentInterim && currentInterim.length > 0) {
                            console.log('[Poseidon] Processing substantial interim after timeout:', currentInterim);
                            handlePoseidonTranscript(currentInterim);
                            pendingTranscript = '';
                        }
                    }
                }, 1500); // Shorter timeout for substantial interim
            } else {
                // Set up normal timeout to process interim if no final comes
                resetSilenceTimeout();
            }
        } else {
            console.warn('[Poseidon] WARNING: No final or interim transcript to process!');
            console.warn('[Poseidon] This might indicate speech recognition is not detecting speech');
        }
        
        console.log('[Poseidon] ===== onresult COMPLETE =====');
    };
    
    recognition.onspeechstart = () => {
        console.log('[Poseidon] ===== SPEECH START DETECTED =====');
        speechDetected = true;
        lastSpeechTime = Date.now();
        consecutiveNoSpeechCount = 0;
        clearTimeout(silenceTimeout);
        updatePoseidonStatus('listening', 'Listening... (speech detected)');
    };
    
    recognition.onspeechend = () => {
        console.log('[Poseidon] ===== SPEECH END DETECTED =====');
        console.log('[Poseidon] Pending transcript:', pendingTranscript);
        console.log('[Poseidon] Transcript processing:', transcriptProcessing);
        
        // Reset speech detected flag and status after a short delay
        // This allows time for final results to come in
        setTimeout(() => {
            speechDetected = false;
            
            // Reset status back to normal "Listening..." if we're not processing
            // If processing, status will be updated by handlePoseidonTranscript to "Thinking..."
            if (!transcriptProcessing && poseidonActive && !poseidonPaused && recognitionState !== 'processing') {
                updatePoseidonStatus('listening', 'Listening...');
                console.log('[Poseidon] Status reset to normal listening after speech end');
            }
            
            const currentPending = pendingTranscript?.trim() || '';
            console.log('[Poseidon] Checking pending transcript after speech end:', currentPending);
            
            if (currentPending.length > 0 && !transcriptProcessing && poseidonActive) {
                console.log('[Poseidon] Processing pending transcript after speech end:', currentPending);
                handlePoseidonTranscript(currentPending);
                pendingTranscript = '';
            } else {
                console.log('[Poseidon] Not processing - pending:', currentPending.length, 'processing:', transcriptProcessing, 'active:', poseidonActive);
            }
        }, 800); // Delay to allow final results
    };
    
    recognition.onsoundstart = () => {
        console.log('[Poseidon] ===== SOUND START DETECTED =====');
        speechDetected = true;
        lastSpeechTime = Date.now();
        updatePoseidonStatus('listening', 'Listening... (sound detected)');
    };
    
    recognition.onsoundend = () => {
        console.log('[Poseidon] ===== SOUND END DETECTED =====');
        // Reset status after sound ends
        setTimeout(() => {
            speechDetected = false;
            if (!transcriptProcessing && poseidonActive && !poseidonPaused && recognitionState !== 'processing') {
                updatePoseidonStatus('listening', 'Listening...');
            }
            
            // Check if we have pending transcript to process
            const currentPending = pendingTranscript?.trim() || '';
            if (currentPending.length > 0 && !transcriptProcessing && poseidonActive) {
                console.log('[Poseidon] Processing pending transcript after sound end:', currentPending);
                handlePoseidonTranscript(currentPending);
                pendingTranscript = '';
            }
        }, 600);
    };
    
    recognition.onaudiostart = () => {
        console.log('[Poseidon] ===== AUDIO INPUT STARTED =====');
        console.log('[Poseidon] Microphone is now receiving audio');
    };
    
    recognition.onaudioend = () => {
        console.log('[Poseidon] ===== AUDIO INPUT ENDED =====');
        console.log('[Poseidon] Microphone input stopped');
    };
    
    recognition.onnomatch = () => {
        console.log('[Poseidon] ===== NO MATCH DETECTED =====');
        console.log('[Poseidon] Consecutive no-match count:', consecutiveNoSpeechCount);
        consecutiveNoSpeechCount++;
        
        // If we have pending transcript, process it
        const currentPending = pendingTranscript?.trim() || '';
        if (currentPending.length > 0 && !transcriptProcessing) {
            console.log('[Poseidon] Processing pending transcript on nomatch:', currentPending);
            handlePoseidonTranscript(currentPending);
            pendingTranscript = '';
        } else if (consecutiveNoSpeechCount >= MAX_NO_SPEECH_COUNT) {
            console.log('[Poseidon] Too many no-match events, restarting recognition');
            restartRecognition();
        } else {
            console.log('[Poseidon] No pending transcript to process, continuing to listen');
        }
    };
    
    function resetSilenceTimeout() {
        clearTimeout(silenceTimeout);
        silenceTimeout = setTimeout(() => {
            console.log('[Poseidon] ===== SILENCE TIMEOUT TRIGGERED =====');
            console.log('[Poseidon] State check - active:', poseidonActive, 'paused:', poseidonPaused, 'processing:', transcriptProcessing);
            
            if (poseidonActive && !poseidonPaused && !transcriptProcessing) {
                const uiTranscript = poseidonUserTranscript?.textContent?.trim() || '';
                const pending = pendingTranscript?.trim() || '';
                const currentTranscript = uiTranscript || pending;
                
                console.log('[Poseidon] Available transcripts - UI:', uiTranscript, 'Pending:', pending, 'Using:', currentTranscript);
                
                if (currentTranscript && currentTranscript.length > 0) {
                    console.log('[Poseidon] Processing transcript after silence timeout:', currentTranscript);
                    handlePoseidonTranscript(currentTranscript);
                    pendingTranscript = '';
                } else {
                    console.log('[Poseidon] Silence timeout - no transcript to process');
                    console.log('[Poseidon] This might mean no speech was detected');
                }
            } else {
                console.log('[Poseidon] Silence timeout ignored - not active/paused or already processing');
            }
        }, SILENCE_TIMEOUT_MS);
        console.log('[Poseidon] Silence timeout set for', SILENCE_TIMEOUT_MS, 'ms');
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
            
            // CRITICAL: Check circuit breaker before restarting on network errors
            // NOTE: Circuit breaker should NOT trigger on network errors in Electron app
            // Network errors in Electron are often transient and not related to speech recognition service
            const isElectron = window.electronAPI !== undefined;
            
            if (serviceNotAllowedDisabled && !isElectron) {
                // Only apply circuit breaker to network errors in browser, not Electron
                console.warn('[Poseidon] Circuit breaker active - not restarting on network error');
                errorMsg = 'Network error. Speech recognition service is temporarily unavailable.';
                shouldRestart = false;
                shouldSpeak = true;
            } else if (!isElectron) {
                // Track network errors for circuit breaker (browser only)
                const now = Date.now();
                rapidErrorTimes.push(now);
                rapidErrorTimes = rapidErrorTimes.filter(time => now - time < RAPID_ERROR_WINDOW_MS);
                
                // If too many network errors, trigger circuit breaker (browser only)
                if (rapidErrorTimes.length >= MAX_RAPID_ERRORS) {
                    console.error(`[Poseidon] 🛑 CIRCUIT BREAKER TRIGGERED: ${rapidErrorTimes.length} network errors in ${RAPID_ERROR_WINDOW_MS}ms`);
                    serviceNotAllowedDisabled = true;
                    errorMsg = 'Multiple network errors detected. Speech recognition service is temporarily unavailable. Please close and reopen Poseidon.';
                    shouldRestart = false;
                    shouldSpeak = true;
                } else {
                    errorMsg = 'Network error. Retrying...';
                    shouldRestart = true;
                }
            } else {
                // Electron: Don't trigger circuit breaker on network errors, just retry
                console.log('[Poseidon] Electron: Network error detected, will retry (circuit breaker disabled for Electron)');
                errorMsg = 'Network error. Retrying...';
                shouldRestart = true;
            }
        } else if (event.error === 'aborted') {
            // Recognition was stopped, don't show error
            console.log('[Poseidon] Recognition aborted (normal operation)');
            return;
        } else if (event.error === 'audio-capture') {
            console.error('[Poseidon] ERROR: No microphone found');
            errorMsg = 'No microphone found. Please connect a microphone.';
        } else if (event.error === 'service-not-allowed') {
            console.error('[Poseidon] ERROR: service-not-allowed - Speech recognition service permission check failed');
            
            const isSafari = /Safari/.test(navigator.userAgent) && !/Chrome/.test(navigator.userAgent);
            
            // Safari-specific: Handle immediately - don't retry
            if (isSafari) {
                console.error('[Poseidon] Safari service-not-allowed error - diagnostic info:', {
                    hasWebkitSpeechRecognition: 'webkitSpeechRecognition' in window,
                    hasSpeechRecognition: 'SpeechRecognition' in window,
                    isSecureContext: window.isSecureContext,
                    protocol: location.protocol,
                    hostname: location.hostname,
                    recognitionExists: !!recognition,
                    recognitionContinuous: recognition?.continuous,
                    recognitionLang: recognition?.lang
                });
                
                // Safari: Show message immediately - don't retry
                console.error('[Poseidon] Safari: Showing Safari-specific error message immediately');
                errorMsg = '⚠️ Safari Speech Recognition Limitation\n\n' +
                          'Safari has very limited and unreliable support for speech recognition.\n\n' +
                          'The Web Speech API in Safari is experimental and may not work on your system.\n\n' +
                          'For the best experience, please use:\n' +
                          '• Chrome (recommended - full support)\n' +
                          '• Edge (full support)\n\n' +
                          'If you must use Safari, try:\n' +
                          '1. Safari > Settings > Websites > Microphone - Allow for this site\n' +
                          '2. Ensure you\'re using HTTPS (not HTTP)\n' +
                          '3. Use Safari 14.1 or later\n' +
                          '4. Speech recognition may still not work due to Safari limitations\n\n' +
                          'Unfortunately, Safari\'s speech recognition support is unreliable and may not work at all.';
                
                updatePoseidonStatus('ready', 'Safari Limited Support');
                if (poseidonAssistantTranscript) {
                    poseidonAssistantTranscript.textContent = errorMsg;
                }
                
                // Try to speak the message
                try {
                    speakText('Safari speech recognition is not available. Please use Chrome or Edge for better compatibility.');
                } catch (speakErr) {
                    console.warn('[Poseidon] Could not speak Safari error message:', speakErr);
                }
                
                shouldSpeak = false; // Already spoke
                shouldRestart = false;
                serviceNotAllowedDisabled = true; // Disable retries for Safari
                return; // Exit immediately for Safari
            }
            
            const now = Date.now();
            const timeSinceLastError = now - lastServiceNotAllowedTime;
            
            // CIRCUIT BREAKER: Track rapid errors to prevent infinite loops
            rapidErrorTimes.push(now);
            // Remove errors older than the window
            rapidErrorTimes = rapidErrorTimes.filter(time => now - time < RAPID_ERROR_WINDOW_MS);
            
            // If we're getting too many errors too quickly, disable retries
            if (rapidErrorTimes.length >= MAX_RAPID_ERRORS) {
                if (!serviceNotAllowedDisabled) {
                    console.error(`[Poseidon] 🛑 CIRCUIT BREAKER TRIGGERED: ${rapidErrorTimes.length} errors in ${RAPID_ERROR_WINDOW_MS}ms`);
                    console.error('[Poseidon] Stopping all retry attempts to prevent infinite loop');
                    serviceNotAllowedDisabled = true;
                    
                    // Show user-friendly error with helpful guidance
                    updatePoseidonStatus('ready', 'Service Unavailable');
                    if (poseidonAssistantTranscript) {
                        const isChrome = /Chrome/.test(navigator.userAgent) && /Google Inc/.test(navigator.vendor);
                        const isEdge = /Edg/.test(navigator.userAgent);
                        const isSafariCheck = /Safari/.test(navigator.userAgent) && !/Chrome/.test(navigator.userAgent);
                        
                        let errorMsg = 'Speech recognition service is not available.\n\n';
                        
                        if (isChrome || isEdge) {
                            errorMsg += 'For Chrome/Edge:\n';
                            errorMsg += '1. Click the lock icon (🔒) in the address bar\n';
                            errorMsg += '2. Allow microphone access\n';
                            errorMsg += '3. Make sure you\'re using HTTPS or localhost\n';
                            errorMsg += '4. Try refreshing the page\n\n';
                            errorMsg += 'If it still doesn\'t work, your browser may not support speech recognition.';
                        } else if (isSafariCheck) {
                            errorMsg = '⚠️ Safari Speech Recognition Limitation\n\n';
                            errorMsg += 'Safari has very limited and unreliable support for speech recognition.\n\n';
                            errorMsg += 'The Web Speech API in Safari is experimental and may not work on your system.\n\n';
                            errorMsg += 'For the best experience, please use:\n';
                            errorMsg += '• Chrome (recommended - full support)\n';
                            errorMsg += '• Edge (full support)\n\n';
                            errorMsg += 'If you must use Safari, try:\n';
                            errorMsg += '1. Safari > Settings > Websites > Microphone - Allow for this site\n';
                            errorMsg += '2. Ensure you\'re using HTTPS (not HTTP)\n';
                            errorMsg += '3. Use Safari 14.1 or later\n';
                            errorMsg += '4. Speech recognition may still not work due to Safari limitations\n\n';
                            errorMsg += 'Unfortunately, Safari\'s speech recognition support is unreliable and may not work at all.';
                        } else {
                            errorMsg += 'Please:\n';
                            errorMsg += '1. Check browser microphone permissions\n';
                            errorMsg += '2. Ensure you\'re using HTTPS or localhost\n';
                            errorMsg += '3. Refresh the page and try again\n\n';
                            errorMsg += 'Note: Speech recognition requires Chrome, Edge, or Safari.';
                        }
                        
                        poseidonAssistantTranscript.textContent = errorMsg;
                    }
                }
                return; // Stop processing this error
            }
            
            // Check if circuit breaker is disabled
            if (serviceNotAllowedDisabled) {
                console.warn('[Poseidon] Circuit breaker is active - ignoring service-not-allowed error');
                return;
            }
            
            // Check if we should retry (cooldown period and retry limit)
            const shouldRetry = serviceNotAllowedRetryCount < MAX_SERVICE_NOT_ALLOWED_RETRIES && 
                               timeSinceLastError > SERVICE_NOT_ALLOWED_COOLDOWN_MS &&
                               !serviceNotAllowedDisabled;
            
            console.log('[Poseidon] Service-not-allowed retry check:', {
                retryCount: serviceNotAllowedRetryCount,
                maxRetries: MAX_SERVICE_NOT_ALLOWED_RETRIES,
                timeSinceLastError: timeSinceLastError,
                cooldown: SERVICE_NOT_ALLOWED_COOLDOWN_MS,
                shouldRetry: shouldRetry,
                rapidErrors: rapidErrorTimes.length,
                circuitBreakerActive: serviceNotAllowedDisabled
            });
            
            // Service not available - check if we're on secure context
            const isSecure = window.isSecureContext || location.protocol === 'https:' || 
                           location.hostname === 'localhost' || location.hostname === '127.0.0.1';
            
            if (!isSecure) {
                console.error('[Poseidon] Not in secure context - HTTPS required');
                errorMsg = 'Speech recognition requires HTTPS or localhost. Please use a secure connection.';
                updatePoseidonStatus('ready', 'HTTPS Required');
                shouldSpeak = true;
                shouldRestart = false;
            } else if (!shouldRetry) {
                // We've exceeded retry limit or are in cooldown - show error and stop
                console.error('[Poseidon] Max retries reached or in cooldown - stopping retry attempts');
                console.error('[Poseidon] Final service-not-allowed error - user action required');
                
                errorMsg = 'Speech recognition service is not available.\n\n' +
                          'Please try the following:\n' +
                          '1. Click the lock icon in your browser\'s address bar\n' +
                          '2. Allow microphone access for this site\n' +
                          '3. Refresh the page\n' +
                          '4. Try opening Poseidon again\n\n' +
                          'If the problem persists, your browser may not support speech recognition.';
                
                updatePoseidonStatus('ready', 'Permission Required');
                shouldSpeak = true;
                shouldRestart = false;
                
                // Reset retry counter after showing error (user can try again manually)
                serviceNotAllowedRetryCount = 0;
                lastServiceNotAllowedTime = 0;
            } else {
                // We're in a secure context and should retry
                // This usually means microphone permission wasn't properly granted
                // Safari-specific: May need different handling
                const isSafari = /Safari/.test(navigator.userAgent) && !/Chrome/.test(navigator.userAgent);
                
                // Safari: Be very conservative - Safari speech recognition is unreliable
                // Show message immediately without retrying
                if (isSafari) {
                    console.error('[Poseidon] Safari: service-not-allowed error detected');
                    console.error('[Poseidon] Safari speech recognition has very limited and unreliable support');
                    console.error('[Poseidon] This is a known Safari limitation - speech recognition may not work');
                    console.error('[Poseidon] Skipping retry attempts for Safari - showing user message immediately');
                    
                    // Don't retry for Safari - it's likely not supported
                    errorMsg = '⚠️ Safari Speech Recognition Limitation\n\n' +
                              'Safari has very limited and unreliable support for speech recognition.\n\n' +
                              'The Web Speech API in Safari is experimental and may not work on your system.\n\n' +
                              'For the best experience, please use:\n' +
                              '• Chrome (recommended - full support)\n' +
                              '• Edge (full support)\n\n' +
                              'If you must use Safari, try:\n' +
                              '1. Safari > Settings > Websites > Microphone - Allow for this site\n' +
                              '2. Ensure you\'re using HTTPS (not HTTP)\n' +
                              '3. Use Safari 14.1 or later\n' +
                              '4. Speech recognition may still not work due to Safari limitations\n\n' +
                              'Unfortunately, Safari\'s speech recognition support is unreliable and may not work at all.';
                    
                    updatePoseidonStatus('ready', 'Safari Limited Support');
                    if (poseidonAssistantTranscript) {
                        poseidonAssistantTranscript.textContent = errorMsg;
                    }
                    
                    // Try to speak the message
                    try {
                        speakText('Safari speech recognition is not available. Please use Chrome or Edge for better compatibility.');
                    } catch (speakErr) {
                        console.warn('[Poseidon] Could not speak Safari error message:', speakErr);
                    }
                    
                    shouldSpeak = false; // Already spoke
                    shouldRestart = false;
                    
                    // Disable circuit breaker for Safari to prevent further errors
                    serviceNotAllowedDisabled = true;
                    return;
                }
                
                serviceNotAllowedRetryCount++;
                lastServiceNotAllowedTime = now;
                
                console.warn(`[Poseidon] Service not allowed - retry attempt ${serviceNotAllowedRetryCount}/${MAX_SERVICE_NOT_ALLOWED_RETRIES}`, {
                    isSafari: isSafari
                });
                console.warn('[Poseidon] Attempting to recover by requesting permission again...');
                
                // Try to request permission again (async operation)
                (async () => {
                    try {
                        // Stop current recognition
                        if (recognition) {
                            try {
                                recognition.stop();
                                console.log('[Poseidon] Stopped recognition for permission retry');
                                // Safari needs more time to fully stop
                                const waitTime = isSafari ? 500 : 300;
                                await new Promise(resolve => setTimeout(resolve, waitTime));
                            } catch (stopErr) {
                                console.warn('[Poseidon] Error stopping recognition:', stopErr);
                            }
                        }
                        
                        // Request microphone permission again
                        console.log('[Poseidon] Re-requesting microphone permission...');
                        const stream = await navigator.mediaDevices.getUserMedia({ 
                            audio: {
                                echoCancellation: true,
                                noiseSuppression: true,
                                autoGainControl: true
                            }
                        });
                        console.log('[Poseidon] Permission re-granted, recreating recognition...');
                        
                        // CRITICAL: Keep the stream alive - don't let old stream be garbage collected
                        // Stop old stream tracks if they exist
                        if (window.poseidonAudioStream) {
                            try {
                                window.poseidonAudioStream.getTracks().forEach(track => track.stop());
                                console.log('[Poseidon] Stopped old stream tracks');
                            } catch (e) {
                                console.warn('[Poseidon] Error stopping old stream:', e);
                            }
                        }
                        
                        // Store new stream globally - CRITICAL to keep reference alive
                        window.poseidonAudioStream = stream;
                        
                        // Prevent stream from being garbage collected
                        // Keep at least one track active
                        const streamTracks = stream.getAudioTracks();
                        if (streamTracks.length > 0) {
                            streamTracks[0].enabled = true;
                            console.log('[Poseidon] Ensured stream track is enabled');
                        }
                        
                        // Verify stream is active
                        const tracks = stream.getAudioTracks();
                        const activeTracks = tracks.filter(t => t.readyState === 'live');
                        console.log('[Poseidon] Stream tracks:', activeTracks.length, 'active out of', tracks.length);
                        
                        // CRITICAL: Try to start recognition immediately after recovery
                        // We're still in the async function, but if the error happened quickly,
                        // we might still be within the user gesture context window
                        console.log('[Poseidon] Permission re-granted, attempting to start recognition immediately...');
                        
                        // Create new instance
                        // Safari requires webkitSpeechRecognition - MUST use webkit prefix
                        const isSafariRecovery = /Safari/.test(navigator.userAgent) && !/Chrome/.test(navigator.userAgent);
                        let SpeechRecognition;
                        
                        if (isSafariRecovery) {
                            // Safari MUST use webkitSpeechRecognition
                            if (!window.webkitSpeechRecognition) {
                                throw new Error('Safari requires webkitSpeechRecognition API');
                            }
                            SpeechRecognition = window.webkitSpeechRecognition;
                            console.log('[Poseidon] Safari detected in recovery - using webkitSpeechRecognition (required)');
                        } else {
                            SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
                        }
                        
                        if (SpeechRecognition) {
                            recognition = new SpeechRecognition();
                            
                            // Safari-specific configuration
                            if (isSafariRecovery) {
                                console.log('[Poseidon] Safari detected in recovery - applying Safari-specific config');
                            }
                            
                            // CRITICAL: Configure IMMEDIATELY after creation
                            recognition.continuous = true;
                            recognition.interimResults = true;
                            // MAJOR ENHANCEMENT: Explicit Hindi recognition language
                if (voiceSettings.accent === 'hi-IN' || currentLanguage === 'hi-IN') {
                    recognition.lang = 'hi-IN';
                    console.log('[Poseidon Hindi] Recognition language explicitly set to Hindi (hi-IN)');
                } else {
                    recognition.lang = voiceSettings.accent || currentLanguage || 'en-US';
                }
                            recognition.maxAlternatives = 1;
                            
                            console.log('[Poseidon] Recognition created and configured:', {
                                continuous: recognition.continuous,
                                interimResults: recognition.interimResults,
                                lang: recognition.lang
                            });
                            
                            // Setup handlers AFTER configuration
                            setupRecognitionHandlers();
                            
                            // RE-CONFIGURE to ensure settings persist (critical for Safari)
                            recognition.continuous = true;
                            recognition.interimResults = true;
                            // MAJOR ENHANCEMENT: Explicit Hindi recognition language
                if (voiceSettings.accent === 'hi-IN' || currentLanguage === 'hi-IN') {
                    recognition.lang = 'hi-IN';
                    console.log('[Poseidon Hindi] Recognition language explicitly set to Hindi (hi-IN)');
                } else {
                    recognition.lang = voiceSettings.accent || currentLanguage || 'en-US';
                }
                            recognition.maxAlternatives = 1;
                            
                            // Safari-specific: Ensure serviceURI is not set (let Safari use default)
                            if (isSafariRecovery && 'serviceURI' in recognition) {
                                console.log('[Poseidon] Safari detected - ensuring default serviceURI');
                            }
                            
                            console.log('[Poseidon] Recognition recreated with final config:', {
                                continuous: recognition.continuous,
                                interimResults: recognition.interimResults,
                                lang: recognition.lang,
                                isSafari: isSafariRecovery
                            });
                            
                            // Verify stream is still active
                            if (!window.poseidonAudioStream || !window.poseidonAudioStream.active) {
                                console.error('[Poseidon] ERROR: Stream not active after recovery');
                                throw new Error('Stream not active after recovery');
                            }
                            
                            const streamTracks = window.poseidonAudioStream.getAudioTracks();
                            const activeTracks = streamTracks.filter(t => t.readyState === 'live' && t.enabled && !t.muted);
                            if (activeTracks.length === 0) {
                                console.error('[Poseidon] ERROR: No active tracks after recovery');
                                throw new Error('No active tracks after recovery');
                            }
                            
                            console.log('[Poseidon] ✅ Stream verified active, attempting to start recognition...');
                            
                            // CRITICAL: Ensure poseidonActive is true if overlay is open
                            // The recovery flow might happen after overlay opens but before poseidonActive is set
                            // This is the ROOT CAUSE of the infinite listening problem
                            // Check multiple ways to detect if overlay is open
                            const overlayVisible = poseidonOverlay && (
                                poseidonOverlay.style.display !== 'none' ||
                                poseidonOverlay.style.display === 'flex' ||
                                poseidonOverlay.offsetParent !== null || // Element is visible
                                window.getComputedStyle(poseidonOverlay).display !== 'none'
                            );
                            
                            if (overlayVisible) {
                                poseidonActive = true;
                                poseidonPaused = false;
                                console.log('[Poseidon] ✅ Ensured poseidonActive=true (overlay is visible) - this fixes infinite listening');
                            } else {
                                console.warn('[Poseidon] ⚠️ Overlay check failed - overlay not visible:', {
                                    overlayExists: !!poseidonOverlay,
                                    displayStyle: poseidonOverlay?.style?.display,
                                    computedDisplay: poseidonOverlay ? window.getComputedStyle(poseidonOverlay).display : 'N/A',
                                    offsetParent: poseidonOverlay?.offsetParent !== null
                                });
                            }
                            
                            // Double-check poseidonActive after ensuring it
                            if (!poseidonActive) {
                                console.error('[Poseidon] ❌ CRITICAL: poseidonActive is still false after overlay check!');
                                console.error('[Poseidon] This indicates a state management bug. Forcing active state...');
                                poseidonActive = true;
                                poseidonPaused = false;
                            }
                            
                            // Try to start recognition immediately (might still be in gesture context)
                            // Safari is especially strict - must start synchronously
                            if (poseidonActive && !poseidonPaused) {
                                try {
                                    // Safari-specific: Re-verify configuration before starting
                                    if (isSafariRecovery) {
                                        recognition.continuous = true;
                                        recognition.interimResults = true;
                                        // MAJOR ENHANCEMENT: Explicit Hindi recognition language
                if (voiceSettings.accent === 'hi-IN' || currentLanguage === 'hi-IN') {
                    recognition.lang = 'hi-IN';
                    console.log('[Poseidon Hindi] Recognition language explicitly set to Hindi (hi-IN)');
                } else {
                    recognition.lang = voiceSettings.accent || currentLanguage || 'en-US';
                }
                                        console.log('[Poseidon] Safari: Re-verified config before start in recovery');
                                    }
                                    
                                    recognition.start();
                                    console.log('[Poseidon] ✅ Recognition started successfully after recovery!', {
                                        isSafari: isSafari
                                    });
                                    updatePoseidonStatus('listening', 'Listening...');
                                    
                                    // Reset retry counter on success
                                    serviceNotAllowedRetryCount = 0;
                                    lastServiceNotAllowedTime = 0;
                                    
                                    shouldSpeak = false;
                                    return; // Successfully started
                                } catch (startErr) {
                                    console.warn('[Poseidon] Could not start immediately after recovery:', startErr);
                                    console.warn('[Poseidon] This is normal if we lost user gesture context - will auto-retry');
                                    
                                    // If we can't start here, the error handler will trigger again
                                    // and we'll retry (up to MAX_SERVICE_NOT_ALLOWED_RETRIES)
                                    // But for now, just continue - the recognition instance is ready
                                    // and will be started on the next user interaction or error retry
                                    
                                    // Reset retry counter to allow one more attempt
                                    serviceNotAllowedRetryCount = Math.max(0, serviceNotAllowedRetryCount - 1);
                                    
                                    // Update status to show we're ready
                                    updatePoseidonStatus('ready', 'Ready - will start automatically');
                                    
                                    shouldSpeak = false;
                                    return; // Exit - will retry on next error or user action
                                }
                            } else {
                                // FINAL FALLBACK: If overlay is open but poseidonActive is false, force it
                                // This is a critical fix for the infinite listening bug
                                const overlayVisible = poseidonOverlay && (
                                    poseidonOverlay.style.display !== 'none' ||
                                    poseidonOverlay.style.display === 'flex' ||
                                    poseidonOverlay.offsetParent !== null ||
                                    window.getComputedStyle(poseidonOverlay).display !== 'none'
                                );
                                
                                if (overlayVisible) {
                                    console.error('[Poseidon] ❌ CRITICAL BUG: Overlay is open but poseidonActive is false!');
                                    console.error('[Poseidon] Forcing poseidonActive=true to fix infinite listening bug');
                                    poseidonActive = true;
                                    poseidonPaused = false;
                                    
                                    // Try again now that we've forced the state
                                    try {
                                        recognition.start();
                                        console.log('[Poseidon] ✅ Recognition started after forcing active state!');
                                        updatePoseidonStatus('listening', 'Listening...');
                                        serviceNotAllowedRetryCount = 0;
                                        lastServiceNotAllowedTime = 0;
                                        shouldSpeak = false;
                                        return;
                                    } catch (forceStartErr) {
                                        console.error('[Poseidon] Still failed after forcing state:', forceStartErr);
                                    }
                                }
                                
                                console.warn('[Poseidon] Cannot start - Poseidon inactive or paused', {
                                    poseidonActive: poseidonActive,
                                    poseidonPaused: poseidonPaused,
                                    overlayOpen: poseidonOverlay && poseidonOverlay.style.display !== 'none',
                                    overlayExists: !!poseidonOverlay
                                });
                                updatePoseidonStatus('ready', 'Ready');
                                shouldSpeak = false;
                                return;
                            }
                        }
                        
                        // If we get here, SpeechRecognition is not available
                        throw new Error('SpeechRecognition API not available');
                    } catch (recoveryErr) {
                        console.error('[Poseidon] ERROR: Failed to recover from service-not-allowed:', recoveryErr);
                        console.error('[Poseidon] Recovery error details:', {
                            name: recoveryErr?.name,
                            message: recoveryErr?.message,
                            stack: recoveryErr?.stack,
                            retryCount: serviceNotAllowedRetryCount
                        });
                        
                        // If we've exhausted retries, show error
                        if (serviceNotAllowedRetryCount >= MAX_SERVICE_NOT_ALLOWED_RETRIES) {
                            errorMsg = 'Speech recognition service is not available after multiple attempts.\n\n' +
                                      'Please:\n' +
                                      '1. Check browser microphone permissions\n' +
                                      '2. Ensure microphone is connected and working\n' +
                                      '3. Refresh the page and try again';
                            updatePoseidonStatus('ready', 'Service Unavailable');
                            shouldSpeak = true;
                        } else {
                            // Will retry on next error
                            shouldSpeak = false;
                        }
                    }
                })();
                
                // Don't show error immediately, wait for recovery attempt
                shouldSpeak = false;
                shouldRestart = false;
                return;
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
        
        // CRITICAL: Don't restart if circuit breaker is active
        if (shouldRestart && poseidonActive && !poseidonPaused && !serviceNotAllowedDisabled) {
            console.log('[Poseidon] Scheduling recognition restart after error');
            setTimeout(() => {
                // Double-check circuit breaker before restarting
                if (serviceNotAllowedDisabled) {
                    console.warn('[Poseidon] Circuit breaker active - cancelling scheduled restart');
                    return;
                }
                
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
    
    // Set inactive FIRST to prevent any async operations from continuing
    poseidonActive = false;
    poseidonPaused = false;
    transcriptProcessing = false;
    recognitionState = 'idle';
    
    // Clear all timeouts
    clearTimeout(silenceTimeout);
    clearTimeout(recognitionRestartTimeout);
    
    // Stop recognition FIRST (before stopping stream)
    if (recognition) {
        try {
            recognition.stop();
            console.log('[Poseidon] Recognition stopped');
        } catch (e) {
            console.warn('[Poseidon] Error stopping recognition:', e);
        }
    }
    
    // Stop speech synthesis
    if (speechSynthesis) {
        speechSynthesis.cancel();
        console.log('[Poseidon] Speech synthesis cancelled');
    }
    
    // Stop audio monitoring
    stopAudioLevelMonitoring();
    
    // Stop and release audio stream LAST
    if (window.poseidonAudioStream) {
        try {
            const tracks = window.poseidonAudioStream.getAudioTracks();
            tracks.forEach(track => {
                track.stop();
                console.log('[Poseidon] Stopped audio track:', track.label);
            });
            window.poseidonAudioStream = null;
            console.log('[Poseidon] Audio stream released');
        } catch (e) {
            console.warn('[Poseidon] Error releasing audio stream:', e);
        }
    }
    
    // Clean up 3D animation if enabled
    if (poseidon3D) {
        try {
            poseidon3D.dispose();
            poseidon3D = null;
            console.log('[Poseidon] 3D animation disposed');
        } catch (error) {
            console.error('[Poseidon] Error disposing 3D animation:', error);
        }
    }
    
    // Restore wave animation if 3D was enabled
    if (poseidonVisualizer && poseidon3DEnabled) {
        poseidonVisualizer.innerHTML = '<div class="poseidon-wave"><div class="wave-bar"></div><div class="wave-bar"></div><div class="wave-bar"></div><div class="wave-bar"></div><div class="wave-bar"></div></div>';
        poseidonVisualizer.classList.remove('poseidon-3d-container');
        poseidonVisualizer.style = '';
    }
    
    // Reset state
    lastSpeechTime = null;
    pendingTranscript = '';
    speechDetected = false;
    consecutiveNoSpeechCount = 0;
    serviceNotAllowedRetryCount = 0; // Reset retry counter
    lastServiceNotAllowedTime = 0;
    rapidErrorTimes = []; // Reset rapid error tracking
    serviceNotAllowedDisabled = false; // Reset circuit breaker
    lastHighVolumeTime = 0;
    currentAudioLevel = 0;
    audioLevelHistory = [];
    
    // Hide overlay
    if (poseidonOverlay) {
        poseidonOverlay.style.display = 'none';
    }
    
    updatePoseidonStatus('ready', 'Ready');
    
    // Clear transcripts
    if (poseidonUserTranscript) {
        poseidonUserTranscript.textContent = '';
    }
    if (poseidonAssistantTranscript) {
        poseidonAssistantTranscript.textContent = '';
    }
    
    // Cleanup 3D animation (v3.x)
    if (poseidon3D && typeof poseidon3D.dispose === 'function') {
        try {
            poseidon3D.dispose();
            poseidon3D = null;
            console.log('[Poseidon] 3D animation disposed');
        } catch (error) {
            console.error('[Poseidon] Error disposing 3D animation:', error);
        }
    }
    
    console.log('[Poseidon] Overlay closed and all resources released');
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
    console.log(`[Poseidon] Status update: ${status} - "${text}"`);
    
    if (poseidonStatusIndicator) {
        poseidonStatusIndicator.className = 'poseidon-status-indicator';
        // Remove all status classes
        poseidonStatusIndicator.classList.remove('listening', 'thinking', 'speaking', 'processing', 'ready', 'paused');
        
        // Add appropriate class
        if (status === 'listening') {
            poseidonStatusIndicator.classList.add('listening');
        } else if (status === 'thinking' || status === 'processing') {
            poseidonStatusIndicator.classList.add('thinking');
        } else if (status === 'speaking') {
            poseidonStatusIndicator.classList.add('speaking');
        } else if (status === 'paused') {
            poseidonStatusIndicator.classList.add('paused');
        } else {
            poseidonStatusIndicator.classList.add('ready');
        }
    }
    
    if (poseidonStatusText) {
        poseidonStatusText.textContent = text;
    }
    
    if (poseidonVisualizer) {
        poseidonVisualizer.className = 'poseidon-visualizer';
        // Remove all status classes
        poseidonVisualizer.classList.remove('listening', 'thinking', 'speaking', 'processing', 'ready', 'paused');
        
        // Add appropriate class
        if (status === 'listening') {
            poseidonVisualizer.classList.add('listening');
        } else if (status === 'thinking' || status === 'processing') {
            poseidonVisualizer.classList.add('thinking');
        } else if (status === 'speaking') {
            poseidonVisualizer.classList.add('speaking');
        } else if (status === 'paused') {
            poseidonVisualizer.classList.add('paused');
        } else {
            poseidonVisualizer.classList.add('ready');
        }
    }
}
