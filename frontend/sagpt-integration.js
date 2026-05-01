/**
 * SAGPT Frontend Integration Kit
 * 
 * 1. Add this script to your Readdy website (Custom HTML/JS block)
 * 2. Configure API_BASE_URL to point to your deployed backend
 * 3. The script will intercept form submissions and enable AI chat
 */

(function() {
  'use strict';

  // ==========================================
  // CONFIGURATION - Change these values
  // ==========================================
  const CONFIG = {
    API_BASE_URL: 'https://api.sagpt.com/api',  // Change to your backend URL
    // Or use relative path if backend is on same domain: '/api'
    
    // AI Chat Settings
    CHAT_ENABLED: true,
    CHAT_POSITION: 'bottom-right', // bottom-right, bottom-left
    
    // Matching Preview
    SHOW_MATCH_PREVIEW: true,
    
    // Feature flags
    ENABLE_STREAMING_CHAT: true,
    ENABLE_DEMAND_TRACKING: true
  };

  // ==========================================
  // STATE
  // ==========================================
  let chatSessionId = localStorage.getItem('sagpt_chat_session') || generateId();
  let chatMessages = [];
  let isChatOpen = false;

  function generateId() {
    const id = 'sess_' + Math.random().toString(36).substr(2, 9);
    localStorage.setItem('sagpt_chat_session', id);
    return id;
  }

  // ==========================================
  // DEMAND FORM INTEGRATION
  // ==========================================
  function initDemandForm() {
    // Find the Submit Demand form on the page
    const submitBtn = document.querySelector('button[type="submit"], button:contains("Submit Demand")');
    const form = document.querySelector('form') || document.querySelector('[data-form="demand"]');
    
    if (!form && !submitBtn) {
      console.log('[SAGPT] No demand form found on this page');
      return;
    }

    // Intercept form submission
    const btn = submitBtn || form.querySelector('button[type="submit"]');
    if (btn) {
      btn.addEventListener('click', handleDemandSubmit);
    }
    
    if (form) {
      form.addEventListener('submit', handleDemandSubmit);
    }

    // Add real-time match preview if enabled
    if (CONFIG.SHOW_MATCH_PREVIEW) {
      addMatchPreviewPanel();
    }
  }

  async function handleDemandSubmit(e) {
    e.preventDefault();
    e.stopPropagation();

    // Collect form data
    const formData = collectFormData();
    if (!formData) {
      alert('Please fill in all required fields');
      return;
    }

    // Show loading state
    const btn = e.target;
    const originalText = btn.textContent;
    btn.textContent = 'AI Matching...';
    btn.disabled = true;

    try {
      // Call our backend API
      const response = await fetch(`${CONFIG.API_BASE_URL}/demands/submit`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      const result = await response.json();

      if (result.success) {
        // Show success with AI match preview
        showSubmissionSuccess(result);
      } else {
        alert('Submission failed: ' + (result.message || 'Unknown error'));
      }
    } catch (err) {
      console.error('[SAGPT] Submit error:', err);
      // Fallback: try original Readdy form submission
      // alert('Network error. Please try again.');
      fallbackSubmit(formData);
    } finally {
      btn.textContent = originalText;
      btn.disabled = false;
    }
  }

  function collectFormData() {
    // Try to read from Readdy form fields
    // You may need to adjust selectors based on your exact form structure
    const getValue = (selectors) => {
      for (const sel of selectors) {
        const el = document.querySelector(sel);
        if (el) return el.value || el.textContent;
      }
      return null;
    };

    const data = {
      target_country: getValue(['select[name="country"]', '[name="target_country"]', '#country']),
      industry: getValue(['select[name="industry"]', '[name="industry"]', '#industry']),
      scenario: getValue(['select[name="scenario"]', '[name="scenario"]', '#scenario']),
      budget_range: getValue(['select[name="budget"]', '[name="budget_range"]', '#budget']),
      urgency: getValue(['input[name="urgency"]:checked', '[name="urgency"]', '#urgency']) || 'normal',
      description: getValue(['textarea[name="description"]', '[name="description"]', '#description']),
      email: getValue(['input[type="email"]', '[name="email"]', '#email']),
      wechat_phone: getValue(['[name="wechat"]', '[name="wechat_phone"]', '#wechat']),
      company_name: getValue(['[name="company"]', '[name="company_name"]', '#company']),
      phone: getValue(['[name="phone"]', '#phone']),
      attachments: []
    };

    // Validate required fields
    if (!data.target_country || !data.industry || !data.scenario || !data.budget_range || !data.description || !data.email) {
      return null;
    }

    return data;
  }

  function fallbackSubmit(formData) {
    // Fallback to original form behavior if API fails
    console.log('[SAGPT] Falling back to original form submission');
    const form = document.querySelector('form');
    if (form) form.submit();
  }

  function showSubmissionSuccess(result) {
    // Create a beautiful success modal with AI match preview
    const modal = document.createElement('div');
    modal.id = 'sagpt-success-modal';
    modal.innerHTML = `
      <div style="
        position: fixed; top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0,0,0,0.6); z-index: 9999;
        display: flex; align-items: center; justify-content: center;
      ">
        <div style="
          background: white; border-radius: 16px; padding: 40px;
          max-width: 600px; width: 90%; max-height: 80vh;
          overflow-y: auto; position: relative;
        ">
          <button onclick="document.getElementById('sagpt-success-modal').remove()" 
            style="position: absolute; top: 16px; right: 16px; background: none; border: none; font-size: 24px; cursor: pointer;">&times;</button>
          
          <div style="text-align: center; margin-bottom: 24px;">
            <div style="font-size: 48px; margin-bottom: 8px;">✅</div>
            <h2 style="color: #0f766e; margin: 0;">Demand Submitted Successfully!</h2>
            <p style="color: #666; margin-top: 8px;">${result.message}</p>
            <p style="color: #0f766e; font-weight: 600;">Estimated match time: ${result.estimated_match_time}</p>
          </div>

          ${result.preview_matches && result.preview_matches.length > 0 ? `
            <div style="margin-top: 24px;">
              <h3 style="color: #333; margin-bottom: 16px;">🤖 AI Found ${result.preview_matches.length} Matching Experts</h3>
              <div style="display: flex; flex-direction: column; gap: 12px;">
                ${result.preview_matches.map(m => `
                  <div style="
                    border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px;
                    display: flex; gap: 16px; align-items: center;
                  ">
                    <img src="${m.photo_url || 'https://via.placeholder.com/60'}" 
                      style="width: 60px; height: 60px; border-radius: 50%; object-fit: cover;" alt="${m.name}">
                    <div style="flex: 1;">
                      <div style="font-weight: 600; color: #111;">${m.name}</div>
                      <div style="font-size: 13px; color: #666;">${m.company || ''} · ${m.country}</div>
                      <div style="font-size: 13px; color: #0f766e; margin-top: 4px;">
                        ⭐ ${m.rating} · ${m.experience_years} yrs · ${m.projects_count} projects
                      </div>
                      <div style="font-size: 12px; color: #0f766e; margin-top: 4px; font-style: italic;">
                        ${m.match_reason}
                      </div>
                    </div>
                    <div style="text-align: center;">
                      <div style="font-size: 24px; font-weight: 700; color: #0f766e;">${Math.round(m.match_score * 100)}%</div>
                      <div style="font-size: 11px; color: #999;">Match</div>
                    </div>
                  </div>
                `).join('')}
              </div>
            </div>
            
            <div style="margin-top: 24px; text-align: center;">
              <p style="color: #666; font-size: 14px;">
                We'll send detailed proposals to your email: <strong>${result.demand_id ? '' : ''}</strong>
              </p>
              <a href="/experts" style="
                display: inline-block; margin-top: 12px;
                background: #0d9488; color: white; padding: 12px 32px;
                border-radius: 8px; text-decoration: none; font-weight: 500;
              ">View All Experts</a>
            </div>
          ` : ''}
        </div>
      </div>
    `;
    document.body.appendChild(modal);
  }

  function addMatchPreviewPanel() {
    // Add a floating panel that shows "X experts may match" as user types
    // This is a simplified version - you can enhance based on your needs
    console.log('[SAGPT] Match preview panel initialized');
  }

  // ==========================================
  // AI CHAT WIDGET
  // ==========================================
  function initChatWidget() {
    if (!CONFIG.CHAT_ENABLED) return;

    // Create chat button
    const chatBtn = document.createElement('div');
    chatBtn.id = 'sagpt-chat-btn';
    chatBtn.innerHTML = `
      <div style="
        position: fixed; bottom: 24px; ${CONFIG.CHAT_POSITION === 'bottom-left' ? 'left: 24px;' : 'right: 24px;'}
        width: 56px; height: 56px; border-radius: 50%;
        background: linear-gradient(135deg, #0d9488, #14b8a6);
        color: white; display: flex; align-items: center; justify-content: center;
        cursor: pointer; box-shadow: 0 4px 20px rgba(13, 148, 136, 0.3);
        z-index: 9998; font-size: 24px; transition: transform 0.2s;
      " onmouseover="this.style.transform='scale(1.1)'" 
         onmouseout="this.style.transform='scale(1)'">
        💬
      </div>
    `;
    document.body.appendChild(chatBtn);

    // Create chat window (hidden initially)
    const chatWindow = document.createElement('div');
    chatWindow.id = 'sagpt-chat-window';
    chatWindow.style.cssText = `
      position: fixed; bottom: 92px; ${CONFIG.CHAT_POSITION === 'bottom-left' ? 'left: 24px;' : 'right: 24px;'}
      width: 380px; height: 500px; background: white;
      border-radius: 16px; box-shadow: 0 8px 40px rgba(0,0,0,0.15);
      z-index: 9997; display: none; flex-direction: column;
      overflow: hidden; border: 1px solid #e5e7eb;
    `;
    chatWindow.innerHTML = `
      <div style="background: linear-gradient(135deg, #0d9488, #14b8a6); padding: 16px 20px; color: white;">
        <div style="font-weight: 600; font-size: 16px;">🤖 SAGPT AI Assistant</div>
        <div style="font-size: 12px; opacity: 0.9;">Ask about global expansion</div>
      </div>
      <div id="sagpt-chat-messages" style="flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px;">
        <div style="align-self: flex-start; background: #f3f4f6; padding: 10px 14px; border-radius: 12px 12px 12px 4px; max-width: 85%; font-size: 14px; color: #374151;">
          Hello! I'm your SAGPT AI assistant. I can help you with:<br><br>
          • Finding the right local experts<br>
          • Understanding country-specific regulations<br>
          • Budget planning for overseas expansion<br>
          • Service recommendations<br><br>
          How can I help you today?
        </div>
      </div>
      <div style="padding: 12px 16px; border-top: 1px solid #e5e7eb; display: flex; gap: 8px;">
        <input id="sagpt-chat-input" type="text" placeholder="Ask about Saudi setup, UAE tax, etc..." 
          style="flex: 1; padding: 10px 14px; border: 1px solid #d1d5db; border-radius: 24px; outline: none; font-size: 14px;">
        <button id="sagpt-chat-send" style="
          background: #0d9488; color: white; border: none; border-radius: 50%;
          width: 40px; height: 40px; cursor: pointer; display: flex; align-items: center; justify-content: center;
          font-size: 16px;
        ">➤</button>
      </div>
    `;
    document.body.appendChild(chatWindow);

    // Toggle chat
    chatBtn.addEventListener('click', () => {
      isChatOpen = !isChatOpen;
      chatWindow.style.display = isChatOpen ? 'flex' : 'none';
    });

    // Send message
    const input = chatWindow.querySelector('#sagpt-chat-input');
    const sendBtn = chatWindow.querySelector('#sagpt-chat-send');
    
    const sendMessage = () => {
      const text = input.value.trim();
      if (!text) return;
      
      addUserMessage(text);
      input.value = '';
      
      if (CONFIG.ENABLE_STREAMING_CHAT) {
        streamChatResponse(text);
      } else {
        sendChatMessage(text);
      }
    };
    
    sendBtn.addEventListener('click', sendMessage);
    input.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') sendMessage();
    });
  }

  function addUserMessage(text) {
    const container = document.getElementById('sagpt-chat-messages');
    const msg = document.createElement('div');
    msg.style.cssText = 'align-self: flex-end; background: #0d9488; color: white; padding: 10px 14px; border-radius: 12px 12px 4px 12px; max-width: 85%; font-size: 14px;';
    msg.textContent = text;
    container.appendChild(msg);
    container.scrollTop = container.scrollHeight;
    
    chatMessages.push({role: 'user', content: text});
  }

  function addAssistantMessage(text, isStreaming = false) {
    const container = document.getElementById('sagpt-chat-messages');
    
    if (isStreaming) {
      // For streaming, find or create the assistant message bubble
      let msg = container.querySelector('.sagpt-assistant-streaming');
      if (!msg) {
        msg = document.createElement('div');
        msg.className = 'sagpt-assistant-streaming';
        msg.style.cssText = 'align-self: flex-start; background: #f3f4f6; padding: 10px 14px; border-radius: 12px 12px 12px 4px; max-width: 85%; font-size: 14px; color: #374151; white-space: pre-wrap;';
        container.appendChild(msg);
      }
      msg.textContent = text;
      container.scrollTop = container.scrollHeight;
    } else {
      const msg = document.createElement('div');
      msg.style.cssText = 'align-self: flex-start; background: #f3f4f6; padding: 10px 14px; border-radius: 12px 12px 12px 4px; max-width: 85%; font-size: 14px; color: #374151; white-space: pre-wrap;';
      msg.textContent = text;
      container.appendChild(msg);
      container.scrollTop = container.scrollHeight;
    }
  }

  async function streamChatResponse(text) {
    const container = document.getElementById('sagpt-chat-messages');
    
    // Remove any existing streaming element
    const existing = container.querySelector('.sagpt-assistant-streaming');
    if (existing) existing.remove();
    
    let fullResponse = '';
    
    try {
      const response = await fetch(`${CONFIG.API_BASE_URL}/chat/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text,
          fingerprint: chatSessionId,
          history: chatMessages.slice(-6) // last 3 exchanges
        })
      });
      
      const result = await response.json();
      
      if (result.chunk) {
        addAssistantMessage(result.chunk);
        chatMessages.push({role: 'assistant', content: result.chunk});
      }
    } catch (err) {
      console.error('[SAGPT] Chat error:', err);
      addAssistantMessage('Sorry, our AI assistant is temporarily unavailable. Please try again later or submit a demand form for expert matching.');
    }
  }

  // ==========================================
  // DYNAMIC EXPERTS LOADING
  // ==========================================
  async function loadExpertsDynamically() {
    // Check if we're on the experts page
    if (!window.location.pathname.includes('experts')) return;
    
    try {
      const response = await fetch(`${CONFIG.API_BASE_URL}/experts?page=1&page_size=50`);
      const data = await response.json();
      
      if (data.experts && data.experts.length > 0) {
        console.log(`[SAGPT] Loaded ${data.experts.length} experts from backend`);
        // You can enhance this to dynamically render experts if Readdy allows DOM manipulation
      }
    } catch (err) {
      console.log('[SAGPT] Could not load experts dynamically:', err);
    }
  }

  // ==========================================
  // INITIALIZATION
  // ==========================================
  function init() {
    console.log('[SAGPT] Integration kit loaded. API:', CONFIG.API_BASE_URL);
    
    initDemandForm();
    initChatWidget();
    loadExpertsDynamically();
    
    // Add global styles
    const style = document.createElement('style');
    style.textContent = `
      #sagpt-chat-messages::-webkit-scrollbar { width: 6px; }
      #sagpt-chat-messages::-webkit-scrollbar-track { background: transparent; }
      #sagpt-chat-messages::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 3px; }
      #sagpt-success-modal { animation: sagptFadeIn 0.3s ease; }
      @keyframes sagptFadeIn { from { opacity: 0; } to { opacity: 1; } }
    `;
    document.head.appendChild(style);
  }

  // Wait for DOM to be ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
