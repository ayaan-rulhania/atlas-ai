// Atlas AI - Thor 1.1 Frontend
// Version 2.0.0 - Major UI/UX overhaul with modern navigation, orange theme, responsive design
let currentChatId = null;
let isLoading = false;
let thinkDeeperMode = false;
let allChats = [];
let currentTheme = 'light';
let themePreference = 'system';
let currentModel = 'thor-1.2';
const PRO_ACCESS_CODE = 'QUANTUM4FUTURE';
let currentTone = 'normal';
let systemMode = localStorage.getItem('systemMode') || 'latest';
let uiMode = localStorage.getItem('uiMode') || 'standard';

// Beta AI capabilities
let comparisonMode = false;
let currentOutputFormat = '';

// Gems (custom sub-models)
let gems = [];
let activeGemDraft = null; 

// Enhanced Features v1.4.2
let keyboardShortcuts = {};
let smartSuggestions = [];
let notifications = [];
let quickActionsMenu = null;

// Background Customization v1.4.5 (Enhanced in v2.0.0 with sidebar support)

// Beta Features v2.0.0
let betaModeEnabled = localStorage.getItem('betaModeEnabled') === 'true';
let betaFeatures = JSON.parse(localStorage.getItem('betaFeatures') || '{}');

// Beta feature configuration schema
const BETA_FEATURE_CATEGORIES = {
    collaboration: {
        name: 'Collaboration & Sharing',
        features: {
            shared_chats: { name: 'Shared Chats', description: 'Share chats with others and collaborate in real-time', default: false },
            gem_marketplace: { name: 'Gem Marketplace', description: 'Public gallery to share and discover custom Gems', default: false },
            enhanced_exports: { name: 'Enhanced Export Formats', description: 'PDF, Markdown, and HTML export options', default: false },
            chat_templates: { name: 'Chat Templates', description: 'Save and reuse conversation templates', default: false }
        }
    },
    productivity: {
        name: 'Productivity & Workflow',
        features: {
            task_management: { name: 'Task Management', description: 'Parse tasks from conversations and create to-do lists', default: false },
            workflow_automation: { name: 'Workflow Automation', description: 'Multi-step workflows with conditional logic', default: false },
            quick_actions: { name: 'Quick Actions & Snippets', description: 'Custom response templates and saved prompts', default: false },
            smart_summaries: { name: 'Smart Summaries', description: 'Auto-summarize conversations with different formats', default: false }
        }
    },
    ai_capabilities: {
        name: 'Enhanced AI Capabilities',
        features: {
            multi_model_comparison: { name: 'Multi-Model Comparison', description: 'Compare responses across different models', default: false },
            structured_output: { name: 'Structured Output Mode', description: 'Generate JSON, tables, and formatted data', default: false },
            code_execution: { name: 'Code Execution', description: 'Run Python and JavaScript code snippets', default: false },
            agent_mode: { name: 'Agent Mode', description: 'Multi-step reasoning with tool use', default: false }
        }
    },
    search_discovery: {
        name: 'Search & Discovery',
        features: {
            global_search: { name: 'Global Search', description: 'Search across all chats and projects', default: false },
            insights_dashboard: { name: 'Insights Dashboard', description: 'Analytics and usage statistics', default: false },
            smart_suggestions: { name: 'Smart Suggestions', description: 'Context-aware prompt and follow-up suggestions', default: false }
        }
    },
    integrations: {
        name: 'Integrations & Extensibility',
        features: {
            api_integrations: { name: 'API Integrations', description: 'Webhooks and external service integrations', default: false },
            browser_extension: { name: 'Browser Extension', description: 'Quick access from any website', default: false },
            plugin_system: { name: 'Plugin System', description: 'Custom plugins and marketplace', default: false }
        }
    },
    document_management: {
        name: 'Document & Content Management',
        features: {
            advanced_processing: { name: 'Advanced Document Processing', description: 'PDF parsing, OCR, and table extraction', default: false },
            document_library: { name: 'Document Library', description: 'Centralized document storage and search', default: false },
            knowledge_base: { name: 'Knowledge Base Builder', description: 'Auto-generate KB from conversations', default: false }
        }
    },
    ux_enhancements: {
        name: 'UX Enhancements',
        features: {
            custom_themes: { name: 'Custom Themes', description: 'Theme builder with export/import', default: false },
            keyboard_navigation: { name: 'Keyboard Navigation', description: 'Enhanced shortcuts and Vim-style navigation', default: false },
            accessibility: { name: 'Accessibility Improvements', description: 'Screen reader and high contrast enhancements', default: false }
        }
    },
    advanced_features: {
        name: 'Advanced Features',
        features: {
            version_control: { name: 'Version Control for Chats', description: 'Git-like branching and diff viewer', default: false },
            encrypted_chats: { name: 'Private/Encrypted Chats', description: 'Password-protected and encrypted conversations', default: false },
            team_management: { name: 'Team Management', description: 'Organizations, roles, and team analytics', default: false }
        }
    }
};

// Utility functions for beta features
function isBetaFeatureEnabled(featureName) {
    return betaModeEnabled && (betaFeatures[featureName] !== false);
}

function setBetaModeEnabled(enabled) {
    betaModeEnabled = enabled;
    localStorage.setItem('betaModeEnabled', enabled.toString());

    if (!enabled) {
        // Reset all beta features to disabled when beta mode is turned off
        betaFeatures = {};
        localStorage.setItem('betaFeatures', JSON.stringify(betaFeatures));
    }

    updateBetaModeUI();
}

function setBetaFeatureEnabled(featureName, enabled) {
    if (!betaModeEnabled) return;

    betaFeatures[featureName] = enabled;
    localStorage.setItem('betaFeatures', JSON.stringify(betaFeatures));
}

function getBetaFeatureCategories() {
    return Object.entries(BETA_FEATURE_CATEGORIES).map(([key, category]) => ({
        key,
        name: category.name,
        features: Object.entries(category.features).map(([featureKey, feature]) => ({
            key: featureKey,
            name: feature.name,
            description: feature.description,
            enabled: betaFeatures[featureKey] !== false
        }))
    }));
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    initializeKineticTypography();
    initializeKeyboardShortcuts();
    initializeAdvancedSearch();
    initializeSmartSuggestions();
    initializeNotifications();
    initializeQuickActions();
    initializeExportImport();
    initializeKeyboardShortcuts();
    initializeCommandPalette();
    initializeDragAndDrop();
    initializeContextMenus();
    initializePWA();
    initializeVirtualScrolling();
});

