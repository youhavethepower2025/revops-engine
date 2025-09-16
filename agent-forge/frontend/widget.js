/**
 * AGENT.FORGE WIDGET
 * The Embeddable Intelligence - One Script to Rule Them All
 * 
 * Usage: <script src="https://agent.forge/widget.js?id=WIDGET_ID"></script>
 * 
 * Built from Medellín with love and game theory
 */

(function() {
    'use strict';
    
    // ===============================
    // THE CONFIGURATION OF POWER
    // ===============================
    
    // Extract widget ID from script src
    const currentScript = document.currentScript || (() => {
        const scripts = document.getElementsByTagName('script');
        return scripts[scripts.length - 1];
    })();
    
    const scriptSrc = currentScript.src;
    const urlParams = new URLSearchParams(scriptSrc.split('?')[1] || '');
    const WIDGET_ID = urlParams.get('id');
    
    if (!WIDGET_ID) {
        console.error('Agent.Forge: Widget ID is required');
        return;
    }
    
    // Widget configuration
    const CONFIG = {
        apiBase: 'https://agent.forge', // Update for production
        widgetId: WIDGET_ID,
        position: 'bottom-right', // Will be overridden by server config
        zIndex: 2147483647, // Maximum z-index
        debug: false
    };
    
    // Widget state
    let widgetConfig = null;
    let isOpen = false;
    let sessionId = null;
    let visitorId = null;
    let messageCount = 0;
    
    // DOM elements
    let widgetContainer = null;
    let chatWindow = null;
    let messagesContainer = null;
    let messageInput = null;
    let sendButton = null;
    let toggleButton = null;
    
    // ===============================
    // THE STYLES OF BEAUTY
    // ===============================
    
    function injectStyles() {
        const styleId = 'agent-forge-widget-styles';
        if (document.getElementById(styleId)) return;
        
        const styles = `
            /* Agent.Forge Widget - The Styles of Valinor */
            .af-widget-container {
                position: fixed;
                z-index: ${CONFIG.zIndex};
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
                color: #1f2937;
                font-size: 14px;
                line-height: 1.5;
                box-sizing: border-box;
            }
            
            .af-widget-container *, 
            .af-widget-container *::before, 
            .af-widget-container *::after {
                box-sizing: border-box;
            }
            
            /* Position variants */
            .af-widget-bottom-right {
                bottom: 20px;
                right: 20px;
            }
            
            .af-widget-bottom-left {
                bottom: 20px;
                left: 20px;
            }
            
            .af-widget-top-right {
                top: 20px;
                right: 20px;
            }
            
            .af-widget-top-left {
                top: 20px;
                left: 20px;
            }
            
            /* Toggle button - The Beacon of Gondor */
            .af-toggle-btn {
                width: 60px;
                height: 60px;
                border-radius: 50%;
                border: none;
                cursor: pointer;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 24px;
                color: white;
                position: relative;
                overflow: hidden;
            }
            
            .af-toggle-btn:hover {
                transform: scale(1.1);
                box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
            }
            
            .af-toggle-btn:active {
                transform: scale(0.95);
            }
            
            .af-toggle-icon {
                transition: transform 0.3s ease;
            }
            
            .af-toggle-btn.open .af-toggle-icon {
                transform: rotate(180deg);
            }
            
            /* Notification badge */
            .af-notification-badge {
                position: absolute;
                top: -5px;
                right: -5px;
                background: #ef4444;
                color: white;
                border-radius: 50%;
                width: 20px;
                height: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 10px;
                font-weight: bold;
                animation: af-pulse 2s infinite;
            }
            
            @keyframes af-pulse {
                0%, 100% { transform: scale(1); opacity: 1; }
                50% { transform: scale(1.1); opacity: 0.8; }
            }
            
            /* Chat window - The Halls of Wisdom */
            .af-chat-window {
                width: 380px;
                max-width: calc(100vw - 40px);
                height: 600px;
                max-height: calc(100vh - 40px);
                background: white;
                border-radius: 16px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
                display: flex;
                flex-direction: column;
                overflow: hidden;
                opacity: 0;
                transform: translateY(20px) scale(0.95);
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                margin-bottom: 80px;
                border: 1px solid rgba(0, 0, 0, 0.1);
            }
            
            .af-chat-window.open {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
            
            .af-chat-window.hidden {
                display: none;
            }
            
            /* Chat header - The Crown of Kings */
            .af-chat-header {
                padding: 20px;
                color: white;
                border-radius: 16px 16px 0 0;
                background: linear-gradient(135deg, var(--af-primary-color, #2563eb), var(--af-primary-dark, #1d4ed8));
                position: relative;
            }
            
            .af-chat-header::before {
                content: '';
                position: absolute;
                inset: 0;
                border-radius: 16px 16px 0 0;
                background: linear-gradient(135deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
                pointer-events: none;
            }
            
            .af-agent-info {
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .af-agent-avatar {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background: rgba(255, 255, 255, 0.2);
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                font-size: 18px;
            }
            
            .af-agent-details {
                flex: 1;
            }
            
            .af-agent-name {
                font-weight: 600;
                margin-bottom: 2px;
            }
            
            .af-agent-status {
                font-size: 12px;
                opacity: 0.9;
                display: flex;
                align-items: center;
                gap: 6px;
            }
            
            .af-status-indicator {
                width: 8px;
                height: 8px;
                background: #10b981;
                border-radius: 50%;
                animation: af-pulse 2s infinite;
            }
            
            .af-close-btn {
                background: none;
                border: none;
                color: white;
                font-size: 18px;
                cursor: pointer;
                padding: 8px;
                border-radius: 50%;
                transition: background-color 0.2s;
            }
            
            .af-close-btn:hover {
                background: rgba(255, 255, 255, 0.2);
            }
            
            /* Messages area - The Chronicle of Words */
            .af-messages-container {
                flex: 1;
                overflow-y: auto;
                padding: 20px;
                display: flex;
                flex-direction: column;
                gap: 16px;
                background: #f8fafc;
                scroll-behavior: smooth;
            }
            
            .af-messages-container::-webkit-scrollbar {
                width: 6px;
            }
            
            .af-messages-container::-webkit-scrollbar-track {
                background: transparent;
            }
            
            .af-messages-container::-webkit-scrollbar-thumb {
                background: #cbd5e1;
                border-radius: 3px;
            }
            
            /* Message styles */
            .af-message {
                max-width: 80%;
                padding: 12px 16px;
                border-radius: 18px;
                word-wrap: break-word;
                animation: af-messageSlideIn 0.3s ease-out;
            }
            
            @keyframes af-messageSlideIn {
                from {
                    opacity: 0;
                    transform: translateY(10px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            .af-message.user {
                align-self: flex-end;
                background: var(--af-primary-color, #2563eb);
                color: white;
                margin-left: auto;
            }
            
            .af-message.assistant {
                align-self: flex-start;
                background: white;
                color: #374151;
                border: 1px solid #e5e7eb;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            }
            
            .af-message.system {
                align-self: center;
                background: #f3f4f6;
                color: #6b7280;
                font-size: 12px;
                border-radius: 12px;
                text-align: center;
                max-width: 90%;
            }
            
            /* Typing indicator */
            .af-typing-indicator {
                align-self: flex-start;
                background: white;
                border: 1px solid #e5e7eb;
                padding: 12px 16px;
                border-radius: 18px;
                display: flex;
                align-items: center;
                gap: 4px;
            }
            
            .af-typing-dot {
                width: 8px;
                height: 8px;
                background: #9ca3af;
                border-radius: 50%;
                animation: af-typingBounce 1.4s infinite ease-in-out both;
            }
            
            .af-typing-dot:nth-child(1) { animation-delay: -0.32s; }
            .af-typing-dot:nth-child(2) { animation-delay: -0.16s; }
            
            @keyframes af-typingBounce {
                0%, 80%, 100% {
                    transform: scale(0);
                }
                40% {
                    transform: scale(1);
                }
            }
            
            /* Input area - The Quill of Power */
            .af-input-area {
                padding: 20px;
                background: white;
                border-top: 1px solid #e5e7eb;
                display: flex;
                gap: 12px;
                align-items: flex-end;
            }
            
            .af-message-input {
                flex: 1;
                border: 1px solid #d1d5db;
                border-radius: 20px;
                padding: 12px 16px;
                font-size: 14px;
                outline: none;
                transition: border-color 0.2s;
                resize: none;
                max-height: 100px;
                min-height: 20px;
            }
            
            .af-message-input:focus {
                border-color: var(--af-primary-color, #2563eb);
            }
            
            .af-message-input::placeholder {
                color: #9ca3af;
            }
            
            .af-send-btn {
                width: 44px;
                height: 44px;
                border: none;
                border-radius: 50%;
                background: var(--af-primary-color, #2563eb);
                color: white;
                cursor: pointer;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s;
                flex-shrink: 0;
            }
            
            .af-send-btn:hover:not(:disabled) {
                background: var(--af-primary-dark, #1d4ed8);
                transform: scale(1.05);
            }
            
            .af-send-btn:disabled {
                opacity: 0.5;
                cursor: not-allowed;
                transform: none;
            }
            
            /* Loading spinner */
            .af-spinner {
                width: 16px;
                height: 16px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                border-top-color: white;
                animation: af-spin 1s linear infinite;
            }
            
            @keyframes af-spin {
                to { transform: rotate(360deg); }
            }
            
            /* Mobile responsive */
            @media (max-width: 480px) {
                .af-chat-window {
                    width: calc(100vw - 20px);
                    height: calc(100vh - 20px);
                    margin: 0;
                    border-radius: 12px;
                }
                
                .af-widget-container {
                    position: fixed !important;
                    inset: 10px !important;
                }
                
                .af-widget-container.mobile-open .af-toggle-btn {
                    display: none;
                }
            }
            
            /* Accessibility */
            .af-widget-container button:focus {
                outline: 2px solid var(--af-primary-color, #2563eb);
                outline-offset: 2px;
            }
            
            .af-sr-only {
                position: absolute;
                width: 1px;
                height: 1px;
                padding: 0;
                margin: -1px;
                overflow: hidden;
                clip: rect(0, 0, 0, 0);
                white-space: nowrap;
                border: 0;
            }
        `;
        
        const styleSheet = document.createElement('style');
        styleSheet.id = styleId;
        styleSheet.textContent = styles;
        document.head.appendChild(styleSheet);
    }
    
    // ===============================
    // THE WIDGET CREATION
    // ===============================
    
    function createWidget() {
        // Create main container
        widgetContainer = document.createElement('div');
        widgetContainer.className = 'af-widget-container af-widget-bottom-right';
        
        // Create toggle button
        toggleButton = document.createElement('button');
        toggleButton.className = 'af-toggle-btn';
        toggleButton.setAttribute('aria-label', 'Open chat');
        toggleButton.innerHTML = `
            <div class="af-toggle-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10h6v-3h-6c-3.86 0-7-3.14-7-7s3.14-7 7-7 7 3.14 7 7v1c0 .55-.45 1-1 1s-1-.45-1-1v-1c0-2.76-2.24-5-5-5s-5 2.24-5 5 2.24 5 5 5c1.38 0 2.63-.56 3.54-1.46.65.89 1.77 1.46 2.96 1.46 1.66 0 3-1.34 3-3v-1c0-5.52-4.48-10-10-10zm0 13c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3z"/>
                </svg>
            </div>
        `;
        
        // Create chat window
        chatWindow = document.createElement('div');
        chatWindow.className = 'af-chat-window hidden';
        
        // Create chat header
        const chatHeader = document.createElement('div');
        chatHeader.className = 'af-chat-header';
        
        // Create messages container
        messagesContainer = document.createElement('div');
        messagesContainer.className = 'af-messages-container';
        
        // Create input area
        const inputArea = document.createElement('div');
        inputArea.className = 'af-input-area';
        
        messageInput = document.createElement('textarea');
        messageInput.className = 'af-message-input';
        messageInput.placeholder = 'Type your message...';
        messageInput.rows = 1;
        messageInput.setAttribute('aria-label', 'Message input');
        
        sendButton = document.createElement('button');
        sendButton.className = 'af-send-btn';
        sendButton.setAttribute('aria-label', 'Send message');
        sendButton.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
        `;
        
        // Assemble the widget
        inputArea.appendChild(messageInput);
        inputArea.appendChild(sendButton);
        
        chatWindow.appendChild(chatHeader);
        chatWindow.appendChild(messagesContainer);
        chatWindow.appendChild(inputArea);
        
        widgetContainer.appendChild(chatWindow);
        widgetContainer.appendChild(toggleButton);
        
        // Add event listeners
        toggleButton.addEventListener('click', toggleChat);
        sendButton.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', handleInputKeypress);
        messageInput.addEventListener('input', adjustTextareaHeight);
        
        // Close button handler
        chatHeader.addEventListener('click', (e) => {
            if (e.target.classList.contains('af-close-btn')) {
                closeChat();
            }
        });
        
        // Append to body
        document.body.appendChild(widgetContainer);
    }
    
    // ===============================
    // THE CHAT FUNCTIONALITY
    // ===============================
    
    function toggleChat() {
        if (isOpen) {
            closeChat();
        } else {
            openChat();
        }
    }
    
    function openChat() {
        isOpen = true;
        chatWindow.classList.remove('hidden');
        setTimeout(() => {
            chatWindow.classList.add('open');
        }, 10);
        
        toggleButton.classList.add('open');
        toggleButton.setAttribute('aria-label', 'Close chat');
        
        // Focus input
        messageInput.focus();
        
        // Track analytics
        trackEvent('widget_opened');
        
        // Load initial messages if first time
        if (messageCount === 0) {
            showWelcomeMessage();
        }
    }
    
    function closeChat() {
        isOpen = false;
        chatWindow.classList.remove('open');
        setTimeout(() => {
            chatWindow.classList.add('hidden');
        }, 300);
        
        toggleButton.classList.remove('open');
        toggleButton.setAttribute('aria-label', 'Open chat');
        
        // Track analytics
        trackEvent('widget_closed');
    }
    
    function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;
        
        // Add user message to UI
        addMessage(message, 'user');
        
        // Clear input
        messageInput.value = '';
        adjustTextareaHeight();
        
        // Show typing indicator
        showTypingIndicator();
        
        // Send to API
        sendToAPI(message);
        
        // Track analytics
        trackEvent('message_sent', { message_length: message.length });
    }
    
    async function sendToAPI(message) {
        try {
            // Ensure we have session IDs
            if (!sessionId) {
                sessionId = 'session_' + generateId();
            }
            if (!visitorId) {
                visitorId = 'visitor_' + generateId();
            }
            
            const response = await fetch(`${CONFIG.apiBase}/widget/${CONFIG.widgetId}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    session_id: sessionId,
                    visitor_id: visitorId
                })
            });
            
            hideTypingIndicator();
            
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            
            const data = await response.json();
            
            if (data.response) {
                addMessage(data.response, 'assistant');
            } else {
                addMessage('Sorry, I encountered an error. Please try again.', 'assistant');
            }
            
        } catch (error) {
            hideTypingIndicator();
            addMessage('Sorry, I cannot connect right now. Please try again later.', 'assistant');
            console.error('Agent.Forge: API Error:', error);
        }
    }
    
    function addMessage(content, role) {
        const messageElement = document.createElement('div');
        messageElement.className = `af-message ${role}`;
        messageElement.textContent = content;
        
        messagesContainer.appendChild(messageElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        messageCount++;
    }
    
    function showWelcomeMessage() {
        if (widgetConfig && widgetConfig.welcome_message) {
            addMessage(widgetConfig.welcome_message, 'assistant');
        }
    }
    
    function showTypingIndicator() {
        const typingElement = document.createElement('div');
        typingElement.className = 'af-typing-indicator';
        typingElement.innerHTML = `
            <div class="af-typing-dot"></div>
            <div class="af-typing-dot"></div>
            <div class="af-typing-dot"></div>
        `;
        typingElement.setAttribute('data-typing', 'true');
        
        messagesContainer.appendChild(typingElement);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    function hideTypingIndicator() {
        const typingElement = messagesContainer.querySelector('[data-typing="true"]');
        if (typingElement) {
            typingElement.remove();
        }
    }
    
    // ===============================
    // EVENT HANDLERS
    // ===============================
    
    function handleInputKeypress(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    }
    
    function adjustTextareaHeight() {
        messageInput.style.height = 'auto';
        messageInput.style.height = Math.min(messageInput.scrollHeight, 100) + 'px';
    }
    
    // ===============================
    // UTILITY FUNCTIONS
    // ===============================
    
    function generateId() {
        return Math.random().toString(36).substr(2, 9);
    }
    
    function trackEvent(eventType, data = {}) {
        // Track analytics event
        if (CONFIG.debug) {
            console.log('Agent.Forge Event:', eventType, data);
        }
        
        // Send to analytics endpoint (optional)
        try {
            fetch(`${CONFIG.apiBase}/analytics/track`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    widget_id: CONFIG.widgetId,
                    event_type: eventType,
                    event_data: data,
                    visitor_id: visitorId,
                    session_id: sessionId,
                    timestamp: new Date().toISOString()
                })
            }).catch(() => {}); // Silent fail for analytics
        } catch (error) {
            // Silent fail
        }
    }
    
    // ===============================
    // INITIALIZATION
    // ===============================
    
    async function init() {
        try {
            // Load widget configuration
            const response = await fetch(`${CONFIG.apiBase}/widget/${CONFIG.widgetId}/config`);
            if (response.ok) {
                widgetConfig = await response.json();
                
                // Apply configuration
                if (widgetConfig.brand_color) {
                    document.documentElement.style.setProperty('--af-primary-color', widgetConfig.brand_color);
                    document.documentElement.style.setProperty('--af-primary-dark', adjustColor(widgetConfig.brand_color, -20));
                }
                
                if (widgetConfig.widget_position) {
                    CONFIG.position = widgetConfig.widget_position;
                }
            }
            
        } catch (error) {
            console.warn('Agent.Forge: Could not load widget configuration, using defaults');
        }
        
        // Inject styles
        injectStyles();
        
        // Create widget
        createWidget();
        
        // Update position class
        widgetContainer.className = `af-widget-container af-widget-${CONFIG.position}`;
        
        // Update toggle button style
        if (widgetConfig && widgetConfig.brand_color) {
            toggleButton.style.background = `linear-gradient(135deg, ${widgetConfig.brand_color}, ${adjustColor(widgetConfig.brand_color, -20)})`;
        }
        
        // Update header with client name
        if (widgetConfig && widgetConfig.client_name) {
            const header = chatWindow.querySelector('.af-chat-header');
            header.innerHTML = `
                <div class="af-agent-info">
                    <div class="af-agent-avatar">${widgetConfig.client_name.charAt(0).toUpperCase()}</div>
                    <div class="af-agent-details">
                        <div class="af-agent-name">${widgetConfig.client_name} Assistant</div>
                        <div class="af-agent-status">
                            <div class="af-status-indicator"></div>
                            Online now
                        </div>
                    </div>
                </div>
                <button class="af-close-btn" aria-label="Close chat">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                    </svg>
                </button>
            `;
        }
        
        // Track initialization
        trackEvent('widget_loaded');
        
        if (CONFIG.debug) {
            console.log('Agent.Forge Widget initialized:', CONFIG.widgetId);
        }
        
    }
    
    // Color utility function
    function adjustColor(color, percent) {
        const num = parseInt(color.replace("#", ""), 16);
        const amt = Math.round(2.55 * percent);
        const R = (num >> 16) + amt;
        const G = (num >> 8 & 0x00FF) + amt;
        const B = (num & 0x0000FF) + amt;
        return "#" + (0x1000000 + (R < 255 ? R < 1 ? 0 : R : 255) * 0x10000 +
            (G < 255 ? G < 1 ? 0 : G : 255) * 0x100 +
            (B < 255 ? B < 1 ? 0 : B : 255))
            .toString(16)
            .slice(1);
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    // Expose global interface (for advanced users)
    window.AgentForgeWidget = {
        open: openChat,
        close: closeChat,
        toggle: toggleChat,
        send: (message) => {
            messageInput.value = message;
            sendMessage();
        }
    };
    
})();