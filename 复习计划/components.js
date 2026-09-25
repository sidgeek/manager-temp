/* ===== 公共组件 ===== */
(function () {
  /* ---- 时间线样式（只注入一次） ---- */
  if (!document.getElementById('timeline-style')) {
    const style = document.createElement('style');
    style.id = 'timeline-style';
    style.textContent = `
      .timeline{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:14px 0;padding:14px;background:#f7f8fc;border-radius:12px}
      .timeline .item{display:flex;align-items:center;gap:6px;font-size:11.5px;color:var(--sub);background:#fff;border:1px solid #e4e7ef;border-radius:20px;padding:5px 10px;white-space:nowrap;text-decoration:none;transition:.15s}
      .timeline .item:hover{filter:brightness(.96);transform:translateY(-1px);box-shadow:0 2px 6px rgba(20,25,50,.06)}
      .timeline .item.done{background:#e8f8f2;color:#0a6b52;border-color:#bfeadd}
      .timeline .item.current{background:var(--accent-soft);color:var(--accent);border-color:#c6dbff;font-weight:600}
      .timeline .item .dot{width:7px;height:7px;border-radius:50%;background:#9aa2b1}
      .timeline .item.done .dot{background:#059669}
      .timeline .item.current .dot{background:var(--accent)}
      .timeline .arr{color:#9aa2b1;font-size:12px}
    `;
    document.head.appendChild(style);
  }

  /* ---- 渲染备考时间线 ----
     currentDay: 'day1' | 'day2' | 'day3' | 'day4'
     stageTitle: 当前阶段描述，如'基础框架构建'
  ---- */
  window.renderTimeline = function (currentDay, stageTitle) {
    const items = [
      { id: 'day1', label: 'Day 1 框架+范围', href: 'day1.html' },
      { id: 'day2', label: 'Day 2 进度+关键路径', href: 'day2.html' },
      { id: 'day3', label: 'Day 3 成本+EVM', href: 'day3.html' },
      { id: 'day4', label: 'Day 4 风险管理', href: 'day4.html' },
      { id: 'day5', label: 'Day 5 质量管理', href: 'day5.html' },
      { id: 'day6', label: 'Day 6 整合管理', href: 'day6.html' },
      { id: 'day7', label: '沟通/干系人', href: null },
      { id: 'day8', label: '案例题综合', href: null }
    ];

    const currentNum = parseInt((currentDay || '').replace('day', ''), 10) || 0;

    let html = '<div class="timeline">';
    items.forEach((item, index) => {
      const itemNum = parseInt(item.id.replace('day', ''), 10) || 99;
      let cls = 'item';
      if (item.id === currentDay) cls += ' current';
      else if (itemNum < currentNum && item.href) cls += ' done';

      const content = item.href
        ? `<a href="${item.href}" class="${cls}"><span class="dot"></span>${item.label}</a>`
        : `<div class="${cls}"><span class="dot"></span>${item.label}</div>`;

      html += content;
      if (index < items.length - 1) html += '<span class="arr">→</span>';
    });
    html += '</div>';

    const stage = document.getElementById('timelineStage');
    if (stage) {
      const titleHtml = stageTitle
        ? `<h3>当前备考阶段：${stageTitle}</h3>`
        : '<h3>当前备考阶段</h3>';
      stage.innerHTML = titleHtml + html;
    }
  };
})();
