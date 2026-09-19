/* ==========================================================
   软考中级专题 · 通用脚本 common.js
   所有专题页共用：返回顶部 + 答案展开/收起（事件委托）
   用法：<span class="toggle" data-target="q1">显示答案</span>
   不写 data-target 时，自动作用于所在的 .qbox
   ========================================================== */
(function () {
  'use strict';

  /* 返回顶部悬浮按钮 */
  var btn = document.getElementById('toTop');
  if (btn) {
    btn.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
    var update = function () { btn.classList.toggle('show', window.scrollY > 300); };
    window.addEventListener('scroll', update, { passive: true });
    update();
  }

  /* 答案展开 / 收起（委托，页面无需再写 onclick） */
  document.addEventListener('click', function (e) {
    var t = e.target.closest ? e.target.closest('.toggle') : null;
    if (!t) return;
    var box = t.dataset.target
      ? document.getElementById(t.dataset.target)
      : (t.closest('.qbox') || t.closest('.card'));
    if (!box) return;
    var open = box.classList.toggle('open');
    /* 按钮文案：优先用 data-open / data-close，默认「显示答案 / 隐藏答案」 */
    if (t.dataset.open && t.dataset.close) {
      t.textContent = open ? t.dataset.close : t.dataset.open;
    } else {
      t.textContent = open ? '隐藏答案' : '显示答案';
    }
  });
})();
