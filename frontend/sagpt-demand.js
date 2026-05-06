/**
 * SAGPT Submit Demand Integration - React 表单专用版
 */

(function() {
  'use strict';

  const API_URL = 'https://sagpt-platform.onrender.com/api';

  // value → 中文名映射
  const COUNTRY_MAP = {
    'uae': '阿联酋', 'saudi': '沙特阿拉伯', 'qatar': '卡塔尔',
    'bahrain': '巴林', 'oman': '阿曼', 'turkey': '土耳其',
    'malaysia': '马来西亚', 'indonesia': '印度尼西亚',
    'usa': '美国', 'uk': '英国', 'germany': '德国', 'france': '法国'
  };
  const INDUSTRY_MAP = {
    'manufacturing': '制造业', 'ecommerce': '电商', 'technology': '科技',
    'finance': '金融', 'retail': '零售', 'logistics': '物流',
    'healthcare': '医疗健康', 'education': '教育', 'realestate': '房地产', 'other': '其他'
  };
  const BUDGET_MAP = {
    'low': '< ¥10,000', 'medium': '¥10,000 - ¥100,000',
    'high': '¥100,000 - ¥1,000,000', 'premium': '¥1,000,000 - ¥10,000,000'
  };

  function init() {
    const submitBtn = findSubmitButton();
    if (!submitBtn) {
      setTimeout(init, 2000);
      return;
    }
    console.log('[SAGPT-Demand] Integration active');
    submitBtn.addEventListener('click', handleSubmit, true);
  }

  function findSubmitButton() {
    const allButtons = document.querySelectorAll('button');
    for (const btn of allButtons) {
      const text = (btn.textContent || '').toLowerCase();
      if (text.includes('submit') || text.includes('提交') || text.includes('send')) {
        return btn;
      }
    }
    return document.querySelector('button[type="submit"]');
  }

  function readReactForm() {
    const selects = document.querySelectorAll('select');
    const textareas = document.querySelectorAll('textarea');
    const emailInput = document.querySelector('input[name="email"], input[type="email"]');
    const phoneInput = document.querySelector('input[name="phone"], input[name="wechat"]');

    const countryValue = selects[0]?.value || '';
    const industryValue = selects[1]?.value || '';
    const budgetValue = selects[2]?.value || '';

    return {
      target_country: COUNTRY_MAP[countryValue] || countryValue,
      industry: INDUSTRY_MAP[industryValue] || industryValue,
      scenario: 'Investment & Setup',
      budget_range: BUDGET_MAP[budgetValue] || budgetValue,
      urgency: 'normal',
      description: textareas[0]?.value || '',
      email: emailInput?.value || '',
      wechat_phone: phoneInput?.value || '',
      company_name: '',
      phone: '',
      attachments: []
    };
  }

  async function handleSubmit(e) {
    e.preventDefault();
    e.stopPropagation();

    const formData = readReactForm();
    console.log('[SAGPT-Demand] Form data:', formData);

    const missing = [];
    if (!formData.target_country) missing.push('目标国家');
    if (!formData.industry) missing.push('行业');
    if (!formData.budget_range) missing.push('预算区间');
    if (!formData.description) missing.push('需求描述');
    if (!formData.email) missing.push('邮箱');

    if (missing.length > 0) {
      alert('请填写以下必填项：\n• ' + missing.join('\n• '));
      return;
    }

    const btn = e.target;
    const originalText = btn.textContent;
    btn.textContent = '🤖 AI 智能匹配中...';
    btn.disabled = true;

    try {
      const response = await fetch(API_URL + '/demands/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData)
      });

      const result = await response.json();

      if (result.success) {
        showSuccessModal(result);
      } else {
        alert('提交失败: ' + (result.message || '未知错误'));
        btn.textContent = originalText;
        btn.disabled = false;
      }
    } catch (err) {
      alert('网络错误: ' + err.message);
      btn.textContent = originalText;
      btn.disabled = false;
    }
  }

  function showSuccessModal(result) {
    const existing = document.getElementById('sagpt-demand-modal');
    if (existing) existing.remove();

    const matches = result.preview_matches || [];
    const demandId = result.demand_id || 'N/A';

    let matchesHTML = '';
    if (matches.length > 0) {
      matchesHTML = `
        <h3 style="color:#333;margin-bottom:16px;text-align:center;">🤖 AI 为您匹配了 ${matches.length} 位专家</h3>
        <div style="display:flex;flex-direction:column;gap:12px;">
          ${matches.map((m, i) => `
            <div style="border:2px solid ${i===0?'#0d9488':'#e5e7eb'};border-radius:16px;padding:16px;display:flex;gap:16px;background:${i===0?'#f0fdfa':'white'};">
              <img src="${m.photo_url || 'https://ui-avatars.com/api/?name='+encodeURIComponent(m.name)+'&background=0d9488&color=fff'}" style="width:60px;height:60px;border-radius:50%;object-fit:cover;flex-shrink:0;">
              <div style="flex:1;">
                <div style="font-weight:600;font-size:15px;">${m.name} ${i===0?'<span style="background:#0d9488;color:white;padding:2px 8px;border-radius:10px;font-size:11px;">最佳匹配</span>':''}</div>
                <div style="font-size:13px;color:#666;">${m.company||''} · ${m.country}</div>
                <div style="font-size:12px;color:#0d9488;margin-top:4px;">⭐ ${m.rating} · ${m.experience_years}年经验</div>
                <div style="font-size:12px;color:#0d9488;font-style:italic;margin-top:4px;">💡 ${m.match_reason}</div>
              </div>
              <div style="text-align:center;">
                <div style="font-size:28px;font-weight:700;color:#0d9488;">${Math.round(m.match_score*100)}%</div>
                <div style="font-size:11px;color:#999;">匹配度</div>
              </div>
            </div>
          `).join('')}
        </div>
      `;
    } else {
      matchesHTML = `
        <div style="padding:16px;background:#fef3c7;border-radius:12px;text-align:center;">
          <p style="color:#92400e;font-size:14px;">⏳ AI 正在筛选专家，结果将通过邮件发送</p>
        </div>
      `;
    }

    const modal = document.createElement('div');
    modal.id = 'sagpt-demand-modal';
    modal.innerHTML = `
      <div style="position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.6);z-index:10000;display:flex;align-items:center;justify-content:center;">
        <div style="background:white;border-radius:20px;padding:40px;max-width:700px;width:90%;max-height:90vh;overflow-y:auto;position:relative;">
          <button onclick="document.getElementById('sagpt-demand-modal').remove()" style="position:absolute;top:16px;right:20px;background:none;border:none;font-size:28px;cursor:pointer;">&times;</button>
          
          <div style="text-align:center;margin-bottom:28px;">
            <div style="font-size:56px;">🎉</div>
            <h2 style="color:#0f766e;margin:0;">需求提交成功！</h2>
            <p style="color:#666;margin-top:8px;">AI 正在为您匹配最合适的本地专家</p>
            <p style="color:#0d9488;font-weight:600;">⏱️ 预计24小时内联系您</p>
          </div>

          ${matchesHTML}

          <div style="margin-top:24px;padding:16px;background:#f0fdfa;border-radius:12px;">
            <p style="color:#0f766e;font-size:14px;margin:0;">
              📧 详细方案发送至邮箱<br>
              📞 顾问24小时内联系<br>
              🆔 需求编号：<code>${demandId}</code>
            </p>
          </div>

          <div style="margin-top:24px;text-align:center;">
            <a href="/experts" style="display:inline-block;padding:12px 32px;background:#0d9488;color:white;text-decoration:none;border-radius:10px;">查看全部专家</a>
          </div>
        </div>
      </div>
    `;
    
    document.body.appendChild(modal);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