async function initializeApp() {
    initializeTheme();
    initializeTone();
    initializeSystemMode();
    initializeUIMode();
    initializeBetaMode();
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

function initializeKineticTypography() {
    const titleEl = document.querySelector('.welcome-title');
    if (!titleEl) return;

    const text = titleEl.textContent;
    titleEl.innerHTML = ''; // clear before injecting spans

    // Split text into individual character spans
    [...text].forEach((ch, i) => {
        const span = document.createElement('span');
        span.className = 'char';
        span.style.display = 'inline-block';
        span.style.animationDelay = `${i * 40}ms, ${i * 60}ms`;
        span.textContent = ch === ' ' ? '\u00A0' : ch; // preserve spaces with non-breaking space
        titleEl.appendChild(span);
    });

    // Hover kinetic pop animation
    titleEl.addEventListener('mouseenter', () => {
        [...titleEl.querySelectorAll('.char')].forEach((el, idx) => {
            el.animate(
                [
                    { transform: 'translateZ(0) scale(1)' },
                    { transform: 'translateZ(24px) scale(1.08)' },
                    { transform: 'translateZ(0) scale(1)' },
                ],
                {
                    duration: 480,
                    delay: idx * 18,
                    easing: 'cubic-bezier(.2,.9,.2,1)',
                }
            );
        });
    });
}

async function restoreModelPreference() {
    // Load saved model preference - Gems are not in dropdown, only accessible via sidebar
    // Default to Thor 1.2 unless API says otherwise
    let defaultModel = 'thor-1.2';
    
    // Try to get default from API
    try {
        const response = await fetch('/api/model/status');
        const data = await response.json();
        defaultModel = data.default_model || 'thor-1.2';
    } catch (e) {
        // Fallback to Thor 1.2 if API call fails
        defaultModel = 'thor-1.2';
    }
    
    const savedModel = localStorage.getItem('selectedModel') || defaultModel;
    // If a gem is saved, keep it (for sidebar access) but default dropdown to Thor 1.2
    // Gems can still be selected via sidebar, just not shown in dropdown
    if (savedModel && savedModel.startsWith('gem:')) {
        currentModel = savedModel; // Keep gem selection for sidebar
    } else if (savedModel && (savedModel === 'thor-1.0' || savedModel === 'thor-1.1' || savedModel === 'thor-1.2' || savedModel === 'antelope-1.0' || savedModel === 'antelope-1.1')) {
        // Respect saved model if it's a valid model
        currentModel = savedModel;
    } else {
        // Use default (Thor 1.2)
        currentModel = defaultModel;
        localStorage.setItem('selectedModel', defaultModel);
    }
    // UI will be updated after `loadGems()` rebuilds the dropdown.
    // Apply a default tone immediately; `loadGems()` may override with a Gem tone.
    document.body.setAttribute('data-tone', currentTone || 'normal');
}

function setupEventListeners() {
    const sendBtn = document.getElementById('sendBtn');
    const messageInput = document.getElementById('messageInput');
    const newChatBtn = document.getElementById('newChatBtn');
    const recentChatsBtn = document.getElementById('recentChatsBtn');
    const gemsDashboardBtn = document.getElementById('gemsDashboardBtn');
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
    const deleteAllChatsBtn = document.getElementById('deleteAllChatsBtn');
    
    sendBtn.addEventListener('click', handleSendMessage);
    newChatBtn.addEventListener('click', startNewChat);
    if (recentChatsBtn) recentChatsBtn.addEventListener('click', openRecentChatsModal);
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
    if (gemsDashboardBtn) gemsDashboardBtn.addEventListener('click', openCustomizeModal);
    if (deleteAllChatsBtn) deleteAllChatsBtn.addEventListener('click', handleDeleteAllChats);
    if (installBtn) installBtn.addEventListener('click', () => {
        // Check if running in Electron app (macOS app)
        const isElectron = window.electronAPI !== undefined;
        const targetUrl = isElectron ? '/update' : '/install';
        
        // Smooth fade-out transition
        document.body.style.transition = 'opacity 0.3s ease';
        document.body.style.opacity = '0';
        
        setTimeout(() => {
            window.location.href = targetUrl;
        }, 300);
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
    
    // User profile modal
    const userAvatar = document.getElementById('userAvatar');
    if (userAvatar) userAvatar.addEventListener('click', openUserProfileModal);
    const closeUserProfileModal = document.getElementById('closeUserProfileModal');
    if (closeUserProfileModal) closeUserProfileModal.addEventListener('click', closeUserProfileModalFunc);
    
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

    // Recent chats dashboard modal
    const closeRecentChatsModal = document.getElementById('closeRecentChatsModal');
    if (closeRecentChatsModal) closeRecentChatsModal.addEventListener('click', closeRecentChatsModalFunc);
    
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

    // Embedded apps (Gaming / Office)
    document.querySelectorAll('.welcome-action-card--embed').forEach(btn => {
        btn.addEventListener('click', () => {
            const url = btn.getAttribute('data-embed-url') || '';
            const title = btn.getAttribute('data-embed-title') || 'App';
            openEmbeddedAppModal(url, title);
        });
    });

    const closeEmbeddedAppModalBtn = document.getElementById('closeEmbeddedAppModal');
    if (closeEmbeddedAppModalBtn) closeEmbeddedAppModalBtn.addEventListener('click', closeEmbeddedAppModalFunc);

    // Templates button (Beta feature)
    const templatesBtn = document.getElementById('templatesBtn');
    if (templatesBtn) templatesBtn.addEventListener('click', openTemplatesModal);

    // Tasks button (Beta feature)
    const tasksBtn = document.getElementById('tasksBtn');
    if (tasksBtn) tasksBtn.addEventListener('click', openTasksPanel);

    // Templates modal
    const closeTemplatesModalBtn = document.getElementById('closeTemplatesModal');
    if (closeTemplatesModalBtn) closeTemplatesModalBtn.addEventListener('click', closeTemplatesModalFunc);

    const createTemplateBtn = document.getElementById('createTemplateBtn');
    if (createTemplateBtn) createTemplateBtn.addEventListener('click', () => {
        // TODO: Open template creation modal/form
        showNotification('Template creation coming soon!', 'info', 3000);
    });

    // Tasks panel
    const closeTasksPanelBtn = document.getElementById('closeTasksPanel');
    if (closeTasksPanelBtn) closeTasksPanelBtn.addEventListener('click', closeTasksPanel);

    const extractTasksBtn = document.getElementById('extractTasksBtn');
    if (extractTasksBtn) extractTasksBtn.addEventListener('click', extractTasksFromCurrentChat);

    const refreshTasksBtn = document.getElementById('refreshTasksBtn');
    if (refreshTasksBtn) refreshTasksBtn.addEventListener('click', loadTasks);

    // Global search (Beta feature)
    const globalSearchBtn = document.getElementById('globalSearchBtn');
    if (globalSearchBtn) globalSearchBtn.addEventListener('click', openGlobalSearchModal);

    // Analytics (Beta feature)
    const analyticsBtn = document.getElementById('analyticsBtn');
    if (analyticsBtn) analyticsBtn.addEventListener('click', openAnalyticsModal);

    // Global search modal
    const closeGlobalSearchModalBtn = document.getElementById('closeGlobalSearchModal');
    if (closeGlobalSearchModalBtn) closeGlobalSearchModalBtn.addEventListener('click', closeGlobalSearchModal);

    // Analytics modal
    const closeAnalyticsModalBtn = document.getElementById('closeAnalyticsModal');
    if (closeAnalyticsModalBtn) closeAnalyticsModalBtn.addEventListener('click', closeAnalyticsModal);

    // Beta AI capabilities
    const compareModelsBtn = document.getElementById('compareModelsBtn');
    if (compareModelsBtn) compareModelsBtn.addEventListener('click', openModelComparison);

    const outputFormatSelector = document.getElementById('outputFormatSelector');
    if (outputFormatSelector) {
        outputFormatSelector.addEventListener('click', toggleOutputFormatDropdown);

        // Handle format selection
        const formatOptions = outputFormatSelector.querySelectorAll('.output-format-option');
        formatOptions.forEach(option => {
            option.addEventListener('click', (e) => {
                e.stopPropagation();
                const format = option.getAttribute('data-format');
                setOutputFormat(format);
            });
        });
    }

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

// Model loading progress tracking
let modelLoadingProgressInterval = null;
let lastProgressState = {};

async function checkModelStatus() {
    try {
        const response = await fetch('/api/model/status');
        const data = await response.json();
        
        // Update default model based on what's loaded
        const defaultModelFromAPI = data.default_model || 'thor-1.2';
        const currentSavedModel = localStorage.getItem('selectedModel');
        
        // If no model is saved or saved model is not loaded, use default from API
        if (!currentSavedModel || (!data.models?.[currentSavedModel]?.loaded && !currentSavedModel.startsWith('gem:'))) {
            if (defaultModelFromAPI && defaultModelFromAPI !== currentModel) {
                currentModel = defaultModelFromAPI;
                localStorage.setItem('selectedModel', defaultModelFromAPI);
                updateModelSelector();
                rebuildModelDropdown();
            }
        }
        
        // Check and display loading progress for all models
        let anyModelLoading = false;
        for (const [modelKey, modelData] of Object.entries(data.models || {})) {
            const progress = modelData.loading_progress || {};
            const progressKey = `${modelKey}_progress`;
            
            // Only update if progress changed
            if (JSON.stringify(lastProgressState[progressKey]) !== JSON.stringify(progress)) {
                lastProgressState[progressKey] = progress;
                
                if (progress.status === 'loading') {
                    anyModelLoading = true;
                    const progressPercent = progress.progress || 0;
                    const message = progress.message || 'Loading...';
                    console.log(`[Model Loading] ${modelKey}: ${progressPercent}% - ${message}`);
                    
                    // Display progress in UI
                    displayModelLoadingProgress(modelKey, progressPercent, message);
                } else if (progress.status === 'loaded') {
                    console.log(`[Model Loading] ${modelKey}: ✅ Loaded successfully`);
                    hideModelLoadingProgress(modelKey);
                } else if (progress.status === 'failed') {
                    console.warn(`[Model Loading] ${modelKey}: ❌ Failed - ${progress.message}`);
                    hideModelLoadingProgress(modelKey);
                }
            }
        }
        
        // Start/stop progress polling
        if (anyModelLoading && !modelLoadingProgressInterval) {
            // Poll every 500ms when loading
            modelLoadingProgressInterval = setInterval(checkModelStatus, 500);
        } else if (!anyModelLoading && modelLoadingProgressInterval) {
            clearInterval(modelLoadingProgressInterval);
            modelLoadingProgressInterval = null;
        }
        
        // Check Thor 1.2 model status (default - same backend as 1.1)
        const thor12Model = data.models?.['thor-1.2'];
        if (thor12Model) {
            if (!thor12Model.loaded) {
                console.warn('[Model Status] ⚠️ Thor 1.2 model is not loaded');
                if (thor12Model.diagnostics?.message) {
                    console.warn('[Model Status] Reason:', thor12Model.diagnostics.message);
                }
            } else {
                console.log('[Model Status] ✅ Thor 1.2 model is loaded and ready');
            }
        }
        
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

function displayModelLoadingProgress(modelKey, progress, message) {
    // Create or update progress indicator
    let progressIndicator = document.getElementById(`model-loading-${modelKey}`);
    if (!progressIndicator) {
        progressIndicator = document.createElement('div');
        progressIndicator.id = `model-loading-${modelKey}`;
        progressIndicator.className = 'model-loading-progress';
        progressIndicator.innerHTML = `
            <div class="model-loading-header">
                <span class="model-loading-name">Loading ${modelKey}...</span>
                <span class="model-loading-percent">${progress}%</span>
            </div>
            <div class="model-loading-bar-container">
                <div class="model-loading-bar" style="width: ${progress}%"></div>
            </div>
            <div class="model-loading-message">${escapeHtml(message)}</div>
        `;
        
        // Insert at top of chat area or in a dedicated area
        const chatContainer = document.getElementById('chatContainer') || document.body;
        chatContainer.insertBefore(progressIndicator, chatContainer.firstChild);
    } else {
        // Update existing indicator
        progressIndicator.querySelector('.model-loading-percent').textContent = `${progress}%`;
        progressIndicator.querySelector('.model-loading-bar').style.width = `${progress}%`;
        progressIndicator.querySelector('.model-loading-message').textContent = message;
    }
}

function hideModelLoadingProgress(modelKey) {
    const progressIndicator = document.getElementById(`model-loading-${modelKey}`);
    if (progressIndicator) {
        progressIndicator.remove();
    }
}

// Track active polling intervals
const modelLoadingPollers = {};

function startModelLoadingPolling(modelName, initialProgress, initialMessage, userMessageId, loadingId) {
    // Stop any existing poller for this model
    if (modelLoadingPollers[modelName]) {
        clearInterval(modelLoadingPollers[modelName]);
    }
    
    // Update loading message to show progress
    const displayMessage = `Model Currently Loading - ${initialProgress}% Loaded.`;
    if (loadingId) {
        replaceLoadingMessage(loadingId, displayMessage + ' ' + initialMessage);
    }
    
    // Display progress indicator
    displayModelLoadingProgress(modelName, initialProgress, initialMessage);
    
    // Start polling
    let pollCount = 0;
    const maxPolls = 600; // 5 minutes max (600 * 500ms)
    
    modelLoadingPollers[modelName] = setInterval(async () => {
        pollCount++;
        
        try {
            const response = await fetch(`/api/model/loading-progress?model=${encodeURIComponent(modelName)}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            const progress = data.progress || 0;
            const status = data.status || 'loading';
            const message = data.message || 'Loading...';
            const displayMsg = data.display_message || `Model Currently Loading - ${progress}% Loaded.`;
            
            // Update progress indicator
            displayModelLoadingProgress(modelName, progress, message);
            
            // Update loading message
            if (loadingId) {
                replaceLoadingMessage(loadingId, displayMsg);
            }
            
            if (status === 'loaded') {
                // Model loaded! Clear polling and retry the request
                clearInterval(modelLoadingPollers[modelName]);
                delete modelLoadingPollers[modelName];
                hideModelLoadingProgress(modelName);
                
                // Retry the original message
                console.log(`[Model Loading] ${modelName} loaded, retrying message...`);
                if (loadingId) {
                    replaceLoadingMessage(loadingId, 'Model loaded! Sending your message...');
                }
                
                // Retry the send
                setTimeout(() => {
                    handleSendMessage();
                }, 500);
            } else if (status === 'failed') {
                // Model failed to load
                clearInterval(modelLoadingPollers[modelName]);
                delete modelLoadingPollers[modelName];
                hideModelLoadingProgress(modelName);
                
                if (loadingId) {
                    replaceLoadingMessage(loadingId, `Model failed to load: ${message}. Please try again or use a different model.`);
                }
            } else if (pollCount >= maxPolls) {
                // Timeout
                clearInterval(modelLoadingPollers[modelName]);
                delete modelLoadingPollers[modelName];
                hideModelLoadingProgress(modelName);
                
                if (loadingId) {
                    replaceLoadingMessage(loadingId, 'Model loading timed out. Please try again or use a different model.');
                }
            }
        } catch (error) {
            console.error(`[Model Loading] Error polling ${modelName}:`, error);
            // Continue polling on error (might be temporary)
        }
    }, 500); // Poll every 500ms
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
            // If selecting from the Recent Chats dashboard, close it after navigation
            const recentModal = document.getElementById('recentChatsModal');
            if (recentModal && recentModal.style.display === 'flex' && typeof closeRecentChatsModalFunc === 'function') {
                closeRecentChatsModalFunc();
            }
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
        
        // Show messages container (welcome screen stays visible above)
        document.getElementById('messagesContainer').style.display = 'flex';
    } catch (error) {
        console.error('Error loading chat:', error);
    }
}

function displayMessages(messages) {
    const container = document.getElementById('messagesContainer');
    
    // Group messages and render
    let html = '';
    let currentGroup = [];
    let lastRole = null;
    
    messages.forEach((msg, index) => {
        const role = msg.role;
        const content = msg.content;
        const timestamp = msg.timestamp || new Date().toISOString();
        const avatar = role === 'user' ? 'U' : 'A';
        
        // Render markdown for assistant messages
        const renderedContent = role === 'assistant' 
            ? renderMarkdown(content) 
            : escapeHtml(content);
        
        // Check if we should start a new group (role changed or first message)
        if (lastRole !== null && lastRole !== role) {
            // Close previous group
            if (currentGroup.length > 0) {
                html += `<div class="message-group">${currentGroup.join('')}</div>`;
                currentGroup = [];
            }
        }
        
        // Add message to current group
        const messageHTML = `
            <div class="message ${role}" data-timestamp="${timestamp}">
                <div class="message-avatar">${avatar}</div>
                <div class="message-content">${renderedContent}</div>
                ${createMessageActionsHTML(role)}
                ${createMessageTimestampHTML(timestamp)}
            </div>
        `;
        currentGroup.push(messageHTML);
        lastRole = role;
        
        // If this is the last message, close the group
        if (index === messages.length - 1) {
            html += `<div class="message-group">${currentGroup.join('')}</div>`;
        }
    });
    
    container.innerHTML = html;
    
    // Setup message actions for all messages
    container.querySelectorAll('.message').forEach(msg => {
        setupMessageActions(msg);
    });
    
    // Initialize virtual scrolling if needed (Phase 5.2 Enhancement)
    setTimeout(() => {
        const messages = container.querySelectorAll('.message, .message-group');
        if (messages.length > 50) {
            initializeVirtualScrolling();
        }
    }, 100);
    
    // Smooth scroll after messages load (Phase 1 Enhancement)
    setTimeout(() => {
        scrollToBottom(true);
    }, 50);
}

function startNewChat() {
    currentChatId = null;
    document.getElementById('welcomeScreen').style.display = 'flex';
    document.getElementById('messagesContainer').style.display = 'none';
    document.getElementById('messagesContainer').innerHTML = '';
    document.getElementById('messageInput').value = '';
    updateChatList();
    // Scroll to top to show welcome screen
    const chatContainer = document.getElementById('chatContainer');
    if (chatContainer) {
        chatContainer.scrollTop = 0;
    }
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
    
    // Keep welcome screen visible, just show messages container below it
    const welcomeScreen = document.getElementById('welcomeScreen');
    const messagesContainer = document.getElementById('messagesContainer');
    
    // Always show messages container (it will appear below welcome screen)
    messagesContainer.style.display = 'flex';
    
    // Add user message to UI (show the transformed command)
    const userMessageId = addMessageToUI('user', messageToSend, false, 'sending');
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

        // Beta features
        if (comparisonMode && betaModeEnabled) {
            requestBody.compare_models = ['thor-1.2', 'thor-1.0']; // Default comparison models
            comparisonMode = false; // Reset after use
        }

        if (currentOutputFormat && betaModeEnabled) {
            requestBody.output_format = currentOutputFormat;
        }

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
            
            // Check if model is loading (503 status with loading info)
            if (response.status === 503 && errorData.model_status === 'loading') {
                // Model is loading - start polling for progress
                const modelName = currentModel || 'thor-1.2';
                startModelLoadingPolling(modelName, errorData.loading_progress || 0, errorData.loading_message || 'Loading...', userMessageId, loadingId);
                return; // Exit early, polling will handle the rest
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
            // Check if it's a loading status error
            if (data.model_status === 'loading') {
                const modelName = currentModel || 'thor-1.2';
                startModelLoadingPolling(modelName, data.loading_progress || 0, data.loading_message || 'Loading...', userMessageId, loadingId);
                return; // Exit early, polling will handle the rest
            }
            throw new Error(data.error);
        }

        // Handle beta comparison mode
        if (data.comparison_mode) {
            return handleComparisonResponse(data, userMessageId, loadingId);
        }

        // Ensure we have a response field
        if (!data.response) {
            console.error('No response field in data:', data);
            throw new Error('Server returned invalid response format');
        }
        
        // Update current chat ID
        currentChatId = data.chat_id;
        
        // Update user message status to sent
        updateMessageStatus(userMessageId, 'sent');
        
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
        // Show more helpful error message (hide raw Python/backend errors from users)
        let userFriendlyError = errorMessage;
        if (errorMessage.includes('Failed to fetch') || errorMessage.includes('NetworkError')) {
            userFriendlyError = 'Cannot connect to server. Please make sure the server is running (python app.py)';
        } else if (errorMessage.includes('parse')) {
            userFriendlyError = 'Server returned invalid response. Please check server logs.';
        } else if (errorMessage.includes('NoneType') || errorMessage.includes('get_response') || errorMessage.includes("'analyze'") || errorMessage.includes('AttributeError') || errorMessage.includes('object has no attribute')) {
            userFriendlyError = 'Something went wrong on the server. Please try again.';
        }
        
        // Update user message status to error
        if (userMessageId) {
            updateMessageStatus(userMessageId, 'error');
        }
        
        if (loadingId) {
            replaceLoadingMessage(loadingId, `Sorry, I encountered an error: ${userFriendlyError}. Please check the browser console (F12) for details.`);
        }
    } finally {
        isLoading = false;
        updateSendButton(false);
    }
}

function createSkeletonMessage(role = 'assistant') {
    const skeletonClass = role === 'user' ? 'skeleton-message--user' : 'skeleton-message--assistant';
    return `
        <div class="skeleton-message-container ${role === 'user' ? 'skeleton-message-container--user' : ''}">
            <div class="message-avatar" style="display: none;"></div>
            <div class="skeleton skeleton-message ${skeletonClass}"></div>
        </div>
    `;
}

function createSkeletonChatCard() {
    return `
        <div class="skeleton skeleton-chat"></div>
    `;
}

function createSkeletonGemCard() {
    return `
        <div class="skeleton skeleton-gem"></div>
    `;
}

function addMessageToUI(role, content, isLoading = false, status = 'sent', timestamp = null) {
    const container = document.getElementById('messagesContainer');
    const messageId = 'msg-' + Date.now() + '-' + Math.random();
    
    // Use current time if no timestamp provided
    if (!timestamp) {
        timestamp = new Date().toISOString();
    }
    
    const avatar = role === 'user' ? 'U' : 'A';
    let messageContent;
    
    if (isLoading) {
        messageContent = createSkeletonMessage(role);
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
    messageDiv.setAttribute('data-timestamp', timestamp);
    
    if (isLoading) {
        messageDiv.innerHTML = messageContent;
    } else {
        messageDiv.innerHTML = `
            <div class="message-avatar">${avatar}</div>
            <div class="message-content">${messageContent}</div>
            ${createMessageActionsHTML(role)}
            ${createMessageTimestampHTML(timestamp)}
            ${role === 'user' ? createMessageStatusHTML(status) : ''}
        `;
        setupMessageActions(messageDiv);
    }
    
    container.appendChild(messageDiv);
    
    // Check if virtual scrolling should be enabled (Phase 5.2 Enhancement)
    if (!virtualScrollEnabled) {
        const messages = container.querySelectorAll('.message, .message-group');
        if (messages.length > 50) {
            setTimeout(() => initializeVirtualScrolling(), 50);
        }
    }
    
    // Smooth scroll for new messages (Phase 1 Enhancement)
    scrollToBottom(true);
    
    return messageId;
}

function replaceLoadingMessage(messageId, content) {
    const messageDiv = document.getElementById(messageId);
    if (messageDiv) {
        // Check if this is a skeleton message (has skeleton class)
        const isSkeleton = messageDiv.querySelector('.skeleton');
        if (isSkeleton) {
            // Replace entire skeleton structure with actual message
            const role = messageDiv.classList.contains('user') ? 'user' : 'assistant';
            const avatar = role === 'user' ? 'U' : 'A';
            const renderedContent = role === 'assistant' ? renderMarkdown(content) : escapeHtml(content);
            const timestamp = messageDiv.getAttribute('data-timestamp') || new Date().toISOString();
            messageDiv.innerHTML = `
                <div class="message-avatar">${avatar}</div>
                <div class="message-content">${renderedContent}</div>
                ${createMessageActionsHTML(role)}
                ${createMessageTimestampHTML(timestamp)}
            `;
            setupMessageActions(messageDiv);
        } else {
            // Traditional loading indicator replacement
            const contentDiv = messageDiv.querySelector('.message-content');
            if (contentDiv) {
                // Render markdown for assistant responses
                contentDiv.innerHTML = renderMarkdown(content);
                // Add message actions if not already present
                if (!messageDiv.querySelector('.message-actions')) {
                    const role = messageDiv.classList.contains('user') ? 'user' : 'assistant';
                    messageDiv.insertAdjacentHTML('beforeend', createMessageActionsHTML(role));
                    setupMessageActions(messageDiv);
                }
            }
        }
    }
}

function scrollToBottom(smooth = false) {
    const container = document.getElementById('messagesContainer');
    if (!container) return;
    
    if (smooth) {
        container.scrollTo({
            top: container.scrollHeight,
            behavior: 'smooth'
        });
    } else {
        container.scrollTop = container.scrollHeight;
    }
}

// ============================================
// MESSAGE ACTIONS (Phase 2.1)
// ============================================

function createMessageActionsHTML(role) {
    const actions = [];
    
    // Copy button for all messages
    actions.push(`
        <button class="message-action-btn" data-action="copy" title="Copy message" aria-label="Copy message">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M5.5 4.5H11.5V10.5H5.5V4.5Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M4.5 6.5C4.5 5.94772 4.94772 5.5 5.5 5.5H10.5V10.5C10.5 11.0523 10.0523 11.5 9.5 11.5H5.5C4.94772 11.5 4.5 11.0523 4.5 10.5V6.5Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
        </button>
    `);
    
    // Regenerate button only for assistant messages
    if (role === 'assistant') {
        actions.push(`
            <button class="message-action-btn" data-action="regenerate" title="Regenerate response" aria-label="Regenerate response">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M2.5 8C2.5 5.51472 4.51472 3 7 3C8.70668 3 10.2103 3.85331 11 5.16667M13.5 8C13.5 10.4853 11.4853 13 9 13C7.29332 13 5.78967 12.1467 5 10.8333M5 10.8333L2.5 13.3333L5 15.8333M11 5.16667L13.5 2.66667L11 0.166667" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </button>
        `);

        // Share button for assistant messages (Beta feature)
        if (isBetaFeatureEnabled('shared_chats')) {
            actions.push(`
                <button class="message-action-btn" data-action="share" title="Share this response" aria-label="Share this response">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <path d="M12 3.5C12 2.67157 11.3284 2 10.5 2C9.67157 2 9 2.67157 9 3.5C9 4.32843 9.67157 5 10.5 5C11.3284 5 12 4.32843 12 3.5Z" stroke="currentColor" stroke-width="1.5"/>
                        <path d="M7 8C7 7.17157 6.32843 6.5 5.5 6.5C4.67157 6.5 4 7.17157 4 8C4 8.82843 4.67157 9.5 5.5 9.5C6.32843 9.5 7 8.82843 7 8Z" stroke="currentColor" stroke-width="1.5"/>
                        <path d="M12 12.5C12 11.6716 11.3284 11 10.5 11C9.67157 11 9 11.6716 9 12.5C9 13.3284 9.67157 14 10.5 14C11.3284 14 12 13.3284 12 12.5Z" stroke="currentColor" stroke-width="1.5"/>
                        <path d="M9.5 5.5L6.5 7.5M9.5 10.5L6.5 8.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                    </svg>
                </button>
            `);
        }

        // Summary button for assistant messages (Beta feature)
        if (isBetaFeatureEnabled('smart_summaries')) {
            actions.push(`
                <button class="message-action-btn" data-action="summarize" title="Summarize conversation" aria-label="Summarize conversation">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <path d="M4 6H12M4 8H10M4 10H8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                        <path d="M2 4H14V12H2V4Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </button>
            `);
        }

        actions.push(`
            <button class="message-action-btn" data-action="like" title="Like this response" aria-label="Like this response">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M8 13.3333L3.33333 8.66667C2.6 7.93333 2.13333 7 2.13333 6C2.13333 3.73333 3.86667 2 6.13333 2C6.93333 2 7.73333 2.26667 8.4 2.73333L8 3.13333L7.6 2.73333C8.26667 2.26667 9.06667 2 9.86667 2C12.1333 2 13.8667 3.73333 13.8667 6C13.8667 7 13.4 7.93333 12.6667 8.66667L8 13.3333Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </button>
        `);
    }
    
    // Delete button only for user messages
    if (role === 'user') {
        actions.push(`
            <button class="message-action-btn" data-action="delete" title="Delete message" aria-label="Delete message">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M4 4L12 12M12 4L4 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
            </button>
        `);
    }
    
    return `<div class="message-actions">${actions.join('')}</div>`;
}

function createMessageStatusHTML(status = 'sent') {
    if (!status || status === 'sent') {
        return '<div class="message-status sent"></div>';
    }
    return `<div class="message-status ${status}"></div>`;
}

function formatTimestamp(timestamp) {
    if (!timestamp) return '';
    
    const date = new Date(timestamp);
    if (isNaN(date.getTime())) return '';
    
    const now = new Date();
    const diffMs = now - date;
    const diffSecs = Math.floor(diffMs / 1000);
    const diffMins = Math.floor(diffSecs / 60);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffSecs < 60) {
        return 'Just now';
    } else if (diffMins < 60) {
        return `${diffMins} minute${diffMins === 1 ? '' : 's'} ago`;
    } else if (diffHours < 24) {
        return `${diffHours} hour${diffHours === 1 ? '' : 's'} ago`;
    } else if (diffDays < 7) {
        return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`;
    } else {
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
}

function createMessageTimestampHTML(timestamp) {
    if (!timestamp) return '';
    const formatted = formatTimestamp(timestamp);
    const fullDate = timestamp ? new Date(timestamp).toLocaleString() : '';
    return `<div class="message-timestamp" title="${fullDate}">${formatted}</div>`;
}

function updateMessageStatus(messageId, status) {
    const messageDiv = document.getElementById(messageId);
    if (!messageDiv) return;
    
    let statusDiv = messageDiv.querySelector('.message-status');
    if (!statusDiv) {
        messageDiv.insertAdjacentHTML('beforeend', createMessageStatusHTML(status));
    } else {
        statusDiv.className = `message-status ${status}`;
    }
}

function setupMessageActions(messageElement) {
    if (!messageElement) return;
    
    const actionButtons = messageElement.querySelectorAll('.message-action-btn');
    actionButtons.forEach(btn => {
        const action = btn.getAttribute('data-action');
        if (!action) return;
        
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            handleMessageAction(messageElement, action, btn);
        });
    });
    
    // Setup code block copy buttons
    const codeBlockCopyBtns = messageElement.querySelectorAll('.code-block-copy-btn');
    codeBlockCopyBtns.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.stopPropagation();
            const codeId = btn.getAttribute('data-code-id');
            if (codeId && window._codeBlocks && window._codeBlocks[codeId]) {
                const code = window._codeBlocks[codeId];
                try {
                    await navigator.clipboard.writeText(code);
                    btn.setAttribute('title', 'Copied!');
                    setTimeout(() => {
                        btn.setAttribute('title', 'Copy code');
                    }, 2000);
                    showNotification('Code copied to clipboard', 'success', 2000);
                } catch (err) {
                    // Fallback
                    const textArea = document.createElement('textarea');
                    textArea.value = code;
                    textArea.style.position = 'fixed';
                    textArea.style.opacity = '0';
                    document.body.appendChild(textArea);
                    textArea.select();
                    try {
                        document.execCommand('copy');
                        btn.setAttribute('title', 'Copied!');
                        setTimeout(() => {
                            btn.setAttribute('title', 'Copy code');
                        }, 2000);
                        showNotification('Code copied to clipboard', 'success', 2000);
                    } catch (e) {
                        showNotification('Failed to copy code', 'error', 2000);
                    }
                    document.body.removeChild(textArea);
                }
            }
        });
    });
}

function handleMessageAction(messageElement, action, buttonElement) {
    const messageContent = messageElement.querySelector('.message-content');
    if (!messageContent) return;
    
    const role = messageElement.classList.contains('user') ? 'user' : 'assistant';
    const messageId = messageElement.id;
    const content = messageContent.textContent || messageContent.innerText;
    
    switch (action) {
        case 'copy':
            copyMessageToClipboard(content);
            break;
        case 'regenerate':
            if (role === 'assistant') {
                regenerateMessage(messageId);
            }
            break;
        case 'like':
            toggleMessageLike(messageElement, buttonElement);
            break;
        case 'share':
            if (role === 'assistant') {
                shareMessage(messageElement);
            }
            break;
        case 'summarize':
            if (role === 'assistant') {
                summarizeChat(currentChatId);
            }
            break;
        case 'delete':
            if (role === 'user') {
                deleteMessage(messageElement);
            }
            break;
    }
}

async function shareMessage(messageElement) {
    try {
        const response = await fetch(`/api/beta/shared-chats/${currentChatId}/share`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Beta-Mode': 'true'
            }
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to share chat');
        }

        const data = await response.json();

        // Copy share URL to clipboard
        await navigator.clipboard.writeText(data.share_url);

        // Show success notification
        showNotification(`Chat shared! Link copied to clipboard.`, 'success', 3000);

        // Update button to indicate success
        const shareBtn = messageElement.querySelector('[data-action="share"]');
        if (shareBtn) {
            const originalTitle = shareBtn.title;
            shareBtn.title = 'Link copied!';
            shareBtn.style.color = 'var(--accent-primary)';

            setTimeout(() => {
                shareBtn.title = originalTitle;
                shareBtn.style.color = '';
            }, 2000);
        }

    } catch (error) {
        console.error('[Beta] Error sharing message:', error);
        showNotification(`Failed to share chat: ${error.message}`, 'error', 5000);
    }
}

async function summarizeChat(chatId) {
    if (!chatId) {
        showNotification('No chat to summarize', 'error', 3000);
        return;
    }

    try {
        // Show format selection modal
        const format = await showSummaryFormatModal();
        if (!format) return;

        const response = await fetch(`/api/beta/summarize/${chatId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Beta-Mode': 'true'
            },
            body: JSON.stringify({ format })
        });

        if (!response.ok) {
            throw new Error('Failed to summarize chat');
        }

        const data = await response.json();

        // Create and display summary in a new message
        const summaryMessage = {
            role: 'assistant',
            content: `## Chat Summary\n\n${data.summary}`,
            timestamp: new Date().toISOString(),
            id: `summary_${Date.now()}`
        };

        // Add the summary message to the chat
        addMessageToChat(summaryMessage, true);
        scrollToBottom(true);

        showNotification('Chat summarized successfully', 'success', 3000);

    } catch (error) {
        console.error('[Beta] Error summarizing chat:', error);
        showNotification(`Failed to summarize chat: ${error.message}`, 'error', 5000);
    }
}

function showSummaryFormatModal() {
    return new Promise((resolve) => {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.id = 'summaryFormatModal';
        modal.style.display = 'flex';
        modal.innerHTML = `
            <div class="modal-content glass-card" style="max-width: 400px;">
                <div class="modal-header">
                    <h2>Choose Summary Format</h2>
                    <button class="modal-close" id="closeSummaryFormatModal">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label for="summaryFormat">Format</label>
                        <select id="summaryFormat" class="form-select">
                            <option value="paragraph">Paragraph</option>
                            <option value="bullet_points">Bullet Points</option>
                            <option value="key_insights">Key Insights</option>
                        </select>
                        <p class="input-disclaimer" style="text-align:left; margin-top:8px;">
                            Choose how you want the chat summary to be formatted.
                        </p>
                    </div>
                    <div class="form-actions">
                        <button type="button" class="btn-secondary" id="cancelSummary">Cancel</button>
                        <button type="button" class="btn-primary" id="confirmSummary">Generate Summary</button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        const closeModal = () => {
            modal.remove();
            resolve(null);
        };

        document.getElementById('closeSummaryFormatModal').addEventListener('click', closeModal);
        document.getElementById('cancelSummary').addEventListener('click', closeModal);

        document.getElementById('confirmSummary').addEventListener('click', () => {
            const format = document.getElementById('summaryFormat').value;
            modal.remove();
            resolve(format);
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });
    });
}

async function copyMessageToClipboard(content) {
    try {
        await navigator.clipboard.writeText(content);
        showNotification('Message copied to clipboard', 'success', 2000);
    } catch (err) {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = content;
        textArea.style.position = 'fixed';
        textArea.style.opacity = '0';
        document.body.appendChild(textArea);
        textArea.select();
        try {
            document.execCommand('copy');
            showNotification('Message copied to clipboard', 'success', 2000);
        } catch (e) {
            showNotification('Failed to copy message', 'error', 2000);
        }
        document.body.removeChild(textArea);
    }
}

function regenerateMessage(messageId) {
    // Find the user message that preceded this assistant message
    const messageElement = document.getElementById(messageId);
    if (!messageElement) return;
    
    // Find previous user message
    let previousMessage = messageElement.previousElementSibling;
    while (previousMessage && !previousMessage.classList.contains('message')) {
        previousMessage = previousMessage.previousElementSibling;
    }
    
    if (!previousMessage || !previousMessage.classList.contains('user')) {
        showNotification('Could not find original message to regenerate', 'error', 2000);
        return;
    }
    
    const userContent = previousMessage.querySelector('.message-content');
    if (!userContent) return;
    
    const userMessage = userContent.textContent || userContent.innerText;
    
    // Remove the current assistant message and all messages after it
    let nextSibling = messageElement.nextElementSibling;
    while (nextSibling) {
        const toRemove = nextSibling;
        nextSibling = nextSibling.nextElementSibling;
        toRemove.remove();
    }
    messageElement.remove();
    
    // Resend the message
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.value = userMessage;
        autoResizeTextarea(messageInput);
        handleSendMessage();
    }
}

function toggleMessageLike(messageElement, buttonElement) {
    const isLiked = buttonElement.classList.contains('liked');
    
    if (isLiked) {
        buttonElement.classList.remove('liked');
        buttonElement.setAttribute('title', 'Like this response');
        buttonElement.querySelector('svg path').setAttribute('fill', 'none');
    } else {
        buttonElement.classList.add('liked');
        buttonElement.setAttribute('title', 'Unlike this response');
        buttonElement.querySelector('svg path').setAttribute('fill', 'currentColor');
        showNotification('Response liked', 'success', 2000);
    }
}

function deleteMessage(messageElement) {
    if (!confirm('Delete this message?')) return;
    
    messageElement.style.animation = 'fadeOut 0.3s ease';
    setTimeout(() => {
        messageElement.remove();
        showNotification('Message deleted', 'success', 2000);
    }, 300);
}

function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
        success: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M16.6667 5L7.50004 14.1667L3.33337 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
        error: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M10 18.3333C14.6024 18.3333 18.3333 14.6024 18.3333 10C18.3333 5.39763 14.6024 1.66667 10 1.66667C5.39763 1.66667 1.66667 5.39763 1.66667 10C1.66667 14.6024 5.39763 18.3333 10 18.3333Z" stroke="currentColor" stroke-width="1.5"/><path d="M10 6.66667V10M10 13.3333H10.0083" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>',
        info: '<svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M10 18.3333C14.6024 18.3333 18.3333 14.6024 18.3333 10C18.3333 5.39763 14.6024 1.66667 10 1.66667C5.39763 1.66667 1.66667 5.39763 1.66667 10C1.66667 14.6024 5.39763 18.3333 10 18.3333Z" stroke="currentColor" stroke-width="1.5"/><path d="M10 6.66667V10M10 13.3333H10.0083" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>'
    };
    
    toast.innerHTML = `
        <div class="toast-icon">${icons[type] || icons.info}</div>
        <div class="toast-message">${escapeHtml(message)}</div>
        <button class="toast-close" aria-label="Close">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M4 4L12 12M12 4L4 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
        </button>
    `;
    
    toastContainer.appendChild(toast);
    
    // Trigger animation
    requestAnimationFrame(() => {
        toast.classList.add('show');
    });
    
    // Close button handler
    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', () => {
        closeToast(toast);
    });
    
    // Auto-remove after 4 seconds
    setTimeout(() => {
        closeToast(toast);
    }, 4000);
}

function closeToast(toast) {
    toast.classList.remove('show');
    setTimeout(() => {
        if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }, 300);
}

// Add fadeOut animation for message deletion
if (!document.getElementById('messageActionsStyles')) {
    const style = document.createElement('style');
    style.id = 'messageActionsStyles';
    style.textContent = `
        @keyframes fadeOut {
            from {
                opacity: 1;
                transform: translateY(0);
            }
            to {
                opacity: 0;
                transform: translateY(-10px);
            }
        }
    `;
    document.head.appendChild(style);
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
    
    // Restore code blocks with syntax highlighting class and copy button
    const codeBlockWrappers = [];
    html = html.replace(/__CODE_BLOCK_START__(\w+)__CODE_SEP__([\s\S]*?)__CODE_BLOCK_END__/g, 
        (match, lang, code) => {
            const codeId = `code-block-${codeBlockWrappers.length}`;
            codeBlockWrappers.push({ id: codeId, code: code });
            return `<div class="code-block-wrapper" data-code-id="${codeId}"><pre class="code-block md-code-block"><code class="language-${lang}">${escapeHtml(code)}</code></pre><button class="code-block-copy-btn" title="Copy code" aria-label="Copy code" data-code-id="${codeId}"><svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M5.5 4.5H11.5V10.5H5.5V4.5Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M4.5 6.5C4.5 5.94772 4.94772 5.5 5.5 5.5H10.5V10.5C10.5 11.0523 10.0523 11.5 9.5 11.5H5.5C4.94772 11.5 4.5 11.0523 4.5 10.5V6.5Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg></button></div>`;
        });
    
    // Store code blocks for copy functionality
    if (codeBlockWrappers.length > 0) {
        window._codeBlocks = window._codeBlocks || {};
        codeBlockWrappers.forEach(wrapper => {
            window._codeBlocks[wrapper.id] = wrapper.code;
        });
    }
    
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

async function handleDeleteAllChats() {
    if (!confirm('Are you absolutely sure you want to delete ALL chats? This action cannot be undone.')) {
        return;
    }
    
    const originalContent = this.innerHTML;
    this.disabled = true;
    this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Deleting...';
    
    try {
        const response = await fetch('/api/chats', {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('All chats deleted successfully', 'success');
            startNewChat();
            loadChats();
            closeSettingsModalFunc();
        } else {
            const data = await response.json();
            alert(data.error || 'Error deleting all chats');
        }
    } catch (error) {
        console.error('Error deleting all chats:', error);
        alert('Error deleting all chats');
    } finally {
        this.disabled = false;
        this.innerHTML = originalContent;
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

function openRecentChatsModal() {
    const modal = document.getElementById('recentChatsModal');
    if (modal) {
        modal.style.display = 'flex';
        // Refresh chat list for the gallery view
        loadChats();
        setTimeout(() => {
            trapFocusInModal(modal);
        }, 100);
    }
}

function closeRecentChatsModalFunc() {
    const modal = document.getElementById('recentChatsModal');
    if (modal) {
        modal.style.display = 'none';
        releaseFocusFromModal();
    }
}

function openEmbeddedAppModal(url, title = 'App') {
    const modal = document.getElementById('embeddedAppModal');
    const frame = document.getElementById('embeddedAppFrame');
    const titleEl = document.getElementById('embeddedAppTitle');
    const openLink = document.getElementById('embeddedAppOpenLink');
    const fallback = document.getElementById('embeddedAppFallback');

    if (!modal || !frame || !titleEl || !openLink) return;
    if (!url) return;

    titleEl.textContent = title;
    openLink.href = url;

    // Reset fallback + load
    if (fallback) fallback.style.display = 'none';
    modal.style.display = 'flex';

    // Clear any previous handlers and reset frame
    frame.onload = null;
    frame.onerror = null;
    frame.src = 'about:blank'; // Clear previous content first

    // If the app blocks iframe embedding, browsers typically prevent rendering; we can't
    // reliably detect X-Frame-Options, but we can show a helper only if the frame doesn't load.
    let loaded = false;
    let loadTimeout = null;
    
    // Set onload handler BEFORE setting src to avoid race conditions
    frame.onload = () => {
        loaded = true;
        if (loadTimeout) {
            clearTimeout(loadTimeout);
            loadTimeout = null;
        }
        if (fallback) fallback.style.display = 'none';
    };
    
    // Note: onerror rarely fires for iframes due to cross-origin restrictions
    // We rely on timeout detection instead

    // Set src after handlers are attached
    frame.src = url;
    
    // Use a longer, more conservative timeout
    // CORS errors when checking iframe content are EXPECTED and NORMAL for cross-origin sites
    // Don't treat CORS errors as failures - they indicate the iframe is loading fine
    loadTimeout = setTimeout(() => {
        if (!loaded && modal.style.display === 'flex' && fallback) {
            // Try to detect if iframe is actually blocked vs just slow to load
            try {
                // Check if we can access the iframe (CORS will block this for cross-origin, which is normal)
                const frameDoc = frame.contentDocument || frame.contentWindow?.document;
                // If we can access the document, check if it has content
                if (frameDoc && frameDoc.body && frameDoc.body.children.length > 0) {
                    // Frame has content - it loaded successfully
                    loaded = true;
                    if (fallback) fallback.style.display = 'none';
                    return;
                }
            } catch (e) {
                // CORS error is EXPECTED and NORMAL for cross-origin iframes
                // This means the iframe is likely loading fine, just can't access it due to security
                // Don't show error for CORS - assume success unless proven otherwise
                // Give it even more time before showing error (sites may load slowly)
                setTimeout(() => {
                    // Final check after extended timeout - only show error if absolutely certain
                    if (!loaded && modal.style.display === 'flex' && fallback) {
                        // Very conservative - only show if modal is still open and definitely not loaded
                        fallback.style.display = 'grid';
                    }
                }, 5000); // Additional 5 seconds for slow-loading sites
                return;
            }
            
            // If we got here and can access the frame but it's empty, it might be blocked
            // But be conservative - give it more time as some sites load very slowly
            setTimeout(() => {
                if (!loaded && modal.style.display === 'flex' && fallback) {
                    fallback.style.display = 'grid';
                }
            }, 3000);
        }
    }, 4000); // Increased to 4 seconds to account for slower-loading sites
}

function closeEmbeddedAppModalFunc() {
    const modal = document.getElementById('embeddedAppModal');
    const frame = document.getElementById('embeddedAppFrame');
    const fallback = document.getElementById('embeddedAppFallback');

    if (modal) modal.style.display = 'none';
    if (frame) {
        frame.onload = null;
        frame.src = '';
    }
    if (fallback) fallback.style.display = 'none';
}

async function openTemplatesModal() {
    const modal = document.getElementById('templatesModal');
    if (!modal) return;

    modal.style.display = 'flex';
    await loadTemplates();
}

function closeTemplatesModalFunc() {
    const modal = document.getElementById('templatesModal');
    if (modal) modal.style.display = 'none';
}

async function loadTemplates() {
    const grid = document.getElementById('templatesGrid');
    if (!grid) return;

    try {
        const response = await fetch('/api/beta/templates', {
            headers: { 'X-Beta-Mode': 'true' }
        });

        if (!response.ok) {
            throw new Error('Failed to load templates');
        }

        const data = await response.json();
        renderTemplates(data.templates);

    } catch (error) {
        console.error('[Beta] Error loading templates:', error);
        grid.innerHTML = '<div class="error-message">Failed to load templates</div>';
    }
}

function renderTemplates(templates) {
    const grid = document.getElementById('templatesGrid');
    if (!grid) return;

    if (!templates || templates.length === 0) {
        grid.innerHTML = '<div class="empty-state">No templates yet. Create your first template!</div>';
        return;
    }

    const html = templates.map(template => `
        <div class="template-card" data-template-id="${template.id}">
            <div class="template-header">
                <h3 class="template-name">${template.name}</h3>
                <span class="template-usage">Used ${template.usage_count || 0} times</span>
            </div>
            <p class="template-description">${template.description || 'No description'}</p>
            <div class="template-actions">
                <button class="btn-secondary template-use-btn" data-template-id="${template.id}">Use Template</button>
                <button class="btn-danger template-delete-btn" data-template-id="${template.id}">Delete</button>
            </div>
        </div>
    `).join('');

    grid.innerHTML = html;

    // Add event listeners
    grid.querySelectorAll('.template-use-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const templateId = e.target.getAttribute('data-template-id');
            useTemplate(templateId);
        });
    });

    grid.querySelectorAll('.template-delete-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const templateId = e.target.getAttribute('data-template-id');
            deleteTemplate(templateId);
        });
    });
}

async function useTemplate(templateId) {
    try {
        const response = await fetch(`/api/beta/templates/${templateId}/use`, {
            method: 'POST',
            headers: { 'X-Beta-Mode': 'true' }
        });

        if (!response.ok) {
            throw new Error('Failed to use template');
        }

        const data = await response.json();

        // Close modal
        closeTemplatesModalFunc();

        // Start new chat with template
        currentChatId = data.chat_id;
        loadChat(data.chat_id);

        showNotification(`Started chat from "${data.name}" template`, 'success', 3000);

    } catch (error) {
        console.error('[Beta] Error using template:', error);
        showNotification(`Failed to use template: ${error.message}`, 'error', 5000);
    }
}

async function deleteTemplate(templateId) {
    if (!confirm('Are you sure you want to delete this template?')) return;

    try {
        const response = await fetch(`/api/beta/templates/${templateId}`, {
            method: 'DELETE',
            headers: { 'X-Beta-Mode': 'true' }
        });

        if (!response.ok) {
            throw new Error('Failed to delete template');
        }

        // Reload templates
        await loadTemplates();
        showNotification('Template deleted', 'success', 3000);

    } catch (error) {
        console.error('[Beta] Error deleting template:', error);
        showNotification(`Failed to delete template: ${error.message}`, 'error', 5000);
    }
}

async function openTasksPanel() {
    const panel = document.getElementById('tasksPanel');
    if (!panel) return;

    panel.style.display = 'block';
    await loadTasks();
}

function closeTasksPanel() {
    const panel = document.getElementById('tasksPanel');
    if (panel) panel.style.display = 'none';
}

async function loadTasks() {
    const list = document.getElementById('tasksList');
    if (!list) return;

    try {
        const response = await fetch(`/api/beta/tasks?chat_id=${currentChatId || ''}`, {
            headers: { 'X-Beta-Mode': 'true' }
        });

        if (!response.ok) {
            throw new Error('Failed to load tasks');
        }

        const data = await response.json();
        renderTasks(data.tasks);

    } catch (error) {
        console.error('[Beta] Error loading tasks:', error);
        list.innerHTML = '<div class="error-message">Failed to load tasks</div>';
    }
}

function renderTasks(tasks) {
    const list = document.getElementById('tasksList');
    if (!list) return;

    if (!tasks || tasks.length === 0) {
        list.innerHTML = '<div class="empty-state">No tasks found. Click "Extract from Chat" to analyze the current conversation.</div>';
        return;
    }

    const html = tasks.map(task => `
        <div class="task-item ${task.status}" data-task-id="${task.id}">
            <div class="task-content">
                <div class="task-text">${task.text}</div>
                <div class="task-meta">
                    <span class="task-confidence">Confidence: ${Math.round(task.confidence * 100)}%</span>
                    <span class="task-date">${new Date(task.created_at).toLocaleDateString()}</span>
                </div>
            </div>
            <div class="task-actions">
                <select class="task-status-select" onchange="updateTaskStatus('${task.id}', this.value)">
                    <option value="pending" ${task.status === 'pending' ? 'selected' : ''}>Pending</option>
                    <option value="in_progress" ${task.status === 'in_progress' ? 'selected' : ''}>In Progress</option>
                    <option value="completed" ${task.status === 'completed' ? 'selected' : ''}>Completed</option>
                    <option value="cancelled" ${task.status === 'cancelled' ? 'selected' : ''}>Cancelled</option>
                </select>
            </div>
        </div>
    `).join('');

    list.innerHTML = html;
}

async function extractTasksFromCurrentChat() {
    if (!currentChatId) {
        showNotification('No active chat to extract tasks from', 'error', 3000);
        return;
    }

    try {
        const response = await fetch(`/api/beta/tasks/extract/${currentChatId}`, {
            method: 'POST',
            headers: { 'X-Beta-Mode': 'true' }
        });

        if (!response.ok) {
            throw new Error('Failed to extract tasks');
        }

        const data = await response.json();
        await loadTasks(); // Refresh the tasks list

        showNotification(`Extracted ${data.count} tasks from chat`, 'success', 3000);

    } catch (error) {
        console.error('[Beta] Error extracting tasks:', error);
        showNotification(`Failed to extract tasks: ${error.message}`, 'error', 5000);
    }
}

async function updateTaskStatus(taskId, status) {
    try {
        const response = await fetch(`/api/beta/tasks/${taskId}/status?chat_id=${currentChatId || ''}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-Beta-Mode': 'true'
            },
            body: JSON.stringify({ status })
        });

        if (!response.ok) {
            throw new Error('Failed to update task status');
        }

        showNotification('Task status updated', 'success', 2000);

    } catch (error) {
        console.error('[Beta] Error updating task status:', error);
        showNotification(`Failed to update task: ${error.message}`, 'error', 3000);
    }
}

async function openGlobalSearchModal() {
    if (!isBetaFeatureEnabled('global_search')) {
        showNotification('Global search requires beta mode', 'error', 3000);
        return;
    }

    const modal = document.getElementById('globalSearchModal');
    if (!modal) return;

    modal.style.display = 'flex';

    // Focus search input
    setTimeout(() => {
        const searchInput = document.getElementById('globalSearchInput');
        if (searchInput) {
            searchInput.focus();
            searchInput.value = '';
            document.getElementById('searchResults').innerHTML = '<div class="search-loading">Enter a search term to begin...</div>';
        }
    }, 100);

    // Set up search input handlers
    const searchInput = document.getElementById('globalSearchInput');
    const searchTypeFilter = document.getElementById('searchTypeFilter');

    if (searchInput) {
        // Debounced search
        let searchTimeout;
        searchInput.addEventListener('input', (e) => {
            clearTimeout(searchTimeout);
            const query = e.target.value.trim();

            if (query.length < 2) {
                document.getElementById('searchResults').innerHTML = '<div class="search-loading">Enter at least 2 characters to search...</div>';
                return;
            }

            searchTimeout = setTimeout(() => {
                performGlobalSearch(query, searchTypeFilter.value);
            }, 300);
        });
    }

    if (searchTypeFilter) {
        searchTypeFilter.addEventListener('change', () => {
            const query = searchInput.value.trim();
            if (query.length >= 2) {
                performGlobalSearch(query, searchTypeFilter.value);
            }
        });
    }
}

function closeGlobalSearchModal() {
    const modal = document.getElementById('globalSearchModal');
    if (modal) modal.style.display = 'none';
}

async function performGlobalSearch(query, searchType) {
    const resultsContainer = document.getElementById('searchResults');
    if (!resultsContainer) return;

    resultsContainer.innerHTML = '<div class="search-loading">Searching...</div>';

    try {
        const response = await fetch(`/api/beta/search?q=${encodeURIComponent(query)}&type=${searchType}&limit=20`, {
            headers: { 'X-Beta-Mode': 'true' }
        });

        if (!response.ok) {
            throw new Error('Search failed');
        }

        const data = await response.json();
        renderSearchResults(data);

    } catch (error) {
        console.error('[Beta] Error performing global search:', error);
        resultsContainer.innerHTML = '<div class="error-message">Failed to perform search</div>';
    }
}

function renderSearchResults(data) {
    const resultsContainer = document.getElementById('searchResults');
    if (!resultsContainer) return;

    if (data.total_results === 0) {
        resultsContainer.innerHTML = '<div class="search-empty">No results found</div>';
        return;
    }

    let html = `<div class="search-summary">Found ${data.total_results} results for "${data.query}"</div>`;

    // Render chats results
    if (data.chats && data.chats.length > 0) {
        html += '<div class="search-section">';
        html += '<h4>Chats</h4>';
        data.chats.forEach(chat => {
            html += `
                <div class="search-item" onclick="loadChat('${chat.chat_id}')">
                    <div class="search-item-header">
                        <span class="search-item-title">${chat.name}</span>
                        <span class="search-item-meta">${chat.message_count} messages</span>
                    </div>
                    <div class="search-item-content">
                        ${chat.message_matches ? chat.message_matches.map(match =>
                            `<div class="search-match">${match.content.substring(0, 100)}...</div>`
                        ).join('') : ''}
                    </div>
                </div>
            `;
        });
        html += '</div>';
    }

    // Render projects results
    if (data.projects && data.projects.length > 0) {
        html += '<div class="search-section">';
        html += '<h4>Projects</h4>';
        data.projects.forEach(project => {
            html += `
                <div class="search-item" onclick="openProjectModal('${project.project_id}')">
                    <div class="search-item-header">
                        <span class="search-item-title">${project.name}</span>
                        <span class="search-item-meta">${project.chat_count} chats</span>
                    </div>
                    <div class="search-item-content">${project.description}</div>
                </div>
            `;
        });
        html += '</div>';
    }

    // Render gems results
    if (data.gems && data.gems.length > 0) {
        html += '<div class="search-section">';
        html += '<h4>Gems</h4>';
        data.gems.forEach(gem => {
            html += `
                <div class="search-item" onclick="selectGem('${gem.gem_id}')">
                    <div class="search-item-header">
                        <span class="search-item-title">${gem.name}</span>
                        <span class="search-item-meta">${gem.tone} tone</span>
                    </div>
                    <div class="search-item-content">${gem.description}</div>
                </div>
            `;
        });
        html += '</div>';
    }

    // Render brain results
    if (data.brain && data.brain.length > 0) {
        html += '<div class="search-section">';
        html += '<h4>Knowledge</h4>';
        data.brain.forEach(item => {
            html += `
                <div class="search-item">
                    <div class="search-item-header">
                        <span class="search-item-title">${item.title}</span>
                        <span class="search-item-meta">${item.source}</span>
                    </div>
                    <div class="search-item-content">${item.content}</div>
                </div>
            `;
        });
        html += '</div>';
    }

    resultsContainer.innerHTML = html;

    // Add close modal on item click
    resultsContainer.querySelectorAll('.search-item').forEach(item => {
        item.addEventListener('click', () => {
            closeGlobalSearchModal();
        });
    });
}

async function openAnalyticsModal() {
    if (!isBetaFeatureEnabled('insights_dashboard')) {
        showNotification('Analytics dashboard requires beta mode', 'error', 3000);
        return;
    }

    const modal = document.getElementById('analyticsModal');
    if (!modal) return;

    modal.style.display = 'flex';
    await loadAnalytics();
}

function closeAnalyticsModal() {
    const modal = document.getElementById('analyticsModal');
    if (modal) modal.style.display = 'none';
}

async function loadAnalytics() {
    const dashboard = document.getElementById('analyticsDashboard');
    if (!dashboard) return;

    dashboard.innerHTML = '<div class="analytics-loading">Loading analytics...</div>';

    try {
        const response = await fetch('/api/beta/analytics', {
            headers: { 'X-Beta-Mode': 'true' }
        });

        if (!response.ok) {
            throw new Error('Failed to load analytics');
        }

        const data = await response.json();
        renderAnalytics(data);

    } catch (error) {
        console.error('[Beta] Error loading analytics:', error);
        dashboard.innerHTML = '<div class="error-message">Failed to load analytics</div>';
    }
}

function renderAnalytics(data) {
    const dashboard = document.getElementById('analyticsDashboard');
    if (!dashboard) return;

    const html = `
        <div class="analytics-grid">
            <!-- Overview Stats -->
            <div class="analytics-card">
                <h3>Overview</h3>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value">${data.total_chats}</div>
                        <div class="stat-label">Total Chats</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${data.total_messages}</div>
                        <div class="stat-label">Total Messages</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${data.total_projects}</div>
                        <div class="stat-label">Projects</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value">${data.total_gems}</div>
                        <div class="stat-label">Gems</div>
                    </div>
                </div>
            </div>

            <!-- Beta Features Usage -->
            <div class="analytics-card">
                <h3>Beta Features Usage</h3>
                <div class="beta-usage-grid">
                    <div class="usage-item">
                        <span>Shared Chats</span>
                        <span class="usage-count">${data.beta_features_usage.shared_chats}</span>
                    </div>
                    <div class="usage-item">
                        <span>Templates</span>
                        <span class="usage-count">${data.beta_features_usage.templates}</span>
                    </div>
                    <div class="usage-item">
                        <span>Tasks</span>
                        <span class="usage-count">${data.beta_features_usage.tasks}</span>
                    </div>
                    <div class="usage-item">
                        <span>Snippets</span>
                        <span class="usage-count">${data.beta_features_usage.snippets}</span>
                    </div>
                    <div class="usage-item">
                        <span>Workflows</span>
                        <span class="usage-count">${data.beta_features_usage.workflows}</span>
                    </div>
                </div>
            </div>

            <!-- Top Topics -->
            <div class="analytics-card">
                <h3>Top Topics</h3>
                <div class="topics-list">
                    ${data.top_topics.slice(0, 8).map(topic => `
                        <div class="topic-item">
                            <span class="topic-name">${topic.topic}</span>
                            <span class="topic-count">${topic.count}</span>
                        </div>
                    `).join('')}
                </div>
            </div>

            <!-- Recent Activity -->
            <div class="analytics-card">
                <h3>Recent Activity</h3>
                <div class="activity-list">
                    ${data.recent_activity.slice(0, 5).map(activity => `
                        <div class="activity-item">
                            <div class="activity-name">${activity.name}</div>
                            <div class="activity-meta">${activity.message_count} messages • ${new Date(activity.created_at).toLocaleDateString()}</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;

    dashboard.innerHTML = html;
}

async function openModelComparison() {
    if (!isBetaFeatureEnabled('multi_model_comparison')) {
        showNotification('Multi-model comparison requires beta mode', 'error', 3000);
        return;
    }

    // Show model selection modal
    const selectedModels = await showModelSelectionModal();
    if (!selectedModels || selectedModels.length < 2) return;

    comparisonMode = true;

    // Show loading state
    showNotification('Comparing models...', 'info', 2000);

    // Modify next message to use comparison
    // This will be handled in handleSendMessage
    showNotification('Click send to compare selected models', 'success', 3000);
}

function showModelSelectionModal() {
    return new Promise((resolve) => {
        const modal = document.createElement('div');
        modal.className = 'modal';
        modal.id = 'modelSelectionModal';
        modal.style.display = 'flex';
        modal.innerHTML = `
            <div class="modal-content glass-card" style="max-width: 400px;">
                <div class="modal-header">
                    <h2>Select Models to Compare</h2>
                    <button class="modal-close" id="closeModelSelectionModal">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <p style="margin-bottom: 16px; color: var(--text-secondary);">
                            Select 2-3 models to compare their responses:
                        </p>
                        <div class="model-selection-list">
                            <label class="model-selection-item">
                                <input type="checkbox" value="thor-1.2" checked>
                                <span>Thor 1.2 (Default)</span>
                            </label>
                            <label class="model-selection-item">
                                <input type="checkbox" value="thor-1.1">
                                <span>Thor 1.1 (Latest)</span>
                            </label>
                            <label class="model-selection-item">
                                <input type="checkbox" value="thor-1.0">
                                <span>Thor 1.0 (Stable)</span>
                            </label>
                        </div>
                        <p class="input-disclaimer" style="text-align:left; margin-top:12px;">
                            Note: Only Thor models are supported for comparison currently.
                        </p>
                    </div>
                    <div class="form-actions">
                        <button type="button" class="btn-secondary" id="cancelModelSelection">Cancel</button>
                        <button type="button" class="btn-primary" id="confirmModelSelection">Compare Models</button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        const closeModal = () => {
            modal.remove();
            resolve(null);
        };

        document.getElementById('closeModelSelectionModal').addEventListener('click', closeModal);
        document.getElementById('cancelModelSelection').addEventListener('click', closeModal);

        document.getElementById('confirmModelSelection').addEventListener('click', () => {
            const selected = Array.from(modal.querySelectorAll('input[type="checkbox"]:checked'))
                .map(cb => cb.value);
            modal.remove();
            resolve(selected);
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });
    });
}

function toggleOutputFormatDropdown(e) {
    e.stopPropagation();
    const selector = document.getElementById('outputFormatSelector');
    const dropdown = document.getElementById('outputFormatDropdown');

    if (selector.classList.contains('active')) {
        selector.classList.remove('active');
    } else {
        // Close other dropdowns
        document.querySelectorAll('.output-format-selector.active').forEach(s => {
            if (s !== selector) s.classList.remove('active');
        });
        selector.classList.add('active');
    }
}

function setOutputFormat(format) {
    currentOutputFormat = format;
    const selector = document.getElementById('outputFormatSelector');
    const label = selector.querySelector('.output-format-label');

    const formatNames = {
        '': 'Text',
        'json': 'JSON',
        'table': 'Table',
        'csv': 'CSV'
    };

    label.textContent = formatNames[format] || 'Text';

    // Update active state
    const options = selector.querySelectorAll('.output-format-option');
    options.forEach(option => {
        option.classList.toggle('active', option.getAttribute('data-format') === format);
    });

    selector.classList.remove('active');

    if (format) {
        showNotification(`Output format set to ${formatNames[format]}`, 'success', 2000);
    }
}

// Close dropdowns when clicking outside
document.addEventListener('click', (e) => {
    if (!e.target.closest('.output-format-selector')) {
        document.querySelectorAll('.output-format-selector.active').forEach(s => {
            s.classList.remove('active');
        });
    }
});

function handleComparisonResponse(data, userMessageId, loadingId) {
    // Update user message status
    updateMessageStatus(userMessageId, 'sent');

    // Remove loading message
    const loadingMessage = document.getElementById(loadingId);
    if (loadingMessage) {
        loadingMessage.remove();
    }

    // Create comparison modal
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.id = 'comparisonModal';
    modal.style.display = 'flex';
    modal.innerHTML = `
        <div class="modal-content glass-card">
            <div class="modal-header">
                <h2>Model Comparison <span class="beta-badge">BETA</span></h2>
                <button class="modal-close" id="closeComparisonModal">&times;</button>
            </div>
            <div class="modal-body">
                <div class="comparison-results">
                    ${data.results.map(result => `
                        <div class="comparison-item">
                            <div class="comparison-header">
                                <div class="comparison-model">${result.model}</div>
                                <div class="comparison-meta">
                                    ${result.length ? `${result.length} chars` : ''}
                                    ${result.timestamp ? new Date(result.timestamp).toLocaleTimeString() : ''}
                                </div>
                            </div>
                            <div class="comparison-response">
                                ${result.error ?
                                    `<span class="comparison-error">${result.error}</span>` :
                                    result.response
                                }
                            </div>
                        </div>
                    `).join('')}
                </div>
                <div class="form-actions" style="margin-top: 20px;">
                    <button type="button" class="btn-primary" id="selectBestResponse">Use Best Response</button>
                    <button type="button" class="btn-secondary" id="closeComparison">Close</button>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // Event listeners
    document.getElementById('closeComparisonModal').addEventListener('click', () => modal.remove());
    document.getElementById('closeComparison').addEventListener('click', () => modal.remove());

    document.getElementById('selectBestResponse').addEventListener('click', () => {
        // Find the best response (longest valid response)
        const bestResult = data.results
            .filter(r => r.response && !r.error)
            .sort((a, b) => (b.length || 0) - (a.length || 0))[0];

        if (bestResult) {
            // Add the best response as a regular message
            const responseMessage = {
                role: 'assistant',
                content: `**Selected from ${bestResult.model}:**\n\n${bestResult.response}`,
                timestamp: new Date().toISOString(),
                id: `comparison_${Date.now()}`
            };

            addMessageToChat(responseMessage, true);
            scrollToBottom(true);
            showNotification(`Used response from ${bestResult.model}`, 'success', 3000);
        }

        modal.remove();
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });

    // Update chat ID
    currentChatId = data.chat_id || currentChatId;

    showNotification(`Compared ${data.results.length} models`, 'success', 3000);
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
        // Re-initialize background customization when settings open
        // This ensures elements exist and settings are properly loaded with event listeners
        setTimeout(() => {
        }, 100);
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

function openUserProfileModal() {
    const modal = document.getElementById('userProfileModal');
    if (modal) {
        modal.style.display = 'flex';
        setTimeout(() => {
            trapFocusInModal(modal);
        }, 100);
    }
}

function closeUserProfileModalFunc() {
    const modal = document.getElementById('userProfileModal');
    if (modal) {
        modal.style.display = 'none';
        releaseFocusFromModal();
    }
}

function openHelpModal() {
    const modal = document.getElementById('helpModal');
    if (modal) {
        modal.style.display = 'flex';
        setTimeout(() => {
            trapFocusInModal(modal);
        }, 100);
    }
}

function closeHelpModalFunc() {
    const modal = document.getElementById('helpModal');
    if (modal) {
        modal.style.display = 'none';
        releaseFocusFromModal();
    }
}

function openCustomizeModal() {
    const modal = document.getElementById('customizeModal');
    if (modal) {
        modal.style.display = 'flex';
        renderGemTryTemplates();
        renderGemsManageList();
        setTimeout(() => {
            trapFocusInModal(modal);
        }, 100);
    }
}

function closeCustomizeModalFunc() {
    const modal = document.getElementById('customizeModal');
    if (modal) {
        modal.style.display = 'none';
        releaseFocusFromModal();
    }
    closeGemEditor();
}

function initializeTheme() {
    // Enhanced Theme System (Phase 4.3)
    const savedTheme = localStorage.getItem('atlasTheme') || 'system';
    themePreference = savedTheme;
    
    // Load custom accent color if set
    const savedAccentColor = localStorage.getItem('atlasAccentColor');
    if (savedAccentColor) {
        setCustomAccentColor(savedAccentColor);
    }
    
    // Load high contrast preference
    const savedHighContrast = localStorage.getItem('atlasHighContrast') === 'true';
    if (savedHighContrast) {
        document.body.setAttribute('data-high-contrast', 'true');
    }
    
    setTheme(savedTheme);
    
    // Enhanced system theme detection (Phase 4.3)
    const systemMedia = window.matchMedia('(prefers-color-scheme: dark)');
    const contrastMedia = window.matchMedia('(prefers-contrast: high)');
    
    // Always listen for system theme changes
    if (systemMedia.addEventListener) {
        systemMedia.addEventListener('change', (e) => {
            // If user preference is 'system', auto-update
            if (themePreference === 'system') {
                setTheme('system');
            }
        });
    } else if (systemMedia.addListener) {
        // Fallback for older browsers
        systemMedia.addListener((e) => {
            if (themePreference === 'system') {
                setTheme('system');
            }
        });
    }
    
    // Auto-enable high contrast if system prefers it
    if (contrastMedia.matches && !savedHighContrast) {
        // Optionally auto-enable, or just show notification
        // For now, we'll just listen for changes
    }
    
    if (contrastMedia.addEventListener) {
        contrastMedia.addEventListener('change', (e) => {
            if (e.matches && themePreference === 'system') {
                // Suggest high contrast mode
                showNotification('High contrast mode detected. Enable in settings?', 'info', 5000);
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
    
    // Initialize accent color picker if it exists
    initializeAccentColorPicker();
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
        if (currentModel === 'thor-1.1' || currentModel === 'thor-1.2' || !currentModel.startsWith('gem:')) {
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
        // Switch to Thor 1.2 in latest mode (unless gem is selected)
        if (currentModel === 'thor-1.0' || (!currentModel.startsWith('gem:') && currentModel !== 'thor-1.1' && currentModel !== 'thor-1.2')) {
            currentModel = 'thor-1.2';
            localStorage.setItem('selectedModel', 'thor-1.2');
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

function initializeBetaMode() {
    // Initialize beta mode toggle in settings
    const betaModeToggle = document.getElementById('betaModeToggle');
    if (betaModeToggle) {
        betaModeToggle.checked = betaModeEnabled;
        betaModeToggle.addEventListener('change', (e) => {
            setBetaModeEnabled(e.target.checked);
            // Show warning modal when enabling beta mode
            if (e.target.checked) {
                showBetaModeWarning();
            }
        });
    }

    // Initialize individual beta feature toggles
    Object.keys(BETA_FEATURE_CATEGORIES).forEach(categoryKey => {
        const category = BETA_FEATURE_CATEGORIES[categoryKey];
        Object.keys(category.features).forEach(featureKey => {
            const toggle = document.getElementById(`betaFeature-${featureKey}`);
            if (toggle) {
                toggle.checked = betaFeatures[featureKey] !== false;
                toggle.disabled = !betaModeEnabled;
                toggle.addEventListener('change', (e) => {
                    setBetaFeatureEnabled(featureKey, e.target.checked);
                });
            }
        });
    });

    updateBetaModeUI();
}

function updateBetaModeUI() {
    // Update UI based on beta mode status
    document.body.setAttribute('data-beta-mode', betaModeEnabled.toString());

    // Update individual feature toggles
    Object.keys(betaFeatures).forEach(featureKey => {
        const toggle = document.getElementById(`betaFeature-${featureKey}`);
        if (toggle) {
            toggle.checked = betaFeatures[featureKey] !== false;
            toggle.disabled = !betaModeEnabled;
        }
    });

    // Update beta sections visibility
    const betaSections = document.querySelectorAll('.beta-settings-section');
    betaSections.forEach(section => {
        if (betaModeEnabled) {
            section.style.display = 'block';
        } else {
            section.style.display = 'none';
        }
    });

    // Update beta badges
    const betaBadges = document.querySelectorAll('.beta-badge');
    betaBadges.forEach(badge => {
        badge.style.display = betaModeEnabled ? 'inline-block' : 'none';
    });

    // Update beta feature buttons
    const betaFeatureBtns = document.querySelectorAll('.beta-feature-btn');
    betaFeatureBtns.forEach(btn => {
        btn.style.display = betaModeEnabled ? 'block' : 'none';
    });
}

function showBetaModeWarning() {
    // Create warning modal for beta mode
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.id = 'betaWarningModal';
    modal.style.display = 'flex';
    modal.innerHTML = `
        <div class="modal-content glass-card" style="max-width: 500px;">
            <div class="modal-header">
                <h2>⚠️ Enable Beta Mode</h2>
                <button class="modal-close" id="closeBetaWarningModal">&times;</button>
            </div>
            <div class="modal-body">
                <div class="settings-section">
                    <p style="color: var(--text-primary); margin-bottom: 16px;">
                        <strong>Warning:</strong> Beta features are experimental and may be unstable.
                        They are provided for testing purposes and may contain bugs or incomplete functionality.
                    </p>
                    <p style="color: var(--text-secondary); font-size: 14px; margin-bottom: 20px;">
                        By enabling beta mode, you acknowledge that:
                    </p>
                    <ul style="color: var(--text-secondary); font-size: 14px; margin-bottom: 20px;">
                        <li>• Features may not work as expected</li>
                        <li>• Your data may be lost or corrupted</li>
                        <li>• Some features may be removed without notice</li>
                        <li>• Performance may be affected</li>
                    </ul>
                    <p style="color: var(--text-secondary); font-size: 14px; margin-bottom: 24px;">
                        <strong>Recommendation:</strong> Only enable beta mode for testing purposes.
                        Keep backups of important data.
                    </p>
                </div>
                <div class="form-actions">
                    <button type="button" class="btn-secondary" id="cancelBetaMode">Cancel</button>
                    <button type="button" class="btn-primary" id="confirmBetaMode">Enable Beta Mode</button>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // Event listeners
    const closeModal = () => {
        modal.remove();
        setBetaModeEnabled(false); // Revert if cancelled
    };

    document.getElementById('closeBetaWarningModal').addEventListener('click', closeModal);
    document.getElementById('cancelBetaMode').addEventListener('click', closeModal);

    document.getElementById('confirmBetaMode').addEventListener('click', () => {
        modal.remove();
        // Beta mode already enabled, just close the warning
    });

    // Close on outside click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });
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
    
    // Apply theme with high contrast support (Phase 4.3)
    const isHighContrast = document.body.getAttribute('data-high-contrast') === 'true';
    let finalTheme = resolved;
    
    if (isHighContrast) {
        finalTheme = resolved === 'dark' ? 'high-contrast-dark' : 'high-contrast-light';
    }
    
    document.body.setAttribute('data-theme', finalTheme);
    localStorage.setItem('atlasTheme', theme);
    updateThemeControls(theme);
}

function resolveSystemTheme() {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return 'dark';
    }
    return 'light';
}

function toggleHighContrast() {
    const isHighContrast = document.body.getAttribute('data-high-contrast') === 'true';
    const newValue = !isHighContrast;
    document.body.setAttribute('data-high-contrast', newValue.toString());
    localStorage.setItem('atlasHighContrast', newValue.toString());
    
    // Reapply theme to get high contrast variant
    setTheme(themePreference);
    
    showNotification(
        newValue ? 'High contrast mode enabled' : 'High contrast mode disabled',
        'success',
        2000
    );
}

function setCustomAccentColor(color) {
    if (!color) return;
    
    // Validate hex color
    const hexRegex = /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/;
    if (!hexRegex.test(color)) {
        console.warn('Invalid accent color:', color);
        return;
    }
    
    // Calculate hover color (darker by 15%)
    const hoverColor = adjustColorBrightness(color, -15);
    
    // Set CSS custom properties
    document.documentElement.style.setProperty('--accent-custom', color);
    document.documentElement.style.setProperty('--accent-custom-hover', hoverColor);
    
    // Optionally apply as primary accent
    const useAsPrimary = localStorage.getItem('atlasUseCustomAccent') === 'true';
    if (useAsPrimary) {
        document.documentElement.style.setProperty('--color-accent-primary', color);
        document.documentElement.style.setProperty('--color-accent-primary-hover', hoverColor);
    }
    
    localStorage.setItem('atlasAccentColor', color);
}

function adjustColorBrightness(hex, percent) {
    // Remove # if present
    hex = hex.replace('#', '');
    
    // Convert to RGB
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    
    // Adjust brightness
    const newR = Math.max(0, Math.min(255, r + (r * percent / 100)));
    const newG = Math.max(0, Math.min(255, g + (g * percent / 100)));
    const newB = Math.max(0, Math.min(255, b + (b * percent / 100)));
    
    // Convert back to hex
    const toHex = (n) => {
        const hex = Math.round(n).toString(16);
        return hex.length === 1 ? '0' + hex : hex;
    };
    
    return `#${toHex(newR)}${toHex(newG)}${toHex(newB)}`;
}

function initializeAccentColorPicker() {
    // Find accent color inputs in settings modal
    const accentColorInput = document.getElementById('accentColorInput');
    const accentColorText = document.getElementById('accentColorText');
    
    if (accentColorInput) {
        const savedColor = localStorage.getItem('atlasAccentColor');
        if (savedColor) {
            accentColorInput.value = savedColor;
            if (accentColorText) accentColorText.value = savedColor;
        }
        
        accentColorInput.addEventListener('input', (e) => {
            const color = e.target.value;
            setCustomAccentColor(color);
            if (accentColorText) accentColorText.value = color;
        });
        
        accentColorInput.addEventListener('change', (e) => {
            setCustomAccentColor(e.target.value);
            showNotification('Accent color updated', 'success', 2000);
        });
    }
    
    if (accentColorText) {
        accentColorText.addEventListener('input', (e) => {
            const color = e.target.value;
            if (color.match(/^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/)) {
                setCustomAccentColor(color);
                if (accentColorInput) accentColorInput.value = color;
            }
        });
        
        accentColorText.addEventListener('blur', (e) => {
            const color = e.target.value;
            if (color.match(/^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/)) {
                setCustomAccentColor(color);
                showNotification('Accent color updated', 'success', 2000);
            } else if (color) {
                showNotification('Invalid color format. Use hex format (e.g., #1a1a1a)', 'error', 3000);
                const savedColor = localStorage.getItem('atlasAccentColor') || '#1a1a1a';
                e.target.value = savedColor;
                if (accentColorInput) accentColorInput.value = savedColor;
            }
        });
    }
    
    // Find "Use as primary" checkbox
    const useAsPrimaryCheckbox = document.getElementById('useCustomAccentAsPrimary');
    if (useAsPrimaryCheckbox) {
        const saved = localStorage.getItem('atlasUseCustomAccent') === 'true';
        useAsPrimaryCheckbox.checked = saved;
        
        useAsPrimaryCheckbox.addEventListener('change', (e) => {
            localStorage.setItem('atlasUseCustomAccent', e.target.checked.toString());
            const savedColor = localStorage.getItem('atlasAccentColor');
            if (savedColor && e.target.checked) {
                setCustomAccentColor(savedColor);
            } else {
                // Reset to default
                document.documentElement.style.removeProperty('--color-accent-primary');
                document.documentElement.style.removeProperty('--color-accent-primary-hover');
            }
            showNotification('Accent color preference updated', 'success', 2000);
        });
    }
    
    // Find high contrast toggle
    const highContrastToggle = document.getElementById('highContrastToggle');
    if (highContrastToggle) {
        const saved = localStorage.getItem('atlasHighContrast') === 'true';
        highContrastToggle.checked = saved;
        
        highContrastToggle.addEventListener('change', (e) => {
            toggleHighContrast();
        });
    }
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
    const recentChatsModal = document.getElementById('recentChatsModal');
    const embeddedAppModal = document.getElementById('embeddedAppModal');
    const userProfileModal = document.getElementById('userProfileModal');
    
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
    if (recentChatsModal && e.target === recentChatsModal) {
        closeRecentChatsModalFunc();
    }
    if (embeddedAppModal && e.target === embeddedAppModal) {
        closeEmbeddedAppModalFunc();
    }
    if (userProfileModal && e.target === userProfileModal) {
        closeUserProfileModalFunc();
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
            currentModel = 'thor-1.2';
            localStorage.setItem('selectedModel', currentModel);
        }

        // Validate saved selection once we know which gems exist
        if (currentModel && currentModel.startsWith('gem:') && currentModel !== 'gem:preview') {
            const id = currentModel.replace(/^gem:/, '');
            const exists = gems.some(g => g.id === id);
            if (!exists) {
                currentModel = 'thor-1.2';
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
    if (!modelId) return 'Thor 1.2';
    if (modelId === 'thor-1.0') return 'Thor 1.0';
    if (modelId === 'thor-1.1') return 'Thor 1.1';
    if (modelId === 'thor-1.2') return 'Thor 1.2';
    if (modelId === 'antelope-1.0') return 'Antelope 1.0';
    if (modelId === 'antelope-1.1') return 'Antelope 1.1';
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

    // Show all available models - Gems are accessible via sidebar
    if (systemMode === 'stable') {
        items.push({ id: 'thor-1.0', name: 'Thor 1.0', note: 'Stable mode' });
    } else {
        items.push({ id: 'thor-1.2', name: 'Thor 1.2', note: 'Default (latest)' });
        items.push({ id: 'thor-1.1', name: 'Thor 1.1', note: 'Latest model' });
        items.push({ id: 'thor-1.0', name: 'Thor 1.0', note: 'Stable version' });
        items.push({ id: 'antelope-1.1', name: 'Antelope 1.1', note: 'Python Specialist' });
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
            currentModel = 'thor-1.2';
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
// Recognition State Machine (v4.1.0)
const RECOGNITION_STATES = {
    IDLE: 'idle',
    STARTING: 'starting',
    LISTENING: 'listening',
    PROCESSING: 'processing',
    STOPPED: 'stopped',
    ERROR: 'error',
    PAUSED: 'paused'
};

const RECOGNITION_TRANSITIONS = {
    [RECOGNITION_STATES.IDLE]: [RECOGNITION_STATES.STARTING],
    [RECOGNITION_STATES.STARTING]: [RECOGNITION_STATES.LISTENING, RECOGNITION_STATES.ERROR],
    [RECOGNITION_STATES.LISTENING]: [RECOGNITION_STATES.PROCESSING, RECOGNITION_STATES.STOPPED, RECOGNITION_STATES.ERROR, RECOGNITION_STATES.PAUSED],
    [RECOGNITION_STATES.PROCESSING]: [RECOGNITION_STATES.LISTENING, RECOGNITION_STATES.STOPPED, RECOGNITION_STATES.ERROR],
    [RECOGNITION_STATES.STOPPED]: [RECOGNITION_STATES.IDLE, RECOGNITION_STATES.STARTING],
    [RECOGNITION_STATES.ERROR]: [RECOGNITION_STATES.IDLE, RECOGNITION_STATES.STARTING],
    [RECOGNITION_STATES.PAUSED]: [RECOGNITION_STATES.LISTENING, RECOGNITION_STATES.STOPPED]
};

let recognitionState = RECOGNITION_STATES.IDLE;
let recognitionStateHistory = []; // Track state transitions for debugging
let recognitionRestartCount = 0; // Track restart attempts to prevent infinite loops
const MAX_RESTART_ATTEMPTS = 10; // Maximum restart attempts before giving up

// Centralized Poseidon State Manager (v4.2.0)
const poseidonStateManager = {
    // Core state
    active: false,
    paused: false,
    initialized: false,

    // Recognition state
    recognition: {
        state: RECOGNITION_STATES.IDLE,
        restartCount: 0,
        lastStartTime: 0,
        transcriptProcessing: false
    },

    // Audio state
    audio: {
        streamActive: false,
        level: 0,
        speechDetected: false,
        lastSpeechTime: 0,
        analyserActive: false
    },

    // UI state
    ui: {
        overlayVisible: false,
        statusText: 'Ready',
        statusIndicator: 'ready',
        visualizerActive: false
    },

    // Error state
    errors: {
        lastError: null,
        errorCount: 0,
        circuitBreakerActive: false
    },

    // State history for debugging
    history: [],
    maxHistorySize: 50,

    /**
     * Initialize state manager
     */
    initialize() {
        console.log('[StateManager] Initializing Poseidon state manager');
        this.reset();
        this.addToHistory('initialized', {});
        this.initialized = true;
    },

    /**
     * Reset all state to defaults
     */
    reset() {
        this.active = false;
        this.paused = false;
        this.initialized = false;

        this.recognition = {
            state: RECOGNITION_STATES.IDLE,
            restartCount: 0,
            lastStartTime: 0,
            transcriptProcessing: false
        };

        this.audio = {
            streamActive: false,
            level: 0,
            speechDetected: false,
            lastSpeechTime: 0,
            analyserActive: false
        };

        this.ui = {
            overlayVisible: false,
            statusText: 'Ready',
            statusIndicator: 'ready',
            visualizerActive: false
        };

        this.errors = {
            lastError: null,
            errorCount: 0,
            circuitBreakerActive: false
        };

        this.history = [];
        console.log('[StateManager] State reset to defaults');
    },

    /**
     * Update recognition state
     */
    updateRecognitionState(newState, context = {}) {
        const oldState = this.recognition.state;
        this.recognition.state = newState;

        // Update global variable for compatibility
        recognitionState = newState;

        this.addToHistory('recognition-state-change', {
            from: oldState,
            to: newState,
            ...context
        });

        console.log(`[StateManager] Recognition state: ${oldState} -> ${newState}`);
    },

    /**
     * Update audio state
     */
    updateAudioState(updates) {
        Object.assign(this.audio, updates);
        this.addToHistory('audio-state-update', updates);
    },

    /**
     * Update UI state
     */
    updateUIState(updates) {
        Object.assign(this.ui, updates);
        this.addToHistory('ui-state-update', updates);
    },

    /**
     * Record an error
     */
    recordError(error, context = {}) {
        this.errors.lastError = error;
        this.errors.errorCount++;
        this.addToHistory('error-recorded', { error, ...context });
    },

    /**
     * Set active state
     */
    setActive(active, context = {}) {
        this.active = active;
        poseidonActive = active; // Keep global in sync
        this.addToHistory('active-state-change', { active, ...context });
    },

    /**
     * Set paused state
     */
    setPaused(paused, context = {}) {
        this.paused = paused;
        poseidonPaused = paused; // Keep global in sync
        this.addToHistory('paused-state-change', { paused, ...context });
    },

    /**
     * Validate current state consistency
     */
    validateState() {
        const issues = [];

        // Check recognition state consistency
        if (this.recognition.state !== recognitionState) {
            issues.push({
                type: 'inconsistency',
                message: `Recognition state mismatch: manager=${this.recognition.state}, global=${recognitionState}`
            });
        }

        // Check active state consistency
        if (this.active !== poseidonActive) {
            issues.push({
                type: 'inconsistency',
                message: `Active state mismatch: manager=${this.active}, global=${poseidonActive}`
            });
        }

        // Check paused state consistency
        if (this.paused !== poseidonPaused) {
            issues.push({
                type: 'inconsistency',
                message: `Paused state mismatch: manager=${this.paused}, global=${poseidonPaused}`
            });
        }

        // Check stream state consistency
        const streamManagerHealth = audioStreamManager.getHealthStatus();
        if (this.audio.streamActive !== streamManagerHealth.isActive) {
            issues.push({
                type: 'inconsistency',
                message: `Stream state mismatch: manager=${this.audio.streamActive}, streamManager=${streamManagerHealth.isActive}`
            });
        }

        if (issues.length > 0) {
            console.warn('[StateManager] State validation found issues:', issues);
            this.addToHistory('validation-issues', { issues });
            return { valid: false, issues };
        }

        return { valid: true };
    },

    /**
     * Attempt to recover from invalid state
     */
    recoverState() {
        console.log('[StateManager] Attempting state recovery');

        // Sync global variables with manager state
        recognitionState = this.recognition.state;
        poseidonActive = this.active;
        poseidonPaused = this.paused;

        // Sync stream state
        const streamHealth = audioStreamManager.getHealthStatus();
        this.audio.streamActive = streamHealth.isActive;

        this.addToHistory('state-recovery', {
            syncedGlobals: true,
            streamHealth: streamHealth
        });

        console.log('[StateManager] State recovery completed');
    },

    /**
     * Add event to history
     */
    addToHistory(event, data) {
        this.history.push({
            timestamp: Date.now(),
            event: event,
            data: data
        });

        // Keep history size manageable
        if (this.history.length > this.maxHistorySize) {
            this.history.shift();
        }
    },

    /**
     * Get current state snapshot
     */
    getStateSnapshot() {
        return {
            ...this,
            history: this.history.slice(-10) // Last 10 events
        };
    },

    /**
     * Export state for debugging
     */
    exportState() {
        return {
            core: {
                active: this.active,
                paused: this.paused,
                initialized: this.initialized
            },
            recognition: { ...this.recognition },
            audio: { ...this.audio },
            ui: { ...this.ui },
            errors: { ...this.errors },
            streamHealth: audioStreamManager.getHealthStatus(),
            recognitionHistory: recognitionStateManager.getHistory().slice(-5),
            recentHistory: this.history.slice(-10)
        };
    }
};

// Recognition State Manager (legacy - now integrated into poseidonStateManager)
const recognitionStateManager = {
    currentState: RECOGNITION_STATES.IDLE,

    /**
     * Transition to a new state
     * @param {string} newState - The target state
     * @param {Object} context - Context information for the transition
     * @returns {boolean} True if transition was successful
     */
    transition(newState, context = {}) {
        const currentState = this.currentState;
        const allowedTransitions = RECOGNITION_TRANSITIONS[currentState] || [];

        if (!allowedTransitions.includes(newState)) {
            console.error(`[RecognitionState] ❌ Invalid transition: ${currentState} -> ${newState}`);
            console.error('[RecognitionState] Allowed transitions:', allowedTransitions);
            console.error('[RecognitionState] Context:', context);
            return false;
        }

        // Update state
        this.currentState = newState;
        recognitionState = newState; // Keep global variable in sync

        // Track transition history
        recognitionStateHistory.push({
            from: currentState,
            to: newState,
            timestamp: Date.now(),
            context: context
        });

        // Keep only recent history (last 20 transitions)
        if (recognitionStateHistory.length > 20) {
            recognitionStateHistory.shift();
        }

        console.log(`[RecognitionState] ✅ ${currentState} -> ${newState}`, context);
        return true;
    },

    /**
     * Check if a transition is valid
     * @param {string} targetState - The target state
     * @returns {boolean} True if transition is valid
     */
    canTransition(targetState) {
        const allowedTransitions = RECOGNITION_TRANSITIONS[this.currentState] || [];
        return allowedTransitions.includes(targetState);
    },

    /**
     * Reset state to idle
     */
    reset() {
        this.transition(RECOGNITION_STATES.IDLE, { reason: 'reset' });
        recognitionRestartCount = 0;
        recognitionStateHistory = [];
    },

    /**
     * Check if we're in a valid restart state
     * @returns {boolean} True if restart is allowed
     */
    canRestart() {
        // Don't restart if we're already trying too many times
        if (recognitionRestartCount >= MAX_RESTART_ATTEMPTS) {
            console.error(`[RecognitionState] ❌ Max restart attempts (${MAX_RESTART_ATTEMPTS}) exceeded`);
            return false;
        }

        // Don't restart if we're not in a restartable state
        const restartableStates = [RECOGNITION_STATES.STOPPED, RECOGNITION_STATES.ERROR, RECOGNITION_STATES.IDLE];
        if (!restartableStates.includes(this.currentState)) {
            console.warn(`[RecognitionState] ⚠️ Cannot restart from state: ${this.currentState}`);
            return false;
        }

        return true;
    },

    /**
     * Get state transition history
     * @returns {Array} State transition history
     */
    getHistory() {
        return recognitionStateHistory;
    }
};
let speechDetected = false;
let consecutiveNoSpeechCount = 0;
let serviceNotAllowedRetryCount = 0; // Track retries for service-not-allowed errors
let lastServiceNotAllowedTime = 0; // Track when last service-not-allowed occurred
let rapidErrorTimes = []; // Track recent error times for circuit breaker
let serviceNotAllowedDisabled = false; // Circuit breaker flag - stop retrying if too many rapid errors

// Enhanced Error Tracker (v4.3.0)
const poseidonErrorTracker = {
    errors: [],
    errorCounts: {},
    circuitBreakerActive: false,
    circuitBreakerTriggeredAt: 0,
    lastError: null,
    errorHistory: [],
    maxHistorySize: 100,
    
    // Error categories
    ERROR_TYPES: {
        PERMISSION: 'permission',
        NETWORK: 'network',
        SERVICE: 'service',
        STATE: 'state',
        AUDIO: 'audio',
        UNKNOWN: 'unknown'
    },
    
    /**
     * Classify error type
     */
    classifyError(error) {
        const errorName = error?.name || '';
        const errorMessage = (error?.message || '').toLowerCase();
        
        if (errorName === 'NotAllowedError' || errorName === 'PermissionDeniedError' || 
            errorMessage.includes('permission') || errorMessage.includes('not allowed')) {
            return this.ERROR_TYPES.PERMISSION;
        }
        
        if (errorName === 'NetworkError' || errorMessage.includes('network') || 
            errorMessage.includes('failed to fetch') || errorMessage.includes('econnrefused')) {
            return this.ERROR_TYPES.NETWORK;
        }
        
        if (errorMessage.includes('service') || errorName === 'service-not-allowed') {
            return this.ERROR_TYPES.SERVICE;
        }
        
        if (errorName === 'InvalidStateError' || errorMessage.includes('state')) {
            return this.ERROR_TYPES.STATE;
        }
        
        if (errorName === 'NotFoundError' || errorName === 'DevicesNotFoundError' ||
            errorMessage.includes('microphone') || errorMessage.includes('audio')) {
            return this.ERROR_TYPES.AUDIO;
        }
        
        return this.ERROR_TYPES.UNKNOWN;
    },
    
    /**
     * Record an error
     */
    recordError(error, context = {}) {
        const errorType = this.classifyError(error);
        const now = Date.now();
        
        const errorRecord = {
            timestamp: now,
            type: errorType,
            name: error?.name || 'Unknown',
            message: error?.message || 'Unknown error',
            context: context,
            error: error
        };
        
        this.errors.push(errorRecord);
        this.lastError = errorRecord;
        
        // Track error counts by type
        this.errorCounts[errorType] = (this.errorCounts[errorType] || 0) + 1;
        
        // Add to history
        this.errorHistory.push(errorRecord);
        if (this.errorHistory.length > this.maxHistorySize) {
            this.errorHistory.shift();
        }
        
        // Update state manager
        if (poseidonStateManager) {
            poseidonStateManager.recordError(errorRecord, context);
        }
        
        console.log(`[ErrorTracker] Recorded ${errorType} error:`, errorRecord);
        
        // Check for circuit breaker conditions
        this.checkCircuitBreaker();
        
        return errorRecord;
    },
    
    /**
     * Check if circuit breaker should be activated
     */
    checkCircuitBreaker() {
        const now = Date.now();
        const windowMs = 5000; // 5 second window
        const threshold = 5; // 5 errors in window
        
        // Filter recent errors
        const recentErrors = this.errorHistory.filter(e => now - e.timestamp < windowMs);
        
        // Don't trigger circuit breaker for permission errors (user action needed)
        const nonPermissionErrors = recentErrors.filter(e => e.type !== this.ERROR_TYPES.PERMISSION);
        
        if (nonPermissionErrors.length >= threshold && !this.circuitBreakerActive) {
            console.error(`[ErrorTracker] 🛑 Circuit breaker triggered: ${nonPermissionErrors.length} errors in ${windowMs}ms`);
            this.circuitBreakerActive = true;
            this.circuitBreakerTriggeredAt = now;
            
            // Update state manager
            if (poseidonStateManager) {
                poseidonStateManager.errors.circuitBreakerActive = true;
            }
        }
    },
    
    /**
     * Reset circuit breaker (with exponential backoff)
     */
    resetCircuitBreaker() {
        const now = Date.now();
        const timeSinceTrigger = now - this.circuitBreakerTriggeredAt;
        
        // Exponential backoff: wait 10s, 20s, 40s...
        const backoffTime = Math.min(10000 * Math.pow(2, this.getCircuitBreakerAttempts()), 60000);
        
        if (timeSinceTrigger >= backoffTime) {
            console.log(`[ErrorTracker] ✅ Circuit breaker reset after ${timeSinceTrigger}ms`);
            this.circuitBreakerActive = false;
            this.circuitBreakerTriggeredAt = 0;
            
            // Clear recent error history
            const windowMs = 5000;
            this.errorHistory = this.errorHistory.filter(e => now - e.timestamp < windowMs);
            
            // Update state manager
            if (poseidonStateManager) {
                poseidonStateManager.errors.circuitBreakerActive = false;
            }
            
            return true;
        }
        
        return false;
    },
    
    /**
     * Get circuit breaker attempts count
     */
    getCircuitBreakerAttempts() {
        // Count how many times circuit breaker has been triggered recently
        const now = Date.now();
        const windowMs = 60000; // 1 minute window
        return this.errorHistory.filter(e => 
            e.type !== this.ERROR_TYPES.PERMISSION && 
            now - e.timestamp < windowMs
        ).length;
    },
    
    /**
     * Get recovery strategy for error type
     */
    getRecoveryStrategy(errorType) {
        const strategies = {
            [this.ERROR_TYPES.PERMISSION]: {
                retry: false,
                delay: 0,
                userAction: true,
                message: 'Microphone permission is required. Please enable microphone access.'
            },
            [this.ERROR_TYPES.NETWORK]: {
                retry: true,
                delay: 1000,
                maxRetries: 3,
                exponentialBackoff: true,
                message: 'Network error. Retrying...'
            },
            [this.ERROR_TYPES.SERVICE]: {
                retry: true,
                delay: 2000,
                maxRetries: 2,
                exponentialBackoff: true,
                message: 'Service error. Retrying...'
            },
            [this.ERROR_TYPES.STATE]: {
                retry: true,
                delay: 300,
                maxRetries: 3,
                exponentialBackoff: false,
                message: 'State error. Retrying...'
            },
            [this.ERROR_TYPES.AUDIO]: {
                retry: true,
                delay: 1000,
                maxRetries: 2,
                exponentialBackoff: true,
                message: 'Audio device error. Retrying...'
            },
            [this.ERROR_TYPES.UNKNOWN]: {
                retry: true,
                delay: 1000,
                maxRetries: 2,
                exponentialBackoff: true,
                message: 'Unknown error. Retrying...'
            }
        };
        
        return strategies[errorType] || strategies[this.ERROR_TYPES.UNKNOWN];
    },
    
    /**
     * Get error statistics
     */
    getStats() {
        return {
            totalErrors: this.errors.length,
            errorCounts: { ...this.errorCounts },
            circuitBreakerActive: this.circuitBreakerActive,
            lastError: this.lastError,
            recentErrors: this.errorHistory.slice(-10)
        };
    },
    
    /**
     * Reset error tracking
     */
    reset() {
        this.errors = [];
        this.errorCounts = {};
        this.circuitBreakerActive = false;
        this.circuitBreakerTriggeredAt = 0;
        this.lastError = null;
        this.errorHistory = [];
        console.log('[ErrorTracker] Error tracking reset');
    }
};
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
// Performance optimized audio constants (v4.2.0)
const AUDIO_CHECK_INTERVAL_MS = 150; // Increased from 100ms - check audio levels every 150ms (better performance)
const AUDIO_CHECK_INTERVAL_ACTIVE_MS = 100; // Faster checks when actively speaking (100ms)
const AUDIO_CHECK_INTERVAL_IDLE_MS = 300; // Slower checks when idle (300ms)
const AUDIO_LEVEL_THRESHOLD = 0.05; // Minimum audio level to consider as speech
const VOLUME_DECLINE_THRESHOLD = 0.02; // Volume must drop below this to trigger processing
const MIN_VOLUME_DECLINE_DURATION = 800; // How long volume must be low before processing (ms)

// Performance optimization: Debounced operations
let audioProcessingDebounceTimeout = null;
const AUDIO_PROCESSING_DEBOUNCE_MS = 50; // Debounce audio processing operations
let lastAudioProcessingTime = 0;
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
                        recognitionStateManager.transition(RECOGNITION_STATES.IDLE, { reason: 'circuit-breaker-reset' });
                        
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
                    recognitionStateManager.transition(RECOGNITION_STATES.PAUSED, { reason: 'speech-start' });
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
            }, Math.max(250, resumeDelay)); // Optimized: Reduced minimum delay from 300ms to 250ms for faster response
        }
        
        // Helper function to restart recognition after speech (unified restart logic)
        function restartRecognitionAfterSpeech() {
            // Check circuit breaker first - try to reset if enough time has passed
            const isElectron = window.electronAPI !== undefined;
            if (poseidonErrorTracker.circuitBreakerActive) {
                if (poseidonErrorTracker.resetCircuitBreaker()) {
                    console.log('[Poseidon] ✅ Circuit breaker reset, allowing restart after speech');
                } else if (!isElectron) {
                    console.warn('[Poseidon] Circuit breaker active - not restarting recognition after speech');
                    return;
                }
            }
            
            // Validate state before restart
            if (!recognition || !poseidonActive || poseidonPaused || isSpeaking) {
                console.log('[Poseidon] Cannot restart recognition - conditions not met:', {
                    hasRecognition: !!recognition,
                    poseidonActive: poseidonActive,
                    poseidonPaused: poseidonPaused,
                    isSpeaking: isSpeaking
                });
                return;
            }
            
            // Check state machine constraints
            if (!recognitionStateManager.canRestart()) {
                console.warn('[Poseidon] Cannot restart - state machine constraints');
                return;
            }
            
            try {
                console.log('[Poseidon] Resuming recognition after speech ended');
                // Use unified startRecognitionWithRetry for consistent error handling
                startRecognitionWithRetry();
                console.log('[Poseidon] ✅ Recognition restart initiated after speech');
            } catch (e) {
                console.warn('[Poseidon] Error resuming recognition:', e);
                // Record error and retry with error handling
                poseidonErrorTracker.recordError(e, { context: 'restartAfterSpeech' });
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
        const isElectron = window.electronAPI !== undefined;
        if (poseidonActive && !poseidonPaused) {
            // Check circuit breaker - try to reset if enough time has passed
            if (poseidonErrorTracker.circuitBreakerActive) {
                if (poseidonErrorTracker.resetCircuitBreaker()) {
                    console.log('[Poseidon] ✅ Circuit breaker reset, allowing restart after speech error');
                } else if (!isElectron) {
                    updatePoseidonStatus('ready', 'Speech Error');
                    return;
                }
            }
            
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
            if (isElectron && poseidonErrorTracker.circuitBreakerActive) {
                console.log('[Poseidon] Electron: Resetting circuit breaker on overlay open');
                poseidonErrorTracker.reset();
                serviceNotAllowedRetryCount = 0;
                lastServiceNotAllowedTime = 0;
            } else {
                // Try to reset circuit breaker (exponential backoff)
                poseidonErrorTracker.resetCircuitBreaker();
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
        
        // Initialize and set up stream with the stream manager
        audioStreamManager.initialize();
        audioStreamManager.setStream(stream);
        
        if (poseidonOverlay) {
            // Overlay already shown at the start of function
            poseidonActive = true;
            console.log('[Poseidon] Overlay visible, setting poseidonActive=true');
            poseidonPaused = false;
            recognitionStateManager.transition(RECOGNITION_STATES.STARTING, { reason: 'initialization' });
            
            // Reset all state
            pendingTranscript = '';
            transcriptProcessing = false;
            speechDetected = false;
            consecutiveNoSpeechCount = 0;
            serviceNotAllowedRetryCount = 0; // Reset retry counter
            lastServiceNotAllowedTime = 0;
            rapidErrorTimes = []; // Reset rapid error tracking (legacy)
            serviceNotAllowedDisabled = false; // Reset circuit breaker (legacy)
            
            // Reset error tracker
            poseidonErrorTracker.reset();
            lastSpeechTime = Date.now();
            clearTimeout(silenceTimeout);
            clearTimeout(recognitionRestartTimeout);

        // Reset state machine, error tracker, and stream manager
        poseidonStateManager.reset();
        poseidonStateManager.initialize();
        audioStreamManager.initialize();
            
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
                    analyser.fftSize = 128; // Optimized: Reduced from 256 for better performance
                    analyser.smoothingTimeConstant = 0.6; // Optimized: Reduced smoothing for faster response
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
        recognitionStateManager.transition(RECOGNITION_STATES.IDLE, { reason: 'inactive' });
    }
}

/**
 * Simplified recognition start function with state machine integration
 * @param {Object} options - Start options
 * @returns {Promise<boolean>} True if recognition started successfully
 */
async function startRecognitionWithRetry(options = {}) {
    const maxRetries = options.maxRetries || 3;
    const forceRestart = options.forceRestart || false;

    // Check circuit breaker first - try to reset if enough time has passed
    const isElectron = window.electronAPI !== undefined;
    if (poseidonErrorTracker.circuitBreakerActive) {
        // Try to reset circuit breaker (exponential backoff)
        if (poseidonErrorTracker.resetCircuitBreaker()) {
            console.log('[Poseidon] ✅ Circuit breaker reset, allowing recognition start');
        } else if (!isElectron) {
            console.warn('[Poseidon] 🛑 Circuit breaker active - blocking recognition start');
            updatePoseidonStatus('ready', 'Service Unavailable');
            return false;
        }
    }

    // Check state machine constraints
    if (!recognitionStateManager.canRestart() && !forceRestart) {
        console.warn('[Poseidon] ❌ Cannot restart recognition - state constraints');
        return false;
    }

    // Ensure Poseidon is active
    if (!poseidonActive) {
        console.warn('[Poseidon] ❌ Cannot start recognition - Poseidon is not active');
        return false;
    }

    // Validate recognition instance
    if (!recognition) {
        console.error('[Poseidon] ❌ Cannot start recognition - recognition instance is null');
        updatePoseidonStatus('ready', 'Error: Recognition not initialized');
        return false;
    }

    // Validate audio stream
    if (!await validateAudioStream()) {
        console.error('[Poseidon] ❌ Cannot start recognition - audio stream validation failed');
        updatePoseidonStatus('ready', 'Error: Audio stream unavailable');
        return false;
    }

    // Validate configuration
    validateRecognitionConfig();

    // Increment restart counter
    recognitionRestartCount++;

    // Attempt to start recognition
    try {
        recognitionStateManager.transition(RECOGNITION_STATES.STARTING, {
            attempt: recognitionRestartCount,
            maxRetries: maxRetries
        });

        console.log(`[Poseidon] Starting recognition (attempt ${recognitionRestartCount})`);

        recognition.start();

        // Verify start after a short delay
        setTimeout(() => {
            if (recognitionStateManager.currentState === RECOGNITION_STATES.STARTING) {
                recognitionStateManager.transition(RECOGNITION_STATES.LISTENING, {
                    verified: true
                });
                updatePoseidonStatus('listening', 'Listening...');
                console.log('[Poseidon] ✅ Recognition started successfully');
            }
        }, 500);

        return true;

    } catch (error) {
        console.error(`[Poseidon] ❌ Failed to start recognition (attempt ${recognitionRestartCount}):`, error);

        // Record error with error tracker
        const errorRecord = poseidonErrorTracker.recordError(error, {
            attempt: recognitionRestartCount,
            function: 'startRecognitionWithRetry'
        });
        const recoveryStrategy = poseidonErrorTracker.getRecoveryStrategy(errorRecord.type);

        recognitionStateManager.transition(RECOGNITION_STATES.ERROR, {
            error: error.message,
            attempt: recognitionRestartCount,
            errorType: errorRecord.type
        });

        // Handle specific error types using recovery strategy
        if (recoveryStrategy.retry && recognitionRestartCount <= (recoveryStrategy.maxRetries || maxRetries)) {
            const delay = recoveryStrategy.exponentialBackoff 
                ? recoveryStrategy.delay * Math.pow(2, recognitionRestartCount)
                : recoveryStrategy.delay;
            
            console.log(`[Poseidon] Retrying recognition start in ${delay}ms (attempt ${recognitionRestartCount + 1}) - ${errorRecord.type} error`);
            setTimeout(() => {
                if (!poseidonErrorTracker.circuitBreakerActive || isElectron) {
                    startRecognitionWithRetry({ maxRetries, forceRestart: true });
                }
            }, delay);
            return false;
        } else if (recoveryStrategy.userAction) {
            updatePoseidonStatus('ready', 'Permission Required');
            alert(recoveryStrategy.message || 'Microphone permission is required. Please allow microphone access and try again.');
            return false;
        }

        // Max retries exceeded or unrecoverable error
        console.error('[Poseidon] ❌ Giving up on recognition start after', recognitionRestartCount, 'attempts');
        updatePoseidonStatus('ready', 'Error: Cannot start recognition');
        recognitionStateManager.transition(RECOGNITION_STATES.IDLE, {
            reason: 'max-retries-exceeded',
            finalError: error.message
        });

        return false;
    }
}

/**
 * Validate audio stream before starting recognition
 * @returns {Promise<boolean>} True if stream is valid
 */
async function validateAudioStream() {
    const healthStatus = audioStreamManager.getHealthStatus();

    if (!healthStatus.hasStream) {
        console.error('[AudioStream] No audio stream available');
        return false;
    }

    if (!healthStatus.isActive || healthStatus.activeTracks === 0) {
        console.warn('[AudioStream] Stream not healthy, health status:', healthStatus);

        // Try stream recovery
        await new Promise(resolve => setTimeout(resolve, 1000)); // Give recovery a moment

        const newHealthStatus = audioStreamManager.getHealthStatus();
        if (!newHealthStatus.isActive || newHealthStatus.activeTracks === 0) {
            console.error('[AudioStream] Stream still not healthy after recovery attempt');
            return false;
        }
    }

    console.log(`[AudioStream] ✅ Validated: ${healthStatus.activeTracks} active track(s)`);
    return true;
}

/**
 * Validate and fix recognition configuration
 */
function validateRecognitionConfig() {
    if (!recognition) return;

        let configChanged = false;
        
    // Ensure correct configuration
        if (recognition.continuous !== true) {
            recognition.continuous = true;
            configChanged = true;
        }
        if (recognition.interimResults !== true) {
            recognition.interimResults = true;
            configChanged = true;
        }
        if (recognition.maxAlternatives !== 1) {
            recognition.maxAlternatives = 1;
            configChanged = true;
        }
        
    // Set language
    const targetLang = voiceSettings.accent === 'hi-IN' || currentLanguage === 'hi-IN'
        ? 'hi-IN'
        : (voiceSettings.accent || currentLanguage || 'en-US');

    if (recognition.lang !== targetLang) {
        recognition.lang = targetLang;
        configChanged = true;
    }

    if (configChanged) {
        console.log('[RecognitionConfig] ✅ Configuration validated and corrected');
    }
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
    
    console.log('[Poseidon] Starting optimized audio level monitoring');
    
    // Reset audio tracking
    lastHighVolumeTime = Date.now();
    currentAudioLevel = 0;
    audioLevelHistory = [];
    lastAudioProcessingTime = 0;
    
    try {
        const dataArray = new Uint8Array(analyser.frequencyBinCount);
        let volumeDeclineStartTime = null;
        let wasSpeaking = false;
        
        let currentCheckInterval = AUDIO_CHECK_INTERVAL_MS;

        const performAudioCheck = () => {
            if (!analyser || !poseidonActive || poseidonPaused) return;

            const now = Date.now();

            // Performance optimization: Debounce rapid audio processing
            if (now - lastAudioProcessingTime < AUDIO_PROCESSING_DEBOUNCE_MS) {
                return;
            }
            
            try {
                analyser.getByteFrequencyData(dataArray);

                // Enhanced audio analysis: Focus on speech frequencies (300Hz-3400Hz)
                // FFT bin 128 covers ~0-24000Hz, we want bins ~3-42 (roughly 300Hz-3400Hz)
                const speechBins = dataArray.slice(3, 43); // Optimized frequency range
                const average = speechBins.reduce((a, b) => a + b, 0) / speechBins.length;
                let audioLevel = average / 255;

                // Apply noise gate to reduce false positives
                const noiseGateThreshold = 0.008; // Very low level noise filtering
                if (audioLevel < noiseGateThreshold) {
                    audioLevel = 0;
                }

                // Apply dynamic range compression for better sensitivity
                if (audioLevel > 0.1) {
                    audioLevel = 0.1 + (audioLevel - 0.1) * 0.3; // Soft compression above 0.1
                }
                currentAudioLevel = audioLevel;
                lastAudioProcessingTime = now;
                
                // Keep history (optimized: last 15 samples = ~2-3 seconds)
                audioLevelHistory.push(audioLevel);
                if (audioLevelHistory.length > 15) {
                    audioLevelHistory.shift();
                }
                
                // Adaptive sensitivity (only when we have enough data)
                if (audioLevelHistory.length >= 8) {
                    adaptListeningSensitivity(audioLevelHistory);
                }
                
                // Batch DOM updates for better performance
                if (poseidonVisualizer) {
                    const level = Math.min(audioLevel * 100, 100);
                    // Use requestAnimationFrame for smooth visual updates
                    requestAnimationFrame(() => {
                        if (poseidonVisualizer) {
                    poseidonVisualizer.style.setProperty('--audio-level', `${level}%`);
                        }
                    });
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
        };
        
        // Start with default interval
        audioLevelCheckInterval = setInterval(performAudioCheck, AUDIO_CHECK_INTERVAL_MS);

        console.log('[Poseidon] Optimized audio level monitoring started successfully');
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
    recognitionStateManager.transition(RECOGNITION_STATES.PROCESSING, { reason: 'transcript-processing' });
    
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
            voice_mode: true  // Optimize for voice mode (v4.3.0)
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
            recognitionStateManager.transition(RECOGNITION_STATES.LISTENING, { reason: 'transcript-end' });
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
            recognitionStateManager.transition(RECOGNITION_STATES.IDLE, { reason: 'inactive' });
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
        recognitionStateManager.transition(RECOGNITION_STATES.STOPPED, { reason: 'recognition-end' });
        
        if (!poseidonActive || poseidonPaused) {
            console.log('[Poseidon] Not restarting - inactive or paused');
            updatePoseidonStatus('ready', 'Ready');
            recognitionStateManager.transition(RECOGNITION_STATES.IDLE, { reason: 'inactive' });
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
            }, 150); // Optimized: Further reduced restart delay from 200ms to 150ms for faster recovery
        }
    };
    
    /**
     * Unified recognition restart function (v4.3.0)
     * Consolidates all restart logic into a single function with proper state management
     */
    function restartRecognition() {
        // Validate state before restart
        if (!poseidonActive || poseidonPaused || transcriptProcessing) {
            console.warn('[Poseidon] Cannot restart recognition - conditions not met:', {
                poseidonActive: poseidonActive,
                poseidonPaused: poseidonPaused,
                transcriptProcessing: transcriptProcessing
            });
            return;
        }
        
        // Check state machine constraints
        if (!recognitionStateManager.canRestart()) {
            console.warn('[Poseidon] Cannot restart - state machine constraints');
            return;
        }
        
        // Check circuit breaker
        const isElectron = window.electronAPI !== undefined;
        if (poseidonErrorTracker.circuitBreakerActive) {
            if (poseidonErrorTracker.resetCircuitBreaker()) {
                console.log('[Poseidon] ✅ Circuit breaker reset, allowing restart');
            } else if (!isElectron) {
                console.warn('[Poseidon] Circuit breaker active - not restarting');
                return;
            }
        }
        
        console.log('[Poseidon] Restarting recognition...');
        
        // Transition to stopped state first
        if (recognitionStateManager.canTransition(RECOGNITION_STATES.STOPPED)) {
            recognitionStateManager.transition(RECOGNITION_STATES.STOPPED, { reason: 'restart-initiated' });
        }
        
        try {
            if (recognition) {
                recognition.stop();
                console.log('[Poseidon] Recognition stopped for restart');
            } else {
                console.error('[Poseidon] ERROR: Cannot restart - recognition is null');
                recognitionStateManager.transition(RECOGNITION_STATES.ERROR, { reason: 'recognition-null' });
                return;
            }
        } catch (e) {
            console.error('[Poseidon] ERROR stopping recognition for restart:', e);
            poseidonErrorTracker.recordError(e, { context: 'restartRecognition-stop' });
            recognitionStateManager.transition(RECOGNITION_STATES.ERROR, { reason: 'stop-error', error: e.message });
        }
        
        // Use unified start function with delay
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
                recognitionStateManager.transition(RECOGNITION_STATES.IDLE, { reason: 'restart-cancelled' });
            }
        }, 250); // Optimized: Reduced delay from 300ms to 250ms for faster restart
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
        
        // Create error object for error tracker
        const errorObj = {
            name: event.error || 'UnknownError',
            message: event.message || `Recognition error: ${event.error}`,
            error: event.error
        };
        
        // Record error with error tracker
        const errorRecord = poseidonErrorTracker.recordError(errorObj, {
            eventType: event.type,
            recognitionState: recognitionState,
            poseidonActive: poseidonActive
        });
        const recoveryStrategy = poseidonErrorTracker.getRecoveryStrategy(errorRecord.type);
        
        let errorMsg = '';
        let shouldSpeak = true;
        let shouldRestart = false;
        
        if (event.error === 'no-speech') {
            console.log('[Poseidon] No speech detected (normal - will restart silently)');
            shouldSpeak = false;
            shouldRestart = true;
        } else if (event.error === 'not-allowed') {
            console.error('[Poseidon] ERROR: Microphone permission denied');
            errorMsg = recoveryStrategy.message || 'Microphone permission denied. Please enable microphone access.';
            alert('Please enable microphone access in your browser settings to use Poseidon.');
            updatePoseidonStatus('ready', 'Permission Required');
        } else if (event.error === 'network') {
            console.error('[Poseidon] ERROR: Network error in recognition');
            
            // CRITICAL: Check circuit breaker before restarting on network errors
            // NOTE: Circuit breaker should NOT trigger on network errors in Electron app
            // Network errors in Electron are often transient and not related to speech recognition service
            const isElectron = window.electronAPI !== undefined;
            
            if (poseidonErrorTracker.circuitBreakerActive && !isElectron) {
                // Only apply circuit breaker to network errors in browser, not Electron
                console.warn('[Poseidon] Circuit breaker active - not restarting on network error');
                errorMsg = recoveryStrategy.message || 'Network error. Speech recognition service is temporarily unavailable.';
                shouldRestart = false;
                shouldSpeak = true;
            } else {
                // Use recovery strategy for network errors
                if (recoveryStrategy.retry && !poseidonErrorTracker.circuitBreakerActive) {
                    errorMsg = recoveryStrategy.message || 'Network error. Retrying...';
                    shouldRestart = true;
                } else {
                    errorMsg = recoveryStrategy.message || 'Network error. Service temporarily unavailable.';
                    shouldRestart = false;
                    shouldSpeak = true;
                }
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
    poseidonStateManager.setActive(false, { reason: 'overlay-closed' });
    poseidonStateManager.setPaused(false, { reason: 'overlay-closed' });
    poseidonStateManager.recognition.transcriptProcessing = false;
    poseidonStateManager.updateRecognitionState(RECOGNITION_STATES.IDLE, { reason: 'overlay-closed' });
    
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
    // Release audio stream using stream manager
    audioStreamManager.releaseStream();
    
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

// ============================================
// ENHANCED FEATURES v1.4.2
// ============================================

// Keyboard Shortcuts System
function initializeKeyboardShortcuts() {
    // Load saved shortcuts from localStorage
    const savedShortcuts = localStorage.getItem('keyboardShortcuts');
    if (savedShortcuts) {
        try {
            keyboardShortcuts = JSON.parse(savedShortcuts);
        } catch (e) {
            console.warn('Failed to load keyboard shortcuts:', e);
        }
    }
    
    // Default shortcuts (Phase 3.1)
    const defaultShortcuts = {
        'newChat': { key: 'n', ctrl: true, shift: false, alt: false, description: 'New Chat' },
        'sendMessage': { key: 'Enter', ctrl: false, shift: false, alt: false, description: 'Send Message' },
        'sendMessageCtrl': { key: 'Enter', ctrl: true, shift: false, alt: false, description: 'Send Message (Ctrl+Enter)' },
        'newLine': { key: 'Enter', ctrl: false, shift: true, alt: false, description: 'New Line' },
        'focusInput': { key: 'l', ctrl: true, shift: false, alt: false, description: 'Focus Input' },
        'toggleSidebar': { key: 'b', ctrl: true, shift: false, alt: false, description: 'Toggle Sidebar' },
        'toggleTheme': { key: 't', ctrl: true, shift: true, alt: false, description: 'Toggle Theme' },
        'toggleThinkDeeper': { key: 'd', ctrl: true, shift: false, alt: false, description: 'Toggle Think Deeper' },
        'openSettings': { key: ',', ctrl: true, shift: false, alt: false, description: 'Open Settings' },
        'openHelp': { key: '/', ctrl: true, shift: false, alt: false, description: 'Open Help' },
        'exportChat': { key: 'e', ctrl: true, shift: true, alt: false, description: 'Export Chat' },
        'commandPalette': { key: 'k', ctrl: true, shift: false, alt: false, description: 'Command Palette' },
        'closeModal': { key: 'Escape', ctrl: false, shift: false, alt: false, description: 'Close Modal' },
    };
    
    // Merge with saved shortcuts
    keyboardShortcuts = { ...defaultShortcuts, ...keyboardShortcuts };
    
    // Add global keyboard listener
    document.addEventListener('keydown', handleKeyboardShortcut);
    
    // Show shortcuts help
    showNotification('Keyboard shortcuts enabled! Press Ctrl+/ to see all shortcuts.', 'info', 3000);
}

function handleKeyboardShortcut(e) {
    // Don't trigger shortcuts when typing in input fields (unless it's a special shortcut)
    const target = e.target;
    const isInput = target.tagName === 'INPUT' || target.tagName === 'TEXTAREA';
    const isContentEditable = target.contentEditable === 'true';
    
    // Special cases: allow shortcuts in input for certain actions
    const allowedInInput = ['Enter', 'Escape'];
    
    if (isInput && !allowedInInput.includes(e.key) && !e.ctrlKey && !e.metaKey) {
        return;
    }
    
    // Check each shortcut
    for (const [action, shortcut] of Object.entries(keyboardShortcuts)) {
        if (matchesShortcut(e, shortcut)) {
            e.preventDefault();
            executeShortcut(action);
            return;
        }
    }
    
    // Special: Ctrl+/ or Cmd+/ for help
    if ((e.ctrlKey || e.metaKey) && e.key === '/') {
        e.preventDefault();
        openKeyboardShortcutsHelp();
        return;
    }
    
    // Special: Ctrl+K or Cmd+K for command palette
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        openCommandPalette();
        return;
    }
    
    // Special: Escape to close modals
    if (e.key === 'Escape') {
        closeTopModal();
        return;
    }
}

function matchesShortcut(e, shortcut) {
    const keyMatch = e.key === shortcut.key || 
                     (shortcut.key === 'Enter' && e.key === 'Enter') ||
                     (shortcut.key.toLowerCase() === e.key.toLowerCase());
    const ctrlMatch = (e.ctrlKey || e.metaKey) === shortcut.ctrl;
    const shiftMatch = e.shiftKey === shortcut.shift;
    const altMatch = e.altKey === shortcut.alt;
    
    return keyMatch && ctrlMatch && shiftMatch && altMatch;
}

function executeShortcut(action) {
    switch (action) {
        case 'newChat':
            startNewChat();
            break;
        case 'sendMessage':
        case 'sendMessageCtrl':
            if (!isLoading) {
                handleSendMessage();
            }
            break;
        case 'commandPalette':
            openCommandPalette();
            break;
        case 'closeModal':
            closeTopModal();
            break;
        case 'newLine':
            // Allow new line in textarea (default behavior)
            break;
        case 'focusInput':
            document.getElementById('messageInput')?.focus();
            break;
        case 'toggleSidebar':
            toggleSidebar();
            break;
        case 'toggleTheme':
            toggleTheme();
            break;
        case 'toggleThinkDeeper':
            toggleThinkDeeper();
            break;
        case 'openSettings':
            openSettingsModal();
            break;
        case 'openHelp':
            openHelpModal();
            break;
        case 'exportChat':
            if (currentChatId) {
                exportChat(currentChatId);
            }
            break;
    }
}

function openKeyboardShortcutsHelp() {
    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.style.display = 'flex';
    modal.innerHTML = `
        <div class="modal-content glass-card" style="max-width: 600px;">
            <div class="modal-header">
                <h2>Keyboard Shortcuts</h2>
                <button class="modal-close" onclick="this.closest('.modal').remove()">&times;</button>
            </div>
            <div class="modal-body">
                <div class="shortcuts-list">
                    ${Object.entries(keyboardShortcuts).map(([action, shortcut]) => {
                        const keys = [];
                        if (shortcut.ctrl) keys.push('Ctrl');
                        if (shortcut.shift) keys.push('Shift');
                        if (shortcut.alt) keys.push('Alt');
                        keys.push(shortcut.key);
                        return `
                            <div class="shortcut-item">
                                <div class="shortcut-keys">
                                    ${keys.map(k => `<kbd>${k}</kbd>`).join(' + ')}
                                </div>
                                <div class="shortcut-action">${formatActionName(action)}</div>
                            </div>
                        `;
                    }).join('')}
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    modal.addEventListener('click', (e) => {
        if (e.target === modal) modal.remove();
    });
}

function formatActionName(action) {
    const names = {
        'newChat': 'New Chat',
        'sendMessage': 'Send Message',
        'newLine': 'New Line',
        'focusInput': 'Focus Input',
        'toggleSidebar': 'Toggle Sidebar',
        'toggleTheme': 'Toggle Theme',
        'toggleThinkDeeper': 'Toggle Think Deeper',
        'openSettings': 'Open Settings',
        'openHelp': 'Open Help',
        'exportChat': 'Export Chat',
        'commandPalette': 'Command Palette',
        'closeModal': 'Close Modal',
    };
    return names[action] || action;
}

function closeTopModal() {
    // Close the topmost visible modal
    const modals = document.querySelectorAll('.modal[style*="flex"], .modal[style*="block"]');
    if (modals.length > 0) {
        const topModal = modals[modals.length - 1];
        topModal.style.display = 'none';
    }
    
    // Also close command palette if open
    const commandPalette = document.getElementById('commandPalette');
    if (commandPalette && commandPalette.style.display !== 'none') {
        closeCommandPalette();
    }
}

// ============================================
// COMMAND PALETTE (Phase 3.2)
// ============================================

let commandPaletteCommands = [];
let selectedCommandIndex = -1;

function initializeCommandPalette() {
    // Build command list - will be called after gems are loaded
    buildCommandList();
}

function buildCommandList() {
    commandPaletteCommands = [
        { id: 'new-chat', name: 'New Chat', description: 'Start a new conversation', category: 'Chat', icon: '+', action: () => startNewChat(), shortcut: 'Ctrl+N' },
        { id: 'search-chats', name: 'Search Chats', description: 'Search through your chat history', category: 'Chat', icon: '🔍', action: () => { closeCommandPalette(); openRecentChatsModal(); } },
        { id: 'open-settings', name: 'Open Settings', description: 'Open application settings', category: 'Navigation', icon: '⚙️', action: () => { closeCommandPalette(); openSettingsModal(); }, shortcut: 'Ctrl+,' },
        { id: 'open-help', name: 'Open Help', description: 'View help and documentation', category: 'Navigation', icon: '?', action: () => { closeCommandPalette(); openHelpModal(); }, shortcut: 'Ctrl+/' },
        { id: 'open-gems', name: 'Open Gems', description: 'Manage and create custom Gems', category: 'Navigation', icon: '💎', action: () => { closeCommandPalette(); openCustomizeModal(); } },
        { id: 'toggle-theme', name: 'Toggle Theme', description: 'Switch between light and dark mode', category: 'Navigation', icon: '🌓', action: () => { closeCommandPalette(); toggleTheme(); }, shortcut: 'Ctrl+Shift+T' },
        { id: 'focus-input', name: 'Focus Input', description: 'Focus the message input field', category: 'Navigation', icon: '⌨️', action: () => { closeCommandPalette(); document.getElementById('messageInput')?.focus(); }, shortcut: 'Ctrl+L' },
        { id: 'toggle-think-deeper', name: 'Toggle Think Deeper', description: 'Enable/disable deep thinking mode', category: 'Features', icon: '🧠', action: () => { closeCommandPalette(); toggleThinkDeeper(); }, shortcut: 'Ctrl+D' },
    ];
    
    // Add model switching commands
    if (systemMode === 'stable') {
        commandPaletteCommands.push({ id: 'switch-model-thor-1-0', name: 'Switch to Thor 1.0', description: 'Use stable Thor 1.0 model', category: 'Model', icon: '🤖', action: () => { closeCommandPalette(); selectModelFromString('thor-1.0'); } });
    } else {
        commandPaletteCommands.push(
            { id: 'switch-model-thor-1-2', name: 'Switch to Thor 1.2', description: 'Use default Thor 1.2 model', category: 'Model', icon: '🤖', action: () => { closeCommandPalette(); selectModelFromString('thor-1.2'); } },
            { id: 'switch-model-thor-1-1', name: 'Switch to Thor 1.1', description: 'Use Thor 1.1 model', category: 'Model', icon: '🤖', action: () => { closeCommandPalette(); selectModelFromString('thor-1.1'); } },
            { id: 'switch-model-thor-1-0', name: 'Switch to Thor 1.0', description: 'Use stable Thor 1.0 model', category: 'Model', icon: '🤖', action: () => { closeCommandPalette(); selectModelFromString('thor-1.0'); } }
        );
    }
    
    // Add gem commands if available
    if (gems && gems.length > 0) {
        gems.forEach(gem => {
            commandPaletteCommands.push({
                id: `switch-gem-${gem.id}`,
                name: `Switch to ${gem.name}`,
                description: `Use ${gem.name} Gem`,
                category: 'Model',
                icon: '💎',
                action: () => { closeCommandPalette(); selectGemModel(gem.id); }
            });
        });
    }
}

function selectModelFromString(modelId) {
    // Create a fake event object for selectModel
    const fakeEvent = {
        currentTarget: {
            closest: () => ({
                getAttribute: () => modelId
            })
        }
    };
    selectModel(fakeEvent);
}

function openCommandPalette() {
    const palette = document.getElementById('commandPalette');
    const input = document.getElementById('commandInput');
    const list = document.getElementById('commandList');
    
    if (!palette || !input || !list) return;
    
    palette.style.display = 'flex';
    selectedCommandIndex = -1;
    
    // Rebuild command list in case gems changed
    buildCommandList();
    
    // Render all commands initially
    renderCommands(commandPaletteCommands);
    
    // Focus input after a brief delay to ensure it's visible
    setTimeout(() => {
        input.focus();
        input.value = '';
    }, 50);
    
    // Setup event listeners (remove old ones first)
    const newInput = input.cloneNode(true);
    input.parentNode.replaceChild(newInput, input);
    const newInputEl = document.getElementById('commandInput');
    
    newInputEl.addEventListener('input', handleCommandSearch);
    newInputEl.addEventListener('keydown', handleCommandKeydown);
    
    // Close on overlay click
    const overlay = palette.querySelector('.command-palette-overlay');
    if (overlay) {
        overlay.addEventListener('click', closeCommandPalette);
    }
}

function closeCommandPalette() {
    const palette = document.getElementById('commandPalette');
    if (palette) {
        palette.style.display = 'none';
    }
    selectedCommandIndex = -1;
}

function handleCommandSearch(e) {
    const query = e.target.value.toLowerCase().trim();
    const filtered = query 
        ? commandPaletteCommands.filter(cmd => 
            cmd.name.toLowerCase().includes(query) || 
            cmd.description.toLowerCase().includes(query) ||
            cmd.category.toLowerCase().includes(query)
          )
        : commandPaletteCommands;
    
    renderCommands(filtered);
    selectedCommandIndex = -1;
}

function handleCommandKeydown(e) {
    const list = document.getElementById('commandList');
    if (!list) return;
    
    const items = list.querySelectorAll('.command-item:not(.command-category)');
    
    switch (e.key) {
        case 'ArrowDown':
            e.preventDefault();
            selectedCommandIndex = Math.min(selectedCommandIndex + 1, items.length - 1);
            updateCommandSelection(items);
            scrollToSelectedCommand(items);
            break;
        case 'ArrowUp':
            e.preventDefault();
            selectedCommandIndex = Math.max(selectedCommandIndex - 1, -1);
            updateCommandSelection(items);
            scrollToSelectedCommand(items);
            break;
        case 'Enter':
            e.preventDefault();
            if (selectedCommandIndex >= 0 && items[selectedCommandIndex]) {
                const commandId = items[selectedCommandIndex].getAttribute('data-command-id');
                executeCommand(commandId);
            } else if (items.length > 0) {
                // Execute first command if none selected
                const commandId = items[0].getAttribute('data-command-id');
                executeCommand(commandId);
            }
            break;
        case 'Escape':
            e.preventDefault();
            closeCommandPalette();
            break;
    }
}

function renderCommands(commands) {
    const list = document.getElementById('commandList');
    if (!list) return;
    
    // Group by category
    const grouped = {};
    commands.forEach(cmd => {
        if (!grouped[cmd.category]) {
            grouped[cmd.category] = [];
        }
        grouped[cmd.category].push(cmd);
    });
    
    let html = '';
    Object.keys(grouped).sort().forEach(category => {
        html += `<div class="command-category">${category}</div>`;
        grouped[category].forEach(cmd => {
            html += `
                <div class="command-item" data-command-id="${cmd.id}">
                    <div class="command-item-icon">${cmd.icon || '•'}</div>
                    <div class="command-item-content">
                        <div class="command-item-name">${escapeHtml(cmd.name)}</div>
                        <div class="command-item-desc">${escapeHtml(cmd.description)}</div>
                    </div>
                    ${cmd.shortcut ? `<div class="command-item-shortcut">${cmd.shortcut}</div>` : ''}
                </div>
            `;
        });
    });
    
    list.innerHTML = html;
    
    // Add click handlers
    list.querySelectorAll('.command-item').forEach(item => {
        item.addEventListener('click', () => {
            const commandId = item.getAttribute('data-command-id');
            executeCommand(commandId);
        });
    });
}

function updateCommandSelection(items) {
    items.forEach((item, index) => {
        if (index === selectedCommandIndex) {
            item.classList.add('selected');
        } else {
            item.classList.remove('selected');
        }
    });
}

function scrollToSelectedCommand(items) {
    if (selectedCommandIndex >= 0 && items[selectedCommandIndex]) {
        items[selectedCommandIndex].scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
}

function executeCommand(commandId) {
    const command = commandPaletteCommands.find(cmd => cmd.id === commandId);
    if (command && command.action) {
        command.action();
    }
}

// ============================================
// FOCUS MANAGEMENT (Phase 3.3)
// ============================================

let focusHistory = [];
let currentModalFocus = null;

function trapFocusInModal(modal) {
    if (!modal) return;
    
    const focusableElements = modal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    );
    
    if (focusableElements.length === 0) return;
    
    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];
    
    // Store current focus
    focusHistory.push(document.activeElement);
    
    // Focus first element
    firstElement.focus();
    currentModalFocus = { modal, firstElement, lastElement };
    
    // Trap focus
    modal.addEventListener('keydown', handleModalKeydown);
}

function releaseFocusFromModal() {
    if (currentModalFocus) {
        currentModalFocus.modal.removeEventListener('keydown', handleModalKeydown);
        currentModalFocus = null;
    }
    
    // Restore previous focus
    if (focusHistory.length > 0) {
        const previousFocus = focusHistory.pop();
        if (previousFocus && typeof previousFocus.focus === 'function') {
            setTimeout(() => {
                previousFocus.focus();
                // Add visual indicator
                previousFocus.classList.add('focus-restore');
                setTimeout(() => {
                    previousFocus.classList.remove('focus-restore');
                }, 300);
            }, 100);
        }
    }
}

function handleModalKeydown(e) {
    if (!currentModalFocus) return;
    
    if (e.key === 'Tab') {
        if (e.shiftKey) {
            // Shift + Tab
            if (document.activeElement === currentModalFocus.firstElement) {
                e.preventDefault();
                currentModalFocus.lastElement.focus();
            }
        } else {
            // Tab
            if (document.activeElement === currentModalFocus.lastElement) {
                e.preventDefault();
                currentModalFocus.firstElement.focus();
            }
        }
    } else if (e.key === 'Escape') {
        // Close modal on Escape
        const modal = currentModalFocus.modal;
        if (modal) {
            modal.style.display = 'none';
            releaseFocusFromModal();
        }
    }
}

// Focus management is integrated into modal open/close functions above


// ============================================
// DRAG AND DROP FOR FILE UPLOADS (Phase 5.1)
// ============================================

function initializeDragAndDrop() {
    const inputContainer = document.querySelector('.input-container');
    const chatContainer = document.getElementById('chatContainer');
    const messageInput = document.getElementById('messageInput');
    
    if (!inputContainer) return;
    
    let dragCounter = 0;
    let isDragging = false;
    
    // Create drop zone overlay
    const dropZone = document.createElement('div');
    dropZone.className = 'drop-zone-overlay';
    dropZone.id = 'dropZoneOverlay';
    dropZone.innerHTML = `
        <div class="drop-zone-content">
            <div class="drop-zone-icon">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V15" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M7 10L12 5L17 10" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M12 5V15" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
            </div>
            <div class="drop-zone-text">Drop files here to upload</div>
            <div class="drop-zone-hint">Supports images and text files</div>
        </div>
    `;
    document.body.appendChild(dropZone);
    
    function showDropZone() {
        if (dragCounter === 0) {
            dropZone.classList.add('active');
            isDragging = true;
        }
        dragCounter++;
    }
    
    function hideDropZone() {
        dragCounter--;
        if (dragCounter === 0) {
            dropZone.classList.remove('active');
            isDragging = false;
        }
    }
    
    function handleFiles(files) {
        if (!files || files.length === 0) return;
        
        Array.from(files).forEach(file => {
            handleFileUpload(file);
        });
    }
    
    function handleFileUpload(file) {
        // Show upload progress (Phase 5.1 Enhancement)
        const uploadNotification = showNotification(`Uploading ${file.name}...`, 'info', 0);
        
        if (file.type.startsWith('image/')) {
            // Handle image
            const reader = new FileReader();
            reader.onload = (event) => {
                const imageData = event.target.result;
                if (uploadNotification) uploadNotification.remove();
                processImage(imageData, file.name);
                showNotification(`Image "${file.name}" uploaded successfully`, 'success', 2000);
            };
            reader.onerror = () => {
                if (uploadNotification) uploadNotification.remove();
                showNotification(`Failed to read image: ${file.name}`, 'error', 3000);
            };
            reader.readAsDataURL(file);
        } else if (file.type.startsWith('text/') || 
                   file.name.endsWith('.txt') || 
                   file.name.endsWith('.md') || 
                   file.name.endsWith('.json')) {
            // Handle text file
            const reader = new FileReader();
            reader.onload = (event) => {
                const content = event.target.result;
                if (uploadNotification) uploadNotification.remove();
                if (messageInput) {
                    messageInput.value = content.substring(0, 1000);
                    autoResizeTextarea(messageInput);
                    messageInput.focus();
                    showNotification(`Text file "${file.name}" loaded into input`, 'success', 2000);
                }
            };
            reader.onerror = () => {
                if (uploadNotification) uploadNotification.remove();
                showNotification(`Failed to read text file: ${file.name}`, 'error', 3000);
            };
            reader.readAsText(file);
        } else {
            if (uploadNotification) uploadNotification.remove();
            showNotification(`Unsupported file type: ${file.name}`, 'error', 3000);
        }
    }
    
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        inputContainer.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
        
        if (chatContainer) {
            chatContainer.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        }
    });
    
    // Show drop zone on drag enter
    inputContainer.addEventListener('dragenter', (e) => {
        if (e.dataTransfer.types.includes('Files')) {
            showDropZone();
        }
    });
    
    if (chatContainer) {
        chatContainer.addEventListener('dragenter', (e) => {
            if (e.dataTransfer.types.includes('Files')) {
                showDropZone();
            }
        });
    }
    
    // Hide drop zone on drag leave
    inputContainer.addEventListener('dragleave', (e) => {
        if (!inputContainer.contains(e.relatedTarget)) {
            hideDropZone();
        }
    });
    
    if (chatContainer) {
        chatContainer.addEventListener('dragleave', (e) => {
            if (!chatContainer.contains(e.relatedTarget)) {
                hideDropZone();
            }
        });
    }
    
    // Handle drop
    inputContainer.addEventListener('drop', (e) => {
        hideDropZone();
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFiles(files);
        }
    });
    
    if (chatContainer) {
        chatContainer.addEventListener('drop', (e) => {
            hideDropZone();
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFiles(files);
            }
        });
    }
    
    // Global drag leave to handle drag leaving window
    document.addEventListener('dragleave', (e) => {
        if (e.clientX === 0 && e.clientY === 0) {
            hideDropZone();
        }
    });
}

// ============================================
// VIRTUAL SCROLLING (Phase 5.2)
// ============================================

let virtualScrollEnabled = false;
let messageObserver = null;

function initializeVirtualScrolling() {
    // Enable virtual scrolling for messages container if there are many messages
    const container = document.getElementById('messagesContainer');
    if (!container) return;
    
    // Check message count and enable virtual scrolling if needed
    const messages = container.querySelectorAll('.message, .message-group');
    if (messages.length > 50) {
        enableVirtualScrolling();
    }
    
    // Use Intersection Observer to enable/disable based on message count
    if (!messageObserver) {
        messageObserver = new MutationObserver(() => {
            const messages = container.querySelectorAll('.message, .message-group');
            if (messages.length > 50 && !virtualScrollEnabled) {
                enableVirtualScrolling();
            } else if (messages.length <= 50 && virtualScrollEnabled) {
                disableVirtualScrolling();
            }
        });
        
        messageObserver.observe(container, {
            childList: true,
            subtree: true
        });
    }
}

function enableVirtualScrolling() {
    if (virtualScrollEnabled) return;
    virtualScrollEnabled = true;
    
    const container = document.getElementById('messagesContainer');
    if (!container) return;
    
    container.classList.add('virtual-scroll-enabled');
    // Virtual scrolling implementation would go here
    // For now, we'll use CSS-based optimization
    container.style.contain = 'layout style paint';
    container.style.contentVisibility = 'auto';
}

function disableVirtualScrolling() {
    if (!virtualScrollEnabled) return;
    virtualScrollEnabled = false;
    
    const container = document.getElementById('messagesContainer');
    if (container) {
        container.classList.remove('virtual-scroll-enabled');
        container.style.contain = '';
        container.style.contentVisibility = '';
    }
}

// ============================================
// PWA CAPABILITIES (Phase 5.3)
// ============================================

function initializePWA() {
    // Register service worker
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/static/js/service-worker.js')
                .then((registration) => {
                    console.log('Service Worker registered:', registration.scope);
                    
                    // Check for updates
                    registration.addEventListener('updatefound', () => {
                        const newWorker = registration.installing;
                        if (newWorker) {
                            newWorker.addEventListener('statechange', () => {
                                if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                                    // New service worker available
                                    showNotification('New version available. Reload to update.', 'info', 5000);
                                }
                            });
                        }
                    });
                })
                .catch((error) => {
                    console.error('Service Worker registration failed:', error);
                });
        });
    }
    
    // Handle beforeinstallprompt for install banner
    let deferredPrompt;
    window.addEventListener('beforeinstallprompt', (e) => {
        e.preventDefault();
        deferredPrompt = e;
        // Show custom install button if needed
        showNotification('Install Atlas AI for a better experience', 'info', 5000);
    });
    
    // Listen for app installed
    window.addEventListener('appinstalled', () => {
        console.log('PWA installed');
        deferredPrompt = null;
    });
    
    // Handle online/offline events
    window.addEventListener('online', () => {
        showNotification('Connection restored', 'success', 2000);
    });
    
    window.addEventListener('offline', () => {
        showNotification('You are offline. Some features may be limited.', 'warning', 3000);
    });
}

// ============================================
// CONTEXT MENUS (Phase 5.4)
// ============================================

let contextMenu = null;
let contextMenuTarget = null;

function initializeContextMenus() {
    // Prevent default context menu
    document.addEventListener('contextmenu', (e) => {
        // Check if right-click is on a message or chat item
        const message = e.target.closest('.message');
        const chatItem = e.target.closest('.chat-item');
        
        if (message) {
            e.preventDefault();
            showMessageContextMenu(e, message);
        } else if (chatItem) {
            e.preventDefault();
            showChatContextMenu(e, chatItem);
        } else {
            // Hide any existing context menu
            hideContextMenu();
        }
    });
    
    // Close context menu on click outside
    document.addEventListener('click', (e) => {
        if (contextMenu && !contextMenu.contains(e.target)) {
            hideContextMenu();
        }
    });
    
    // Close context menu on Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && contextMenu) {
            hideContextMenu();
        }
    });
}

function showMessageContextMenu(e, messageElement) {
    hideContextMenu();
    
    const messageId = messageElement.id;
    const role = messageElement.classList.contains('user') ? 'user' : 'assistant';
    const messageContent = messageElement.querySelector('.message-content')?.textContent || '';
    
    contextMenu = document.createElement('div');
    contextMenu.className = 'context-menu';
    contextMenu.id = 'messageContextMenu';
    
    const menuItems = [
        {
            label: 'Copy',
            icon: 'copy',
            action: () => {
                navigator.clipboard.writeText(messageContent);
                showNotification('Message copied', 'success', 2000);
                hideContextMenu();
            }
        }
    ];
    
    if (role === 'user') {
        menuItems.push({
            label: 'Edit',
            icon: 'edit',
            action: () => {
                const messageContent = messageElement.querySelector('.message-content');
                if (messageContent) {
                    const currentText = messageContent.textContent || '';
                    const messageInput = document.getElementById('messageInput');
                    if (messageInput) {
                        messageInput.value = currentText;
                        messageInput.focus();
                        autoResizeTextarea(messageInput);
                        messageInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        showNotification('Message loaded into input. Edit and send to update.', 'info', 3000);
                    }
                }
                hideContextMenu();
            }
        });
        
        menuItems.push({
            label: 'Delete',
            icon: 'delete',
            action: () => {
                if (confirm('Delete this message?')) {
                    messageElement.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                    messageElement.style.opacity = '0';
                    messageElement.style.transform = 'translateX(-20px)';
                    setTimeout(() => {
                        messageElement.remove();
                        showNotification('Message deleted', 'success', 2000);
                    }, 300);
                    hideContextMenu();
                }
            },
            danger: true
        });
    } else {
        menuItems.push({
            label: 'Regenerate',
            icon: 'refresh',
            action: () => {
                const previousUserMessage = messageElement.previousElementSibling;
                if (previousUserMessage && previousUserMessage.classList.contains('user')) {
                    const userMessageContent = previousUserMessage.querySelector('.message-content')?.textContent || '';
                    if (userMessageContent) {
                        messageElement.style.transition = 'opacity 0.3s ease';
                        messageElement.style.opacity = '0';
                        setTimeout(() => {
                            messageElement.remove();
                            const messageInput = document.getElementById('messageInput');
                            if (messageInput) {
                                messageInput.value = userMessageContent;
                                autoResizeTextarea(messageInput);
                                setTimeout(() => {
                                    handleSendMessage();
                                }, 100);
                            }
                        }, 300);
                    }
                } else {
                    showNotification('Cannot regenerate: previous user message not found', 'warning', 3000);
                }
                hideContextMenu();
            }
        });
        
        menuItems.push({
            label: 'Copy Code Blocks',
            icon: 'copy',
            action: () => {
                const codeBlocks = messageElement.querySelectorAll('pre code, code');
                if (codeBlocks.length > 0) {
                    const allCode = Array.from(codeBlocks).map(block => block.textContent).join('\n\n');
                    navigator.clipboard.writeText(allCode).then(() => {
                        showNotification(`Copied ${codeBlocks.length} code block(s)`, 'success', 2000);
                    }).catch(() => {
                        showNotification('Failed to copy code blocks', 'error', 2000);
                    });
                } else {
                    showNotification('No code blocks found in this message', 'info', 2000);
                }
                hideContextMenu();
            }
        });
    }
    
    menuItems.push({ type: 'separator' });
    
    menuItems.push({
        label: 'Select All',
        icon: 'select',
        action: () => {
            const selection = window.getSelection();
            const range = document.createRange();
            range.selectNodeContents(messageElement.querySelector('.message-content'));
            selection.removeAllRanges();
            selection.addRange(range);
            hideContextMenu();
        }
    });
    
    contextMenu.innerHTML = menuItems.map(item => {
        if (item.type === 'separator') {
            return '<div class="context-menu-separator"></div>';
        }
        return `
            <button class="context-menu-item ${item.danger ? 'context-menu-item-danger' : ''}" data-action="${item.label.toLowerCase()}">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    ${getContextMenuIcon(item.icon)}
                </svg>
                <span>${item.label}</span>
            </button>
        `;
    }).join('');
    
    // Add event listeners
    menuItems.forEach(item => {
        if (item.action) {
            const button = contextMenu.querySelector(`[data-action="${item.label.toLowerCase()}"]`);
            if (button) {
                button.addEventListener('click', item.action);
            }
        }
    });
    
    document.body.appendChild(contextMenu);
    contextMenuTarget = messageElement;
    
    // Position menu
    positionContextMenu(e, contextMenu);
}

function showChatContextMenu(e, chatElement) {
    hideContextMenu();
    
    const chatId = chatElement.dataset.chatId;
    const chatName = chatElement.querySelector('.chat-item-name')?.textContent || 'Chat';
    
    contextMenu = document.createElement('div');
    contextMenu.className = 'context-menu';
    contextMenu.id = 'chatContextMenu';
    
    const menuItems = [
        {
            label: 'Open',
            icon: 'open',
            action: () => {
                if (chatId) {
                    loadChat(chatId);
                }
                hideContextMenu();
            }
        },
        {
            label: 'Rename',
            icon: 'edit',
            action: async () => {
                const newName = prompt('Enter new chat name:', chatName);
                if (newName && newName.trim() && newName !== chatName) {
                    try {
                        const response = await fetch(`/api/chats/${chatId}`, {
                            method: 'PATCH',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ name: newName.trim() })
                        });
                        if (response.ok) {
                            showNotification('Chat renamed', 'success', 2000);
                            loadChats();
                        } else {
                            showNotification('Failed to rename chat', 'error', 2000);
                        }
                    } catch (error) {
                        console.error('Error renaming chat:', error);
                        showNotification('Failed to rename chat', 'error', 2000);
                    }
                }
                hideContextMenu();
            }
        },
        { type: 'separator' },
        {
            label: 'Export',
            icon: 'export',
            action: () => {
                if (chatId) {
                    exportChat(chatId);
                }
                hideContextMenu();
            }
        },
        { type: 'separator' },
        {
            label: 'Delete',
            icon: 'delete',
            action: () => {
                if (confirm(`Delete "${chatName}"?`)) {
                    if (chatId) {
                        deleteChat(chatId);
                    }
                    hideContextMenu();
                }
            },
            danger: true
        }
    ];
    
    contextMenu.innerHTML = menuItems.map(item => {
        if (item.type === 'separator') {
            return '<div class="context-menu-separator"></div>';
        }
        return `
            <button class="context-menu-item ${item.danger ? 'context-menu-item-danger' : ''}" data-action="${item.label.toLowerCase()}">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    ${getContextMenuIcon(item.icon)}
                </svg>
                <span>${item.label}</span>
            </button>
        `;
    }).join('');
    
    // Add event listeners
    menuItems.forEach(item => {
        if (item.action) {
            const button = contextMenu.querySelector(`[data-action="${item.label.toLowerCase()}"]`);
            if (button) {
                button.addEventListener('click', item.action);
            }
        }
    });
    
    document.body.appendChild(contextMenu);
    contextMenuTarget = chatElement;
    
    // Position menu
    positionContextMenu(e, contextMenu);
}

function positionContextMenu(e, menu) {
    const menuRect = menu.getBoundingClientRect();
    const viewportWidth = window.innerWidth;
    const viewportHeight = window.innerHeight;
    
    let left = e.clientX;
    let top = e.clientY;
    
    // Adjust horizontal position
    if (left + menuRect.width > viewportWidth) {
        left = viewportWidth - menuRect.width - 10;
    }
    if (left < 10) {
        left = 10;
    }
    
    // Adjust vertical position
    if (top + menuRect.height > viewportHeight) {
        top = viewportHeight - menuRect.height - 10;
    }
    if (top < 10) {
        top = 10;
    }
    
    menu.style.left = `${left}px`;
    menu.style.top = `${top}px`;
}

function hideContextMenu() {
    if (contextMenu) {
        contextMenu.remove();
        contextMenu = null;
        contextMenuTarget = null;
    }
}

function getContextMenuIcon(iconType) {
    const icons = {
        copy: '<path d="M5.5 4.5H11.5V10.5H5.5V4.5Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M4.5 6.5C4.5 5.94772 4.94772 5.5 5.5 5.5H10.5V10.5C10.5 11.0523 10.0523 11.5 9.5 11.5H5.5C4.94772 11.5 4.5 11.0523 4.5 10.5V6.5Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>',
        edit: '<path d="M11 4H4C3.44772 4 3 4.44772 3 5V12C3 12.5523 3.44772 13 4 13H11C11.5523 13 12 12.5523 12 12V5C12 4.44772 11.5523 4 11 4Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M8.5 6.5L9.5 7.5L6.5 10.5H5.5V9.5L8.5 6.5Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>',
        delete: '<path d="M6.5 6.5V12.5M9.5 6.5V12.5M4.5 4.5H11.5M3 6.5H13M11 4.5V6.5C11 7.05228 10.5523 7.5 10 7.5H6C5.44772 7.5 5 7.05228 5 6.5V4.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>',
        refresh: '<path d="M13 3C13 3 11.5 5.5 8 5.5C5.51472 5.5 3.5 7.51472 3.5 10C3.5 12.4853 5.51472 14.5 8 14.5C10.4853 14.5 12.5 12.4853 12.5 10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M10 3L13 3L13 6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>',
        select: '<path d="M3 4.5H13M3 8H13M3 11.5H13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>',
        open: '<path d="M6.5 4.5H11.5C12.0523 4.5 12.5 4.94772 12.5 5.5V10.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M8 6.5L12.5 11L8 15.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>',
        export: '<path d="M4.5 4.5H11.5C12.0523 4.5 12.5 4.94772 12.5 5.5V10.5M10.5 12.5L12.5 10.5L10.5 8.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/><path d="M12.5 10.5H8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>'
    };
    return icons[iconType] || icons.copy;
}

// Smart Suggestions System
function initializeSmartSuggestions() {
    const messageInput = document.getElementById('messageInput');
    if (!messageInput) return;
    
    let suggestionsContainer = document.getElementById('smartSuggestions');
    if (!suggestionsContainer) {
        suggestionsContainer = document.createElement('div');
        suggestionsContainer.id = 'smartSuggestions';
        suggestionsContainer.className = 'smart-suggestions';
        messageInput.parentElement.appendChild(suggestionsContainer);
    }
    
    messageInput.addEventListener('input', debounce(handleInputChange, 300));
    messageInput.addEventListener('keydown', handleSuggestionKeydown);
}

function handleInputChange(e) {
    const query = e.target.value.trim();
    if (query.length < 2) {
        hideSuggestions();
        return;
    }
    
    generateSuggestions(query);
}

function generateSuggestions(query) {
    // Common suggestions based on query
    const commonSuggestions = [
        'Explain',
        'Summarize',
        'Write',
        'Create',
        'Help me with',
        'What is',
        'How to',
        'Tell me about',
    ];
    
    // Filter and generate suggestions
    smartSuggestions = commonSuggestions
        .filter(s => s.toLowerCase().includes(query.toLowerCase()) || query.toLowerCase().includes(s.toLowerCase()))
        .slice(0, 5)
        .map(s => `${s} ${query}`);
    
    showSuggestions(smartSuggestions);
}

function showSuggestions(suggestions) {
    const container = document.getElementById('smartSuggestions');
    if (!container || suggestions.length === 0) {
        hideSuggestions();
        return;
    }
    
    container.innerHTML = suggestions.map((suggestion, index) => `
        <div class="suggestion-item" data-index="${index}" onclick="applySuggestion('${escapeHtml(suggestion)}')">
            ${escapeHtml(suggestion)}
        </div>
    `).join('');
    
    container.style.display = 'block';
}

function hideSuggestions() {
    const container = document.getElementById('smartSuggestions');
    if (container) {
        container.style.display = 'none';
    }
}

function applySuggestion(suggestion) {
    const messageInput = document.getElementById('messageInput');
    if (messageInput) {
        messageInput.value = suggestion;
        messageInput.focus();
        hideSuggestions();
    }
}

function handleSuggestionKeydown(e) {
    const container = document.getElementById('smartSuggestions');
    if (!container || container.style.display === 'none') return;
    
    const items = container.querySelectorAll('.suggestion-item');
    const activeItem = container.querySelector('.suggestion-item.active');
    let currentIndex = activeItem ? parseInt(activeItem.dataset.index) : -1;
    
    if (e.key === 'ArrowDown') {
        e.preventDefault();
        currentIndex = (currentIndex + 1) % items.length;
        items.forEach(item => item.classList.remove('active'));
        items[currentIndex].classList.add('active');
    } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        currentIndex = currentIndex <= 0 ? items.length - 1 : currentIndex - 1;
        items.forEach(item => item.classList.remove('active'));
        items[currentIndex].classList.add('active');
    } else if (e.key === 'Enter' && activeItem) {
        e.preventDefault();
        applySuggestion(activeItem.textContent);
    } else if (e.key === 'Escape') {
        hideSuggestions();
    }
}

// Notification System
function initializeNotifications() {
    // Create notification container if it doesn't exist
    if (!document.getElementById('notificationsContainer')) {
        const container = document.createElement('div');
        container.id = 'notificationsContainer';
        container.className = 'notifications-container';
        document.body.appendChild(container);
    }
}

function showNotification(message, type = 'info', duration = 5000) {
    const container = document.getElementById('notificationsContainer');
    if (!container) return null;
    
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-message">${escapeHtml(message)}</span>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path d="M12 4L4 12M4 4L12 12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
            </button>
        </div>
    `;
    
    container.appendChild(notification);
    
    // Animate in (Phase 1 Enhancement - smoother animation)
    requestAnimationFrame(() => {
        notification.classList.add('show');
    });
    
    // Auto remove
    if (duration > 0) {
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, duration);
    }
    
    return notification;
}

// Quick Actions Menu
function initializeQuickActions() {
    // Add quick actions button to input area
    const inputWrapper = document.querySelector('.input-wrapper');
    if (inputWrapper && !document.getElementById('quickActionsBtn')) {
        const quickActionsBtn = document.createElement('button');
        quickActionsBtn.id = 'quickActionsBtn';
        quickActionsBtn.className = 'input-icon-btn quick-actions-btn';
        quickActionsBtn.title = 'Quick Actions';
        quickActionsBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                <path d="M10 2.5C6.96243 2.5 4.5 4.96243 4.5 8C4.5 9.92209 5.56683 11.5852 7.14944 12.4634C7.38096 12.5911 7.5 12.8458 7.5 13.107V14C7.5 14.5523 7.94772 15 8.5 15H11.5C12.0523 15 12.5 14.5523 12.5 14V13.107C12.5 12.8458 12.619 12.5911 12.8506 12.4634C14.4332 11.5852 15.5 9.92209 15.5 8C15.5 4.96243 13.0376 2.5 10 2.5Z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M8 17H12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                <path d="M9 19H11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
        `;
        quickActionsBtn.addEventListener('click', toggleQuickActionsMenu);
        
        const inputLeftActions = document.querySelector('.input-left-actions');
        if (inputLeftActions) {
            inputLeftActions.appendChild(quickActionsBtn);
        }
    }
}

function toggleQuickActionsMenu() {
    if (quickActionsMenu && quickActionsMenu.style.display !== 'none') {
        quickActionsMenu.remove();
        quickActionsMenu = null;
        return;
    }
    
    const actions = [
        { label: 'New Chat', icon: 'plus', action: () => startNewChat() },
        { label: 'Export Chat', icon: 'download', action: () => currentChatId && exportChat(currentChatId) },
        { label: 'Analytics', icon: 'chart', action: () => openAnalyticsModal() },
        { label: 'Settings', icon: 'settings', action: () => openSettingsModal() },
        { label: 'Help', icon: 'help', action: () => openHelpModal() },
    ];
    
    quickActionsMenu = document.createElement('div');
    quickActionsMenu.className = 'quick-actions-menu';
    quickActionsMenu.innerHTML = actions.map(action => `
        <button class="quick-action-item" onclick="this.closest('.quick-actions-menu').remove(); (${action.action.toString()})()">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                ${getActionIcon(action.icon)}
            </svg>
            <span>${action.label}</span>
        </button>
    `).join('');
    
    const btn = document.getElementById('quickActionsBtn');
    if (btn) {
        const rect = btn.getBoundingClientRect();
        quickActionsMenu.style.top = `${rect.bottom + 8}px`;
        quickActionsMenu.style.left = `${rect.left}px`;
        document.body.appendChild(quickActionsMenu);
        
        // Close on outside click
        setTimeout(() => {
            document.addEventListener('click', function closeMenu(e) {
                if (!quickActionsMenu.contains(e.target) && e.target !== btn) {
                    quickActionsMenu.remove();
                    document.removeEventListener('click', closeMenu);
                }
            }, { once: true });
        }, 10);
    }
}

function getActionIcon(icon) {
    const icons = {
        'plus': '<path d="M8 3V13M3 8H13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>',
        'download': '<path d="M8 2V10M8 10L5 7M8 10L11 7M3 12V13C3 13.5523 3.44772 14 4 14H12C12.5523 14 13 13.5523 13 13V12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>',
        'search': '<circle cx="7" cy="7" r="4" stroke="currentColor" stroke-width="1.5"/><path d="M10 10L13 13" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>',
        'settings': '<circle cx="8" cy="8" r="2" stroke="currentColor" stroke-width="1.5"/><path d="M8 2V3M8 13V14M14 8H13M3 8H2M12.5 3.5L11.9 4.1M4.1 11.9L3.5 12.5M12.5 12.5L11.9 11.9M4.1 4.1L3.5 3.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>',
        'help': '<circle cx="8" cy="8" r="6" stroke="currentColor" stroke-width="1.5"/><path d="M6 6C6 4.89543 6.89543 4 8 4C9.10457 4 10 4.89543 10 6C10 7.10457 9.10457 8 8 8V10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/><circle cx="8" cy="12" r="1" fill="currentColor"/>',
        'chart': '<path d="M3 12L6 9L9 11L13 5M3 12V14H13V5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>',
    };
    return icons[icon] || '';
}

// Export/Import System
function initializeExportImport() {
    // Add export/import to settings or quick actions
    // This is handled in the quick actions menu
}

async function exportChat(chatId, format = 'json') {
    try {
        let response;

        if (isBetaFeatureEnabled('enhanced_exports') && ['pdf', 'markdown', 'html'].includes(format)) {
            // Use beta enhanced export API
            response = await fetch(`/api/beta/chats/${chatId}/export/${format}`, {
                headers: { 'X-Beta-Mode': 'true' }
            });
        } else {
            // Use standard JSON export
            response = await fetch(`/api/chats/${chatId}`);
            const data = await response.json();

            const exportData = {
                version: '1.4.2',
                exported_at: new Date().toISOString(),
                chat: data,
            };

            const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `atlas-chat-${chatId}-${Date.now()}.json`;
            a.click();
            URL.revokeObjectURL(url);

            showNotification('Chat exported successfully!', 'success');
            return;
        }

        if (!response.ok) {
            throw new Error('Export failed');
        }

        // Handle file download for enhanced formats
        const contentType = response.headers.get('content-type');
        const contentDisposition = response.headers.get('content-disposition');
        const filename = contentDisposition
            ? contentDisposition.split('filename=')[1].replace(/"/g, '')
            : `atlas-chat-${chatId}-${Date.now()}.${format}`;

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);

        showNotification(`Chat exported as ${format.toUpperCase()}!`, 'success');
    } catch (error) {
        console.error('Error exporting chat:', error);
        showNotification('Failed to export chat', 'error');
    }
}

async function importChat(file) {
    try {
        const text = await file.text();
        const data = JSON.parse(text);
        
        if (!data.chat || !data.chat.messages) {
            throw new Error('Invalid chat file format');
        }
        
        // Create new chat with imported messages
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                messages: data.chat.messages,
                name: data.chat.name || 'Imported Chat',
            }),
        });
        
        const result = await response.json();
        if (result.chat_id) {
            showNotification('Chat imported successfully!', 'success');
            loadChats();
            loadChat(result.chat_id);
        }
    } catch (error) {
        console.error('Error importing chat:', error);
        showNotification('Failed to import chat', 'error');
    }
}

// Utility Functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Analytics Dashboard
function openAnalyticsModal() {
    const modal = document.getElementById('analyticsModal');
    if (modal) {
        modal.style.display = 'flex';
        loadAnalytics();
    }
}

function closeAnalyticsModal() {
    const modal = document.getElementById('analyticsModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

async function loadAnalytics() {
    const dashboard = document.getElementById('analyticsDashboard');
    if (!dashboard) return;
    
    try {
        dashboard.innerHTML = '<div class="chats-loading">Loading analytics...</div>';
        
        const response = await fetch('/api/analytics');
        const data = await response.json();
        
        // Format dates for display
        const dates = Object.keys(data.chats_by_date || {}).sort();
        const dateLabels = dates.map(d => {
            const date = new Date(d);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        });
        const dateValues = dates.map(d => data.chats_by_date[d]);
        
        dashboard.innerHTML = `
            <div class="analytics-grid">
                <div class="analytics-card">
                    <div class="analytics-card-title">Total Chats</div>
                    <div class="analytics-card-value">${data.total_chats || 0}</div>
                </div>
                <div class="analytics-card">
                    <div class="analytics-card-title">Total Messages</div>
                    <div class="analytics-card-value">${data.total_messages || 0}</div>
                </div>
                <div class="analytics-card">
                    <div class="analytics-card-title">User Messages</div>
                    <div class="analytics-card-value">${data.user_messages || 0}</div>
                </div>
                <div class="analytics-card">
                    <div class="analytics-card-title">Assistant Messages</div>
                    <div class="analytics-card-value">${data.assistant_messages || 0}</div>
                </div>
                <div class="analytics-card">
                    <div class="analytics-card-title">Avg Messages/Chat</div>
                    <div class="analytics-card-value">${data.average_messages_per_chat || 0}</div>
                </div>
            </div>
            <div class="analytics-chart">
                <h3>Chats Over Time</h3>
                <div class="chart-container">
                    ${dates.length > 0 ? `
                        <div class="chart-bars">
                            ${dates.map((date, i) => {
                                const maxValue = Math.max(...dateValues);
                                const height = maxValue > 0 ? (dateValues[i] / maxValue) * 100 : 0;
                                return `
                                    <div class="chart-bar-item">
                                        <div class="chart-bar" style="height: ${height}%">
                                            <span class="chart-bar-value">${dateValues[i]}</span>
                                        </div>
                                        <div class="chart-bar-label">${dateLabels[i]}</div>
                                    </div>
                                `;
                            }).join('')}
                        </div>
                    ` : '<p class="text-muted">No data available</p>'}
                </div>
            </div>
        `;
    } catch (error) {
        console.error('Error loading analytics:', error);
        dashboard.innerHTML = '<div class="chats-loading">Error loading analytics</div>';
    }
}

// Initialize analytics on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        const closeAnalyticsBtn = document.getElementById('closeAnalyticsModal');
        if (closeAnalyticsBtn) {
            closeAnalyticsBtn.addEventListener('click', closeAnalyticsModal);
        }
        
        // Add keyboard shortcut for analytics (Ctrl+Shift+A)
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'A') {
                e.preventDefault();
                openAnalyticsModal();
            }
        });
    });
} else {
    const closeAnalyticsBtn = document.getElementById('closeAnalyticsModal');
    if (closeAnalyticsBtn) {
        closeAnalyticsBtn.addEventListener('click', closeAnalyticsModal);
    }
    
    document.addEventListener('keydown', (e) => {
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'A') {
            e.preventDefault();
            openAnalyticsModal();
        }
    });
}

// Audio Stream Lifecycle Manager (v4.1.0)
let audioStreamManager = {
    stream: null,
    healthCheckInterval: null,
    recoveryAttempts: 0,
    lastHealthCheck: 0,
    streamHealth: 'unknown', // 'healthy', 'degraded', 'failed', 'unknown'

    /**
     * Initialize stream manager
     */
    initialize() {
        console.log('[StreamManager] Initializing audio stream manager');
        this.stream = null;
        this.recoveryAttempts = 0;
        this.streamHealth = 'unknown';
        this.stopHealthMonitoring();
    },

    /**
     * Set the active audio stream
     * @param {MediaStream} stream - The audio stream
     */
    setStream(stream) {
        console.log('[StreamManager] Setting new audio stream');

        // Clean up existing stream
        if (this.stream && this.stream !== stream) {
            this.releaseStream();
        }

        this.stream = stream;
        this.recoveryAttempts = 0;
        this.streamHealth = 'healthy';
        this.lastHealthCheck = Date.now();

        // Ensure stream stays active
        this.preserveStream();

        // Start health monitoring
        this.startHealthMonitoring();

        console.log('[StreamManager] ✅ Audio stream set and monitoring started');
    },

    /**
     * Preserve stream from garbage collection and ensure tracks stay active
     */
    preserveStream() {
        if (!this.stream) return;

        try {
            const tracks = this.stream.getAudioTracks();
            if (tracks.length > 0) {
                // Ensure at least one track is active
                const activeTrack = tracks.find(t => t.readyState === 'live') || tracks[0];
                if (activeTrack) {
                    activeTrack.enabled = true;
                    activeTrack.muted = false;

                    // Add event listeners for track state changes
                    activeTrack.onended = () => {
                        console.warn('[StreamManager] Audio track ended unexpectedly');
                        this.handleTrackFailure();
                    };

                    activeTrack.onmute = () => {
                        console.warn('[StreamManager] Audio track muted unexpectedly');
                        // Try to unmute
                        setTimeout(() => {
                            if (activeTrack.muted) {
                                activeTrack.muted = false;
                                console.log('[StreamManager] Attempted to unmute track');
                            }
                        }, 100);
                    };
                }
            }

            // Keep global reference to prevent garbage collection
            window.poseidonAudioStream = this.stream;

        } catch (error) {
            console.error('[StreamManager] Error preserving stream:', error);
        }
    },

    /**
     * Start periodic health monitoring
     */
    startHealthMonitoring() {
        this.stopHealthMonitoring(); // Stop any existing monitoring

        this.healthCheckInterval = setInterval(() => {
            this.performHealthCheck();
        }, 5000); // Check every 5 seconds

        console.log('[StreamManager] Health monitoring started');
    },

    /**
     * Stop health monitoring
     */
    stopHealthMonitoring() {
        if (this.healthCheckInterval) {
            clearInterval(this.healthCheckInterval);
            this.healthCheckInterval = null;
            console.log('[StreamManager] Health monitoring stopped');
        }
    },

    /**
     * Perform a health check on the audio stream
     */
    performHealthCheck() {
        if (!this.stream) {
            this.streamHealth = 'failed';
            return;
        }

        try {
            const now = Date.now();
            const tracks = this.stream.getAudioTracks();
            const activeTracks = tracks.filter(t =>
                t.readyState === 'live' && t.enabled && !t.muted
            );

            if (!this.stream.active || activeTracks.length === 0) {
                console.warn('[StreamManager] Health check failed - stream not active or no active tracks');
                this.streamHealth = 'failed';
                this.handleStreamFailure();
                return;
            }

            // Check for track state changes
            const endedTracks = tracks.filter(t => t.readyState === 'ended');
            if (endedTracks.length > 0) {
                console.warn(`[StreamManager] ${endedTracks.length} track(s) have ended`);
                this.streamHealth = 'degraded';
            } else {
                this.streamHealth = 'healthy';
            }

            this.lastHealthCheck = now;
            
            // Update state manager with current stream health
            if (poseidonStateManager) {
                poseidonStateManager.updateAudioState({ 
                    streamActive: this.stream.active && activeTracks.length > 0 
                });
            }

        } catch (error) {
            console.error('[StreamManager] Error during health check:', error);
            this.streamHealth = 'failed';
            this.handleStreamFailure();
        }
    },

    /**
     * Handle stream failure with automatic recovery (v4.3.0: Enhanced with error tracking)
     */
    async handleStreamFailure() {
        if (this.recoveryAttempts >= 3) {
            console.error('[StreamManager] ❌ Max stream recovery attempts reached');
            this.streamHealth = 'failed';
            
            // Record error with error tracker
            const error = new Error('Stream recovery failed after max attempts');
            poseidonErrorTracker.recordError(error, {
                context: 'stream-recovery',
                recoveryAttempts: this.recoveryAttempts,
                streamHealth: this.streamHealth
            });
            
            // Notify error handler
            if (poseidonActive) {
                updatePoseidonStatus('ready', 'Audio stream failed');
            }
            
            // Update state manager
            if (poseidonStateManager) {
                poseidonStateManager.updateAudioState({ streamActive: false });
            }
            
            return;
        }

        console.log(`[StreamManager] Attempting stream recovery (attempt ${this.recoveryAttempts + 1})`);
        this.recoveryAttempts++;

        try {
            // Try to re-enable existing tracks
            if (this.stream) {
                const tracks = this.stream.getAudioTracks();
                tracks.forEach(track => {
                    if (track.readyState !== 'ended') {
                        track.enabled = true;
                        track.muted = false;
                    }
                });

                // Wait and check if recovery worked
                await new Promise(resolve => setTimeout(resolve, 1000));

                const activeTracks = tracks.filter(t =>
                    t.readyState === 'live' && t.enabled && !t.muted
                );

                if (activeTracks.length > 0 && this.stream.active) {
                    console.log('[StreamManager] ✅ Stream recovered by re-enabling tracks');
                    this.recoveryAttempts = 0;
                    this.streamHealth = 'healthy';
                    
                    // Update state manager
                    if (poseidonStateManager) {
                        poseidonStateManager.updateAudioState({ streamActive: true });
                    }
                    
                    return;
                }
            }

            // If re-enabling didn't work, request new stream
            console.log('[StreamManager] Re-enabling failed, requesting new stream');
            const newStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });

            this.setStream(newStream);
            console.log('[StreamManager] ✅ Stream recovered with new stream');
            
            // Update state manager
            if (poseidonStateManager) {
                poseidonStateManager.updateAudioState({ streamActive: true });
            }

        } catch (error) {
            console.error('[StreamManager] ❌ Stream recovery failed:', error);
            
            // Record error with error tracker
            poseidonErrorTracker.recordError(error, {
                context: 'stream-recovery',
                attempt: this.recoveryAttempts
            });
            
            // Exponential backoff for retries
            const backoffDelay = Math.min(1000 * Math.pow(2, this.recoveryAttempts), 10000);
            setTimeout(() => {
                // Only retry if circuit breaker is not active
                const isElectron = window.electronAPI !== undefined;
                if (!poseidonErrorTracker.circuitBreakerActive || isElectron) {
                    this.handleStreamFailure();
                } else {
                    console.warn('[StreamManager] Circuit breaker active - stopping stream recovery');
                }
            }, backoffDelay);
        }
    },

    /**
     * Handle individual track failure
     */
    handleTrackFailure() {
        console.warn('[StreamManager] Track failure detected');
        if (this.stream) {
            const tracks = this.stream.getAudioTracks();
            const activeTracks = tracks.filter(t =>
                t.readyState === 'live' && t.enabled && !t.muted
            );

            if (activeTracks.length === 0) {
                console.error('[StreamManager] No active tracks remaining');
                this.handleStreamFailure();
            }
        }
    },

    /**
     * Release the current stream and clean up resources
     */
    releaseStream() {
        console.log('[StreamManager] Releasing audio stream');

        this.stopHealthMonitoring();

        if (this.stream) {
            try {
                // Stop all tracks
                const tracks = this.stream.getTracks();
                tracks.forEach(track => {
                    try {
                        track.stop();
                        console.log('[StreamManager] Stopped track:', track.kind, track.label);
                    } catch (e) {
                        console.warn('[StreamManager] Error stopping track:', e);
                    }
                });
            } catch (error) {
                console.warn('[StreamManager] Error stopping stream tracks:', error);
            }

            this.stream = null;
        }

        // Clear global reference
        if (window.poseidonAudioStream) {
            window.poseidonAudioStream = null;
        }

        this.streamHealth = 'unknown';
        this.recoveryAttempts = 0;

        console.log('[StreamManager] ✅ Audio stream released');
    },

    /**
     * Get stream health status
     * @returns {Object} Health status information
     */
    getHealthStatus() {
        return {
            health: this.streamHealth,
            hasStream: !!this.stream,
            isActive: this.stream?.active || false,
            activeTracks: this.stream ? this.stream.getAudioTracks().filter(t =>
                t.readyState === 'live' && t.enabled && !t.muted
            ).length : 0,
            totalTracks: this.stream ? this.stream.getAudioTracks().length : 0,
            recoveryAttempts: this.recoveryAttempts,
            lastHealthCheck: this.lastHealthCheck
        };
    }
};

