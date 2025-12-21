// Dev Atlas - Cursor Agents Style JavaScript

class DevAtlas {
    constructor() {
        this.messagesContainer = document.getElementById('messages');
        this.debugContent = document.getElementById('debugContent');
        this.promptForm = document.getElementById('promptForm');
        this.promptInput = document.getElementById('promptInput');
        this.clearBtn = document.getElementById('clearBtn');
        this.toggleDebug = document.getElementById('toggleDebug');
        this.debugPanel = document.querySelector('.debug-panel');
        
        this.isDebugCollapsed = false;
        this.isLoading = false;
        this.startTime = null;
        this.codeStats = { added: 0, removed: 0 };
        
        this.init();
    }
    
    init() {
        const welcomeMsg = this.messagesContainer.querySelector('.welcome-message');
        if (welcomeMsg) {
            this.welcomeMsg = welcomeMsg;
        }
        
        this.promptForm.addEventListener('submit', (e) => this.handleSubmit(e));
        this.clearBtn.addEventListener('click', () => this.clearChat());
        this.toggleDebug.addEventListener('click', () => this.toggleDebugPanel());
        
        this.promptInput.focus();
        
        // Update metrics periodically
        setInterval(() => this.updateMetrics(), 1000);
    }
    
    updateMetrics() {
        const timeElapsed = document.getElementById('timeElapsed');
        const codeStats = document.getElementById('codeStats');
        
        if (this.startTime && this.isLoading) {
            const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            timeElapsed.textContent = minutes > 0 ? `${minutes}m` : `${seconds}s`;
        } else {
            timeElapsed.textContent = '--';
        }
        
        codeStats.textContent = `+${this.codeStats.added} -${this.codeStats.removed}`;
    }
    
    handleSubmit(e) {
        e.preventDefault();
        
        const message = this.promptInput.value.trim();
        if (!message || this.isLoading) return;
        
        if (this.welcomeMsg) {
            this.welcomeMsg.remove();
            this.welcomeMsg = null;
        }
        
        this.addMessage('user', message);
        
        this.promptInput.value = '';
        this.promptInput.disabled = true;
        this.isLoading = true;
        this.startTime = Date.now();
        this.codeStats = { added: 0, removed: 0 };
        
        this.clearDebug();
        this.addActionLog('info', 'Initializing', 'Preparing to process your query and analyze the request...');
        
        this.sendMessage(message);
    }
    
