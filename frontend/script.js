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
 * Escape HTML to prevent XSS
 * @param {string} text - Raw text
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
}

/**
 * Apply inline formatting (bold, italic, code, links)
 * @param {string} text - Text to format
 * @returns {string} Formatted HTML
 */
function applyInlineFormatting(text) {
    let result = escapeHtml(text);
    
    // Inline code (` ... `)
    result = result.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Bold (**text** or __text__)
    result = result.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    result = result.replace(/__([^_]+)__/g, '<strong>$1</strong>');
    
    // Italic (*text* or _text_) - be careful not to match inside words
    result = result.replace(/(?<!\w)\*([^*]+)\*(?!\w)/g, '<em>$1</em>');
    result = result.replace(/(?<!\w)_([^_]+)_(?!\w)/g, '<em>$1</em>');
    
    // Links [text](url)
    result = result.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
    
    return result;
}

/**
 * Parse markdown text into HTML with proper structure
 * Handles: code blocks, headers, nested lists, paragraphs, inline formatting
 * @param {string} text - Raw markdown text
 * @returns {string} HTML string
 */
function parseMarkdown(text) {
    const lines = text.split('\n');
    const result = [];
    let inCodeBlock = false;
    let codeBlockLang = '';
    let codeBlockContent = [];
    let listStack = []; // Track nested list levels
    
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        
        // Handle fenced code blocks (``` ... ```)
        if (line.trim().startsWith('```')) {
            if (!inCodeBlock) {
                // Start code block
                inCodeBlock = true;
                codeBlockLang = line.trim().slice(3).trim();
                codeBlockContent = [];
            } else {
                // End code block
                inCodeBlock = false;
                closeAllLists(result, listStack);
                result.push(`<pre><code class="language-${codeBlockLang}">${escapeHtml(codeBlockContent.join('\n'))}</code></pre>`);
                codeBlockContent = [];
                codeBlockLang = '';
            }
            continue;
        }
        
        if (inCodeBlock) {
            codeBlockContent.push(line);
            continue;
        }
        
        // Empty line - close lists and add paragraph break
        if (line.trim() === '') {
            closeAllLists(result, listStack);
            continue;
        }
        
        // Headers (# ## ### ####)
        const headerMatch = line.match(/^(#{1,4})\s+(.+)$/);
        if (headerMatch) {
            closeAllLists(result, listStack);
            const level = headerMatch[1].length + 1; // h2, h3, h4, h5
            result.push(`<h${level}>${applyInlineFormatting(headerMatch[2])}</h${level}>`);
            continue;
        }
        
        // List items - detect indent level
        const listMatch = line.match(/^(\s*)[-*•]\s+(.+)$/);
        if (listMatch) {
            const indent = listMatch[1].length;
            const content = listMatch[2];
            const level = Math.floor(indent / 2); // 2 spaces = 1 level, 4 spaces = 2 levels
            
            // Adjust list nesting
            while (listStack.length > level + 1) {
                result.push('</li></ul>');
                listStack.pop();
            }
            
            if (listStack.length === level + 1) {
                // Same level - close previous item
                result.push('</li>');
            } else if (listStack.length < level + 1) {
                // Deeper level - open new nested list
                while (listStack.length < level + 1) {
                    result.push('<ul>');
                    listStack.push('ul');
                }
            }
            
            result.push(`<li>${applyInlineFormatting(content)}`);
            continue;
        }
        
        // Numbered list items
        const numListMatch = line.match(/^(\s*)(\d+)\.\s+(.+)$/);
        if (numListMatch) {
            const indent = numListMatch[1].length;
            const content = numListMatch[3];
            const level = Math.floor(indent / 2);
            
            while (listStack.length > level + 1) {
                const tag = listStack.pop();
                result.push(`</li></${tag}>`);
            }
            
            if (listStack.length === level + 1) {
                result.push('</li>');
            } else if (listStack.length < level + 1) {
                while (listStack.length < level + 1) {
                    result.push('<ol>');
                    listStack.push('ol');
                }
            }
            
            result.push(`<li>${applyInlineFormatting(content)}`);
            continue;
        }
        
        // Indented content (4+ spaces) - treat as part of previous item or code
        if (line.match(/^\s{4,}/) && listStack.length > 0) {
            result.push(`<br>${applyInlineFormatting(line.trim())}`);
            continue;
        }
        
        // Regular paragraph text
        closeAllLists(result, listStack);
        result.push(`<p>${applyInlineFormatting(line)}</p>`);
    }
    
    // Close any remaining open elements
    if (inCodeBlock) {
        result.push(`<pre><code class="language-${codeBlockLang}">${escapeHtml(codeBlockContent.join('\n'))}</code></pre>`);
    }
    closeAllLists(result, listStack);
    
    // Clean up consecutive paragraph tags
    let html = result.join('\n');
    html = html.replace(/<\/p>\n<p>/g, '</p><p>');
    html = html.replace(/<p><\/p>/g, '');
    
    return html;
}

/**
 * Close all open list elements
 * @param {string[]} result - Result array to append closing tags to
 * @param {string[]} listStack - Stack of open list types
 */
function closeAllLists(result, listStack) {
    while (listStack.length > 0) {
        const tag = listStack.pop();
        result.push(`</li></${tag}>`);
    }
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

