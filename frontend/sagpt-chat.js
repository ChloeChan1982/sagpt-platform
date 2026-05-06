/**
 * SAGPT AI Chat Widget
 * 嵌入 Readdy 网站的 AI 聊天组件
 */

(function() {
  'use strict';

  const API_URL = 'https://sagpt-platform.onrender.com/api';
  
  // 创建聊天按钮
  const chatBtn = document.createElement('div');
  chatBtn.id = 'sagpt-chat-btn';
  chatBtn.innerHTML = `
    <div style="
      position: fixed;
      bottom: 24px;
      right: 24px;
      width: 60px;
      height: 60px;
      border-radius: 50%;
      background: linear-gradient(135deg, #0d9488, #14b8a6);
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      box-shadow: 0 4px 20px rgba(13, 148, 136, 0.3);
      z-index: 9998;
      font-size: 24px;
      transition: transform 0.2s;
      border: 2px solid white;
    " onmouseover="this.style.transform='scale(1.1)'" 
       onmouseout="this.style.transform='scale(1)'">
      🤖
    </div>
  `;
  
  // 创建聊天窗口
  const chatWindow = document.createElement('div');
  chatWindow.id = 'sagpt-chat-window';
  chatWindow.style.cssText = `
    position: fixed;
    bottom: 96px;
    right: 24px;
    width: 400px;
    height: 550px;
    background: white;
    border-radius: 16px;
    box-shadow: 0 12px 48px rgba(0,0,0,0.15);
    z-index: 9997;
    display: none;
    flex-direction: column;
    overflow: hidden;
    border: 1px solid #e5e7eb;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  `;
  
  chatWindow.innerHTML = `
    <div style="background: linear-gradient(135deg, #0d9488, #14b8a6); padding: 16px 20px; color: white; display: flex; justify-content: space-between; align-items: center;">
      <div>
        <div style="font-weight: 600; font-size: 16px;">🤖 SAGPT AI 助手</div>
        <div style="font-size: 12px; opacity: 0.9;">全球出海智能顾问</div>
      </div>
      <div id="sagpt-close-btn" style="cursor: pointer; font-size: 20px; padding: 4px;">✕</div>
    </div>
    
    <div id="sagpt-chat-messages" style="flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 12px; background: #f9fafb;">
      <div style="align-self: flex-start; background: white; padding: 12px 16px; border-radius: 12px 12px 12px 4px; max-width: 85%; font-size: 14px; color: #374151; box-shadow: 0 1px 3px rgba(0,0,0,0.1); line-height: 1.5;">
        <strong>您好！我是 SAGPT AI 助手 👋</strong><br><br>
        我可以帮您：<br>
        • 了解各国出海政策法规<br>
        • 推荐合适的本地服务商<br>
        • 解答税务/法律/合规问题<br>
        • 预估出海预算和 timeline<br><br>
        请问有什么可以帮您？
      </div>
    </div>
    
    <div style="padding: 12px 16px; border-top: 1px solid #e5e7eb; background: white;">
      <div style="display: flex; gap: 8px; margin-bottom: 8px;">
        <button onclick="window.sagptQuickAsk('沙特开公司需要什么？')" style="padding: 6px 12px; border: 1px solid #0d9488; border-radius: 16px; background: white; color: #0d9488; font-size: 12px; cursor: pointer; white-space: nowrap;">🇦🇪 沙特开公司</button>
        <button onclick="window.sagptQuickAsk('阿联酋税务怎么交？')" style="padding: 6px 12px; border: 1px solid #0d9488; border-radius: 16px; background: white; color: #0d9488; font-size: 12px; cursor: pointer; white-space: nowrap;">💰 阿联酋税务</button>
        <button onclick="window.sagptQuickAsk('推荐电商服务商')" style="padding: 6px 12px; border: 1px solid #0d9488; border-radius: 16px; background: white; color: #0d9488; font-size: 12px; cursor: pointer; white-space: nowrap;">🛒 电商服务商</button>
      </div>
      <div style="display: flex; gap: 8px; align-items: center;">
        <input id="sagpt-chat-input" type="text" placeholder="输入您的问题..." 
          style="flex: 1; padding: 10px 14px; border: 1px solid #d1d5db; border-radius: 24px; outline: none; font-size: 14px;">
        <button id="sagpt-chat-send" style="background: #0d9488; color: white; border: none; border-radius: 50%; width: 40px; height: 40px; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 16px;">➤</button>
      </div>
    </div>
  `;
  
  document.body.appendChild(chatBtn);
  document.body.appendChild(chatWindow);
  
  // 样式
  const style = document.createElement('style');
  style.textContent = `
    #sagpt-chat-messages::-webkit-scrollbar { width: 6px; }
    #sagpt-chat-messages::-webkit-scrollbar-track { background: transparent; }
    #sagpt-chat-messages::-webkit-scrollbar-thumb { background: #d1d5db; border-radius: 3px; }
    .sagpt-user-msg { align-self: flex-end; background: #0d9488; color: white; padding: 10px 14px; border-radius: 12px 12px 4px 12px; max-width: 85%; font-size: 14px; line-height: 1.5; }
    .sagpt-ai-msg { align-self: flex-start; background: white; padding: 10px 14px; border-radius: 12px 12px 12px 4px; max-width: 85%; font-size: 14px; color: #374151; line-height: 1.5; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .sagpt-loading { align-self: center; color: #9ca3af; font-size: 13px; padding: 8px; }
  `;
  document.head.appendChild(style);
  
  let isOpen = false;
  const messagesContainer = document.getElementById('sagpt-chat-messages');
  const input = document.getElementById('sagpt-chat-input');
  
  // 开关聊天窗口
  chatBtn.onclick = function() {
    isOpen = !isOpen;
    chatWindow.style.display = isOpen ? 'flex' : 'none';
  };
  
  // 关闭按钮
  document.getElementById('sagpt-close-btn').onclick = function(e) {
    e.stopPropagation();
    isOpen = false;
    chatWindow.style.display = 'none';
  };
  
  // 快速提问
  window.sagptQuickAsk = function(text) {
    input.value = text;
    sendMessage();
  };
  
  // 发送消息
  function sendMessage() {
    const text = input.value.trim();
    if (!text) return;
    
    // 添加用户消息
    addMessage(text, 'user');
    input.value = '';
    
    // 显示加载中
    const loadingId = 'loading_' + Date.now();
    const loadingDiv = document.createElement('div');
    loadingDiv.id = loadingId;
    loadingDiv.className = 'sagpt-loading';
    loadingDiv.innerHTML = '💭 AI 思考中...';
    messagesContainer.appendChild(loadingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    // 调用 API
    fetch(API_URL + '/chat/message', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: text,
        fingerprint: 'web_' + Date.now(),
        history: []
      })
    })
    .then(r => r.json())
    .then(data => {
      document.getElementById(loadingId).remove();
      
      const reply = data.chunk || data.message || '抱歉，AI 暂时无法回答。';
      
      if (reply.includes('[AI Error') || reply.includes('[AI unavailable')) {
        addMessage('⚠️ ' + reply, 'ai');
      } else {
        // 格式化回复：加粗、列表等
        const formatted = reply
          .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
          .replace(/\n/g, '<br>');
        addMessage(formatted, 'ai');
      }
    })
    .catch(err => {
      document.getElementById(loadingId).remove();
      addMessage('⚠️ 网络错误，请稍后重试。<br><small>' + err.message + '</small>', 'ai');
    });
  }
  
  function addMessage(text, type) {
    const div = document.createElement('div');
    div.className = type === 'user' ? 'sagpt-user-msg' : 'sagpt-ai-msg';
    if (type === 'ai') div.innerHTML = text;
    else div.textContent = text;
    messagesContainer.appendChild(div);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
  }
  
  // 绑定发送
  document.getElementById('sagpt-chat-send').onclick = sendMessage;
  input.onkeypress = function(e) {
    if (e.key === 'Enter') sendMessage();
  };
  
  console.log('[SAGPT] AI Chat Widget loaded. API:', API_URL);
})();