    async sendMessage(message) {
        try {
            const response = await fetch('/api/dev-chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            this.addMessage('assistant', data.response || 'No response received');
            
            if (data.debug_log && Array.isArray(data.debug_log)) {
                data.debug_log.forEach(step => {
                    this.addActionLogEnhanced(
                        step.status || 'info',
                        step.step,
                        step.data
                    );
                });
            }
            
            if (data.knowledge_items && data.knowledge_items.length > 0) {
                this.addActionLogEnhanced('success', 'Knowledge Retrieved from Brain', {
                    count: data.knowledge_items.length,
                    items: data.knowledge_items
                });
            }
            
            if (data.search_results && data.search_results.length > 0) {
                this.addActionLogEnhanced('success', 'Web Search Results', {
                    count: data.search_results.length,
                    results: data.search_results
                });
            }
            
        } catch (error) {
            console.error('Error:', error);
            this.addMessage('assistant', `Error: ${error.message}`);
            this.addActionLogEnhanced('error', 'Request Failed', { error: error.message });
        } finally {
            this.promptInput.disabled = false;
            this.isLoading = false;
            this.startTime = null;
            this.promptInput.focus();
        }
    }
    
    addMessage(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const header = document.createElement('div');
        header.className = 'message-header';
        header.innerHTML = `
            <i class="fas ${role === 'user' ? 'fa-user' : 'fa-robot'}"></i>
            <span>${role === 'user' ? 'You' : 'Atlas'}</span>
        `;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        contentDiv.textContent = content;
        
        messageDiv.appendChild(header);
        messageDiv.appendChild(contentDiv);
        
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    formatStepDescription(stepName, data) {
        const descriptions = {
            'Request Received': () => {
                const msg = data?.message || 'query';
                return `Received your query: "${msg.substring(0, 100)}${msg.length > 100 ? '...' : ''}"`;
            },
            'Query Normalized': () => {
                const original = data?.original || '';
                const normalized = data?.normalized || '';
                if (original === normalized) {
                    return `Query is already in standard format: "${normalized}"`;
                }
                return `Normalized query from "${original}" to "${normalized}" for better processing`;
            },
            'Conversational Analysis': () => {
                const isConv = data?.is_conversational || false;
                const confidence = data?.confidence || 0;
                const requiresSearch = data?.requires_search || false;
                
                if (isConv) {
                    return `Detected conversational query (confidence: ${(confidence * 100).toFixed(0)}%). This appears to be a casual conversation rather than a factual question.`;
                }
                if (requiresSearch) {
                    return `This is a factual query that requires web search to find accurate information.`;
                }
                return `Analyzed query type and context. Ready to process.`;
            },
            'Starting Web Search': () => {
                const query = data?.query || '';
                return `Searching the web for: "${query}". Checking multiple search engines (Google, Bing, DuckDuckGo, Wikipedia) to find the most relevant information.`;
            },
            'Web Search Complete': () => {
                const count = data?.results_count || 0;
                const results = data?.results || [];
                const sources = data?.sources || {};
                
                let desc = `Found ${count} search result${count !== 1 ? 's' : ''} from multiple search engines.`;
                
                if (Object.keys(sources).length > 0) {
                    desc += ` Sources: `;
                    const sourceList = [];
                    if (sources.google) sourceList.push(`${sources.google} from Google`);
                    if (sources.bing) sourceList.push(`${sources.bing} from Bing`);
                    if (sources.duckduckgo) sourceList.push(`${sources.duckduckgo} from DuckDuckGo`);
                    if (sources.wikipedia) sourceList.push(`${sources.wikipedia} from Wikipedia`);
                    if (sources.brave) sourceList.push(`${sources.brave} from Brave`);
                    desc += sourceList.join(', ') + '.';
                }
                
                return desc;
            },
            'Retrieving Knowledge from Brain': () => {
                const query = data?.query || '';
                return `Searching internal knowledge base for: "${query}". Checking stored information that Atlas has learned from previous conversations.`;
            },
            'Knowledge Retrieved from Brain': () => {
                const count = data?.items_count || data?.count || 0;
                const items = data?.items || [];
                let desc = `Found ${count} relevant knowledge item${count !== 1 ? 's' : ''} in internal knowledge base.`;
                
                if (items.length > 0) {
                    desc += ` Top matches:\n`;
                    items.slice(0, 5).forEach((item, i) => {
                        const title = item.title || 'Untitled';
                        const score = item.score ? ` (relevance: ${(item.score * 100).toFixed(0)}%)` : '';
                        desc += `  ${i + 1}. ${title}${score}\n`;
                    });
                }
                return desc;
            },
            'No Knowledge Found in Brain': () => {
                return `No relevant information found in internal knowledge base. Will search the web for accurate information.`;
            },
            'Generating Response': () => {
                const hasKnowledge = data?.has_knowledge || false;
                const knowledgeItems = data?.knowledge_items || 0;
                return `Synthesizing information from ${hasKnowledge ? 'knowledge base and ' : ''}web search to generate a comprehensive answer. Using the AI model to create a natural, helpful response.`;
            },
            'Response Generated': () => {
                const length = data?.length || 0;
                return `Generated response (${length} characters). Combining information from multiple sources to provide an accurate answer.`;
            },
            'Refining Response': () => {
                return `Refining and polishing the response to ensure clarity, accuracy, and proper formatting.`;
            },
            'Response Refined': () => {
                return `Response has been refined and is ready to be sent.`;
            },
            'Formatting Response': () => {
                return `Formatting the response with proper markdown, code blocks, and structure for better readability.`;
            },
            'Response Formatted': () => {
                return `Response formatting complete. The answer is ready to be sent.`;
            }
        };
        
        const formatter = descriptions[stepName];
        if (formatter) {
            try {
                return formatter();
            } catch (e) {
                console.error('Error formatting step:', e);
            }
        }
        
        return `Processing: ${stepName}`;
    }
    
    addActionLogEnhanced(status, stepName, data) {
        const placeholder = this.debugContent.querySelector('.debug-placeholder');
        if (placeholder) {
            placeholder.remove();
        }
        
        const actionItem = document.createElement('div');
        actionItem.className = 'action-log-item';
        
        const header = document.createElement('div');
        header.className = 'action-header';
        
        const titleDiv = document.createElement('div');
        titleDiv.className = 'action-title';
        
        const icon = document.createElement('div');
        icon.className = 'action-icon';
        const iconMap = {
            'info': 'fa-info-circle',
            'success': 'fa-check-circle',
            'warning': 'fa-exclamation-triangle',
            'error': 'fa-times-circle'
        };
        icon.innerHTML = `<i class="fas ${iconMap[status] || 'fa-circle'}"></i>`;
        
        titleDiv.appendChild(icon);
        titleDiv.appendChild(document.createTextNode(stepName));
        
        const time = document.createElement('div');
        time.className = 'action-time';
        const now = new Date();
        time.textContent = now.toLocaleTimeString('en-US', { 
            hour: 'numeric', 
            minute: '2-digit', 
            second: '2-digit', 
            hour12: true 
        });
        
        header.appendChild(titleDiv);
        header.appendChild(time);
        actionItem.appendChild(header);
        
        const description = document.createElement('div');
        description.className = 'action-description';
        description.textContent = this.formatStepDescription(stepName, data);
        actionItem.appendChild(description);
        
        // Special handling for search results
        if (stepName === 'Web Search Complete' && (data.results || data.top_results)) {
            const results = data.results || data.top_results || [];
            
            // Group by source
            const bySource = {};
            results.forEach(result => {
                const source = result.source || result.Source || 'web';
                if (!bySource[source]) {
                    bySource[source] = [];
                }
                bySource[source].push(result);
            });
            
            // Display grouped by source
            Object.keys(bySource).forEach(source => {
                const sourceGroup = document.createElement('div');
                sourceGroup.className = 'search-results-group';
                
                const sourceHeader = document.createElement('div');
                sourceHeader.className = 'search-source-header';
                sourceHeader.innerHTML = `
                    <i class="fas fa-search"></i>
                    <span>${source.charAt(0).toUpperCase() + source.slice(1)} (${bySource[source].length} result${bySource[source].length !== 1 ? 's' : ''})</span>
                `;
                sourceGroup.appendChild(sourceHeader);
                
                bySource[source].forEach((result) => {
                    const resultItem = document.createElement('div');
                    resultItem.className = 'search-result-item';
                    
                    const title = document.createElement('div');
                    title.className = 'search-result-title';
                    const resultTitle = result.title || result.Title || 'Untitled';
                    const cleanTitle = resultTitle.replace(/^(Google|Bing|DuckDuckGo|Wikipedia|Brave)\s*—\s*/i, '');
                    title.textContent = cleanTitle;
                    
                    if (result.url || result.URL) {
                        const url = document.createElement('div');
                        url.className = 'search-result-url';
                        url.textContent = result.url || result.URL;
                        resultItem.appendChild(url);
                    }
                    
                    resultItem.appendChild(title);
                    sourceGroup.appendChild(resultItem);
                });
                
                actionItem.appendChild(sourceGroup);
            });
        } else if (stepName === 'Knowledge Retrieved from Brain' && data.items) {
            const itemsGroup = document.createElement('div');
            itemsGroup.className = 'search-results-group';
            
            data.items.slice(0, 5).forEach((item) => {
                const itemDiv = document.createElement('div');
                itemDiv.className = 'search-result-item';
                
                const title = document.createElement('div');
                title.className = 'search-result-title';
                const itemTitle = item.title || 'Untitled';
                const score = item.score ? ` (${(item.score * 100).toFixed(0)}% match)` : '';
                title.textContent = `${itemTitle}${score}`;
                
                itemDiv.appendChild(title);
                itemsGroup.appendChild(itemDiv);
            });
            
            actionItem.appendChild(itemsGroup);
        } else if (data && Object.keys(data).length > 0 && stepName !== 'Web Search Complete') {
            // Show raw data in collapsible section
            const collapsible = this.createCollapsibleSection('Technical Details', JSON.stringify(data, null, 2));
            actionItem.appendChild(collapsible);
        }
        
        this.debugContent.appendChild(actionItem);
        this.scrollDebugToBottom();
    }
    
    createCollapsibleSection(title, content) {
        const section = document.createElement('div');
        section.className = 'collapsible-section';
        
        const header = document.createElement('div');
        header.className = 'collapsible-header';
        header.innerHTML = `
            <span>${title}</span>
            <i class="fas fa-chevron-down collapse-icon"></i>
        `;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'collapsible-content';
        
        const inner = document.createElement('div');
        inner.className = 'collapsible-content-inner';
        inner.style.fontFamily = "'JetBrains Mono', monospace";
        inner.style.fontSize = '11px';
        inner.style.color = 'var(--text-muted)';
        inner.style.whiteSpace = 'pre-wrap';
        inner.style.wordBreak = 'break-word';
        inner.textContent = content;
        
        contentDiv.appendChild(inner);
        section.appendChild(header);
        section.appendChild(contentDiv);
        
        header.addEventListener('click', () => {
            header.classList.toggle('collapsed');
            contentDiv.classList.toggle('collapsed');
        });
        
        return section;
    }
    
    addActionLog(status, stepName, description) {
        this.addActionLogEnhanced(status, stepName, { description });
    }
    
    clearDebug() {
        this.debugContent.innerHTML = `
            <div class="debug-placeholder">
                <i class="fas fa-info-circle"></i>
                <p>Processing request...</p>
            </div>
        `;
    }
    
    clearChat() {
        if (confirm('Clear all messages?')) {
            this.messagesContainer.innerHTML = `
                <div class="welcome-message">
                    <div class="welcome-icon">
                        <i class="fas fa-microscope"></i>
                    </div>
                    <h2>Dev Atlas</h2>
                    <p>Debugging interface for Atlas AI</p>
                    <p class="subtitle">See every step of the thinking process</p>
                </div>
            `;
            this.welcomeMsg = this.messagesContainer.querySelector('.welcome-message');
            this.clearDebug();
            this.debugContent.innerHTML = `
                <div class="debug-placeholder">
                    <i class="fas fa-info-circle"></i>
                    <p>Send a message to see the debugging process</p>
                </div>
            `;
        }
    }
    
    toggleDebugPanel() {
        this.isDebugCollapsed = !this.isDebugCollapsed;
        this.debugPanel.classList.toggle('collapsed', this.isDebugCollapsed);
        
        const icon = this.toggleDebug.querySelector('i');
        icon.className = this.isDebugCollapsed ? 'fas fa-chevron-up' : 'fas fa-chevron-down';
    }
    
    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
    
    scrollDebugToBottom() {
        this.debugContent.scrollTop = this.debugContent.scrollHeight;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new DevAtlas();
});
