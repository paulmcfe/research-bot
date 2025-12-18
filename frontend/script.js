/**
 * ResearchBot Frontend - Chat Interface
 * Handles user input, API communication, and message rendering
 */

// Configuration
const API_BASE_URL = 'http://localhost:8000';
const API_CHAT_ENDPOINT = `${API_BASE_URL}/api/chat`;

// DOM Elements
const chatContainer = document.getElementById('chatContainer');
const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');

// State
let isLoading = false;

/**
 * Initialize the chat application
 */
function init() {
    // Set up event listeners
    chatForm.addEventListener('submit', handleSubmit);
    messageInput.addEventListener('input', handleInputChange);
    messageInput.addEventListener('keydown', handleKeyDown);
    
    // Focus input on load
    messageInput.focus();
}

/**
 * Handle form submission
 * @param {Event} event - Form submit event
 */
async function handleSubmit(event) {
    event.preventDefault();
    
    const message = messageInput.value.trim();
    if (!message || isLoading) return;
    
    // Clear input and reset height
    messageInput.value = '';
    messageInput.style.height = 'auto';
    
    // Remove welcome message if present
    const welcomeMessage = chatContainer.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.remove();
    }
    
    // Add user message to chat
    addMessage(message, 'user');
    
    // Send to API and get response
    await sendMessage(message);
}

/**
 * Handle input changes for auto-resize
 * @param {Event} event - Input event
 */
function handleInputChange(event) {
    const textarea = event.target;
    // Reset height to auto to get the correct scrollHeight
    textarea.style.height = 'auto';
    // Set height to scrollHeight (capped by CSS max-height)
    textarea.style.height = textarea.scrollHeight + 'px';
}

/**
 * Handle keyboard shortcuts
 * @param {KeyboardEvent} event - Keyboard event
 */
function handleKeyDown(event) {
    // Submit on Enter (without Shift)
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        // Use requestSubmit() to properly trigger form submission with validation
        chatForm.requestSubmit();
    }
}

/**
 * Simple markdown parser for AI responses
 * Handles: code blocks, inline code, bold, italic, headers, lists, links
 * @param {string} text - Raw markdown text
 * @returns {string} HTML string
 */
function parseMarkdown(text) {
    // Escape HTML to prevent XSS
    let html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    
    // Code blocks (``` ... ```)
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
        return `<pre><code class="language-${lang}">${code.trim()}</code></pre>`;
    });
    
    // Inline code (` ... `)
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Bold (**text** or __text__)
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/__([^_]+)__/g, '<strong>$1</strong>');
    
    // Italic (*text* or _text_)
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    html = html.replace(/_([^_]+)_/g, '<em>$1</em>');
    
    // Headers (# ## ###)
    html = html.replace(/^### (.+)$/gm, '<h4>$1</h4>');
    html = html.replace(/^## (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^# (.+)$/gm, '<h2>$1</h2>');
    
    // Unordered lists (- item)
    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
    
    // Numbered lists (1. item)
    html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
    
    // Links [text](url)
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    
    // Paragraphs (double newlines)
    html = html.replace(/\n\n+/g, '</p><p>');
    
    // Single line breaks
    html = html.replace(/\n/g, '<br>');
    
    // Wrap in paragraph tags
    html = '<p>' + html + '</p>';
    
    // Clean up empty paragraphs
    html = html.replace(/<p><\/p>/g, '');
    html = html.replace(/<p>(<h[234]>)/g, '$1');
    html = html.replace(/(<\/h[234]>)<\/p>/g, '$1');
    html = html.replace(/<p>(<pre>)/g, '$1');
    html = html.replace(/(<\/pre>)<\/p>/g, '$1');
    html = html.replace(/<p>(<ul>)/g, '$1');
    html = html.replace(/(<\/ul>)<\/p>/g, '$1');
    
    return html;
}

/**
 * Add a message to the chat container
 * @param {string} content - Message content
 * @param {string} type - Message type ('user' or 'ai')
 */
function addMessage(content, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.setAttribute('role', 'article');
    
    const label = document.createElement('span');
    label.className = 'message-label';
    label.textContent = type === 'user' ? 'You' : 'ResearchBot';
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // Use markdown parsing for AI messages, plain text for user messages
    if (type === 'ai') {
        contentDiv.innerHTML = parseMarkdown(content);
    } else {
        contentDiv.textContent = content;
    }
    
    messageDiv.appendChild(label);
    messageDiv.appendChild(contentDiv);
    chatContainer.appendChild(messageDiv);
    
    // Scroll to bottom
    scrollToBottom();
}

/**
 * Show loading indicator
 * @returns {HTMLElement} The loading element (for removal later)
 */
function showLoading() {
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'message ai';
    loadingDiv.setAttribute('role', 'status');
    loadingDiv.setAttribute('aria-label', 'ResearchBot is thinking');
    
    const label = document.createElement('span');
    label.className = 'message-label';
    label.textContent = 'ResearchBot';
    
    const indicator = document.createElement('div');
    indicator.className = 'loading-indicator';
    indicator.innerHTML = `
        <div class="loading-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
        <span>Thinking...</span>
    `;
    
    loadingDiv.appendChild(label);
    loadingDiv.appendChild(indicator);
    chatContainer.appendChild(loadingDiv);
    
    scrollToBottom();
    return loadingDiv;
}

/**
 * Show error message
 * @param {string} message - Error message to display
 */
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.setAttribute('role', 'alert');
    errorDiv.textContent = message;
    chatContainer.appendChild(errorDiv);
    scrollToBottom();
}

/**
 * Scroll chat container to bottom
 */
function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

/**
 * Set loading state
 * @param {boolean} loading - Whether app is in loading state
 */
function setLoading(loading) {
    isLoading = loading;
    sendButton.disabled = loading;
    messageInput.disabled = loading;
    
    if (!loading) {
        messageInput.focus();
    }
}

/**
 * Send message to API and handle response
 * @param {string} message - User message to send
 */
async function sendMessage(message) {
    setLoading(true);
    const loadingElement = showLoading();
    
    try {
        const response = await fetch(API_CHAT_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message }),
        });
        
        // Remove loading indicator
        loadingElement.remove();
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            const errorMessage = errorData.detail || `Server error: ${response.status}`;
            throw new Error(errorMessage);
        }
        
        const data = await response.json();
        
        if (data.reply) {
            addMessage(data.reply, 'ai');
        } else {
            throw new Error('Invalid response from server');
        }
        
    } catch (error) {
        // Remove loading indicator if still present
        if (loadingElement.parentNode) {
            loadingElement.remove();
        }
        
        console.error('Chat error:', error);
        
        // Show user-friendly error message
        let errorMessage = 'Something went wrong. Please try again.';
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            errorMessage = 'Unable to connect to the server. Make sure the backend is running at ' + API_BASE_URL;
        } else if (error.message) {
            errorMessage = error.message;
        }
        
        showError(errorMessage);
    } finally {
        setLoading(false);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', init);

