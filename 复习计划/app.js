
/* ===== 渲染计划卡片 ===== */
const areaColors={"第 1 周":"#d97706","第 2 周":"#2563eb","第 3 周":"#059669","第 4 周":"#7c3aed","第 5 周":"#e11d48","第 6 周（考前）":"#37415c"};
const pc=document.getElementById('planCards');
pc.innerHTML=PLAN.map((p,i)=>`
 <div class="card phase" style="border-left-color:${areaColors[p.w]}">
  <h3><span class="tag" style="background:${areaColors[p.w]}1a;color:${areaColors[p.w]}">${p.w}</span>${p.title}</h3>
  <div class="goal">${p.goal}</div>
  <ul class="tasks">${p.tasks.map((t,j)=>`<li data-k="p${i}-${j}"><input type="checkbox"><span>${t}</span></li>`).join('')}</ul>
  <div class="mile">🏁 ${p.mile}</div>
 </div>`).join('');

/* ===== 打卡状态 ===== */
const KEY='ruankao_plan_v1';
let st={};try{st=JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){}
function refresh(){
 let done=0,total=0;
 document.querySelectorAll('ul.tasks li[data-k]').forEach(li=>{
   const k=li.dataset.k;const c=li.querySelector('input');c.checked=!!st[k];
   li.classList.toggle('done',!!st[k]);total++;if(st[k])done++;
 });
 // 考前清单
 document.querySelectorAll('#key ul.tasks li:not([data-k])').forEach((li,i)=>{});
 const bar=document.getElementById('totalBar'),txt=document.getElementById('totalTxt');
 const pct=total?Math.round(done/total*100):0;
 bar.style.width=pct+'%';txt.textContent=`已完成 ${done} / ${total} 项任务（${pct}%）`;
}
document.querySelectorAll('ul.tasks li[data-k] input').forEach(c=>{
 c.addEventListener('change',()=>{
   const k=c.closest('li').dataset.k;
   st[k]=c.checked;
   localStorage.setItem(KEY,JSON.stringify(st));
   refresh();
 });
});
document.getElementById('resetBtn').addEventListener('click',()=>{st={};localStorage.removeItem(KEY);refresh();});
refresh();

/* ===== 矩阵 ===== */
const keyOf={};
ITTO.forEach(p=>{keyOf[p.area+'|'+p.process]=p});
const mtx=document.getElementById('mtxTable');
let h='<tr><th class="rowh" style="background:transparent"></th>'+GROUPS.map(g=>`<th class="h-${GCLS[g]}">${g.replace('过程组','')}</th>`).join('')+'</tr>';
AREAS.forEach(a=>{
 const label=a.replace('项目','').replace('管理','');
 const areaClick=AREA_EXTRA[a]?` style="cursor:pointer" onclick="showAreaExtra('${a}')" title="点击查看${label}领域速记"`:'';
 h+=`<tr><th class="rowh"${areaClick}>${label}</th>`;
 GROUPS.forEach(g=>{
   const ps=ITTO.filter(p=>p.area===a&&p.group===g);
   h+=`<td class="cell">`+ps.map(p=>`<button class="chip c-${GCLS[g]}" onclick="showProc('${p.area}','${p.process}')">${p.process}</button>`).join('')+`</td>`;
 });
 h+='</tr>';
});
mtx.innerHTML=h;

/* ===== 大纲树 ===== */
const tree=document.getElementById('outlineTree');
tree.innerHTML=AREAS.map(a=>{
 const ps=ITTO.filter(p=>p.area===a);
 return `<div class="area-block">
  <div class="area-head" onclick="this.parentElement.classList.toggle('open')">
    <span class="arrow">▶</span><b>${a}</b><span class="cnt">${ps.length} 个过程</span>
    <span style="margin-left:auto;font-size:11.5px;color:#9aa2b1">点击展开/折叠</span>
  </div>
  <div class="proc-list">${ps.map(p=>`
    <div class="proc-item">
      <h4><span class="pg chip c-${GCLS[p.group]}" style="display:inline-block;width:auto;margin:0;font-size:10.5px;padding:1px 7px;border-radius:5px;cursor:default">${p.group.replace('过程组','')}</span>${p.process}</h4>
      <div class="brief">${p.def||''}</div>
      <button class="det" onclick="showProc('${p.area}','${p.process}')">查看 ITTO 详情 →</button>
    </div>`).join('')}</div>
  ${AREA_EXTRA[a]||''}
 </div>`}).join('');
document.querySelectorAll('.exp').forEach(b=>b.addEventListener('click',()=>{
 document.querySelectorAll('.area-block').forEach(x=>x.classList.toggle('open',b.dataset.all==='open'));
}));

/* ===== 抽屉 ===== */
const drawer=document.getElementById('drawer'),mask=document.getElementById('mask');
function esc(s){return (s||'').replace(/&/g,'&amp;').replace(/<(?!\/?b>)/g,'&lt;')}
function showProc(area,proc){
 const p=keyOf[area+'|'+proc];if(!p)return;
 document.getElementById('dTitle').textContent=proc+'（'+p.group+' · '+p.area+'）';
 document.getElementById('dBody').innerHTML=`
  <div class="dsec t-def"><span class="dt">定义</span><div class="dv">${esc(p.def)}</div></div>
  <div class="dsec t-role"><span class="dt">主要作用</span><div class="dv">${esc(p.role)}</div></div>
  <div class="dsec t-freq"><span class="dt">开展频率</span><div class="dv">${esc(p.freq)}</div></div>
  <div class="dsec t-in"><span class="dt">输入 Input</span><div class="dv">${esc(p.input)}</div></div>
  <div class="dsec t-tool"><span class="dt">工具与技术 T&T</span><div class="dv">${esc(p.tools)}</div></div>
  <div class="dsec t-out"><span class="dt">输出 Output</span><div class="dv">${esc(p.output)}</div></div>
  ${p.extra?`<div class="dsec t-extra"><span class="dt">补充说明</span><div class="dv">${esc(p.extra)}</div></div>`:''}`;
 document.body.classList.add('show-drawer');
}
function showAreaExtra(area){
 const html=AREA_EXTRA[area];if(!html)return;
 document.getElementById('dTitle').textContent=area+' · 领域速记';
 document.getElementById('dBody').innerHTML=html;
 document.body.classList.add('show-drawer');
}
function hideDrawer(){document.body.classList.remove('show-drawer')}
mask.addEventListener('click',hideDrawer);
document.getElementById('dClose').addEventListener('click',hideDrawer);
document.addEventListener('keydown',e=>{if(e.key==='Escape')hideDrawer()});

/* ===== 导航高亮 ===== */
const secs=[...document.querySelectorAll('section')];
const links=[...document.querySelectorAll('nav.toc a')];
window.addEventListener('scroll',()=>{
 let cur=secs[0];secs.forEach(s=>{if(s.getBoundingClientRect().top<120)cur=s});
 links.forEach(l=>l.classList.toggle('on',l.getAttribute('href')==='#'+cur.id));
},{passive:true});

/* ===== 返回顶部 ===== */
(function(){var b=document.getElementById('toTop');function u(){b.classList.toggle('show',window.scrollY>300);}window.addEventListener('scroll',u,{passive:true});u();})();
