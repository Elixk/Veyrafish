# 维舆 · 报告页（report）还原规范

> 参考图：`report.png` · 导航激活项：**报告** · 最终标题统一为 **维舆-新时代高效通用多维度舆论平台**。

------

## 一、页面目标

报告页用于生成、编辑、定稿并导出舆情分析报告。核心视觉是中间的“宣纸报告预览”，左侧控制报告结构/设置，右侧控制导出与定稿。

Footer 口号：`采 群 言 以 成 案 ， 稽 众 论 而 定 策`。

------

## 二、整体布局

```css
.report-page .workspace.three-column {
  grid-template-columns: 320px minmax(780px, 1fr) 320px;
  gap: 16px;
  padding: 16px 24px 0;
}
.report-page .main-panel { padding: 16px; }
```

------

## 三、左侧栏：报告结构 + 报告设置

### 3.1 报告结构

```html
<section class="sidebar-section report-structure">
  <h2 class="sidebar-section-title">报告结构</h2>
  <nav class="sidebar-nav">
    <button class="sidebar-nav-item active"><i>▤</i>执行摘要</button>
    <button class="sidebar-nav-item"><i>ⓘ</i>事件概览</button>
    <button class="sidebar-nav-item"><i>⌁</i>舆情走势</button>
    <button class="sidebar-nav-item"><i>▦</i>媒体分析</button>
    <button class="sidebar-nav-item"><i>♙</i>论坛分析</button>
    <button class="sidebar-nav-item"><i>△</i>风险判断</button>
    <button class="sidebar-nav-item"><i>◌</i>对策建议</button>
    <button class="sidebar-nav-item"><i>▣</i>附录证据</button>
  </nav>
</section>
```

### 3.2 报告设置

```html
<section class="sidebar-section report-settings">
  <h2 class="sidebar-section-title">报告设置</h2>
  <label class="filter-group"><span>报告类型</span><select><option>专报</option></select></label>
  <label class="filter-group"><span>模板风格</span><select><option>政务版</option></select></label>
  <label class="filter-group"><span>时间范围</span><div class="date-picker-row">2024-05-20 ~ 2024-05-27</div></label>
  <label class="filter-group"><span>作者署名</span><input class="filter-input" value="维舆智库研究团队" /></label>
  <div class="sidebar-footer"><button class="btn-outline">保存模板</button><button class="btn-outline">重置</button></div>
</section>
```

------

## 四、中间主内容区：报告引擎 + 预览纸张

### 4.1 标题栏与工具条

```html
<div class="content-header report-header">
  <div class="engine-banner"><h2>报告引擎 · 立论成文</h2><span>采众端而成说，稽群情而定策。</span></div>
  <div class="data-timestamp">生成时间：2024-05-27 21:46:20 <button>↻</button></div>
</div>
<div class="report-toolbar">
  <button>✧ 自动生成摘要</button>
  <button>✎ 润色</button>
  <button>⌁ 插入图表</button>
  <button>❝ 引用证据</button>
</div>
```

```css
.report-toolbar { height:44px; display:flex; align-items:center; gap:28px; padding:0 24px; border:1px solid var(--color-border); border-radius:999px; background:rgba(255,255,255,.72); margin:12px 0; }
.report-toolbar button { border:0; background:transparent; font-size:14px; color:var(--color-text-primary); cursor:pointer; }
```

### 4.2 报告纸张预览

```html
<section class="report-paper-wrap">
  <article class="report-paper">
    <h1>重点事件舆情分析专报</h1>
    <div class="paper-meta">报告类型：专报　|　作者：维舆智库研究团队　|　时间范围：2024-05-20 ~ 2024-05-27　|　生成时间：2024-05-27 21:46 <span class="paper-seal">维舆</span></div>
    <section><h2>一、执行摘要</h2><p>本周重点事件在全网关注度持续上升，整体声量较上周增长 15.3%。负面情绪占比上升至 41.8%，主要集中在部分论坛和短视频平台，涉及政策争议与服务体验等议题。</p></section>
    <section><h2>二、舆情走势</h2><div class="paper-chart" id="paper-trend-chart"></div></section>
    <section class="paper-two-cols"><div><h2>三、媒体与论坛观察</h2><div class="observation positive"><b>媒体观察</b><ul><li>主流媒体以政策解读和事实澄清为主，发布积极。</li><li>地方媒体关注度上升，报道侧重民生影响。</li><li>自媒体与短视频平台传播活跃，情绪偏负面。</li></ul></div></div><div><h2>&nbsp;</h2><div class="observation warning"><b>论坛观察</b><ul><li>车主集中在维权、民生争论，讨论度较高。</li><li>网民关注点：服务体验、政策落地、信息透明度。</li><li>部分话题存在误解与情绪化表达，需及时引导。</li></ul></div></div></section>
    <section><h2>四、风险判断</h2><div class="risk-box"><b>中等级别风险（★★★★☆）</b><p>负面情绪增长较快，若回应不及时，可能引发话题扩散与舆论反弹，建议密切跟踪并加强沟通引导。</p></div></section>
    <section><h2>五、对策建议</h2><ol class="paper-suggestions"><li>强化权威信息发布，及时澄清误解，稳定公众预期。</li><li>聚焦高频关注议题，优化服务流程，回应民生关切。</li><li>加强重点平台监测与沟通，提前识别风险苗头。</li></ol></section>
    <section><h2>附证摘录</h2><div class="evidence-row"><article><b>人民日报</b><time>05-25 10:23</time><p>权威回应：多部门联合部署，切实保障民生服务稳定有序。</p></article><article><b>央视新闻</b><time>05-25 11:08</time><p>专家解读：政策调整有助于长期发展，影响可控。</p></article><article><b>澎湃新闻</b><time>05-25 14:30</time><p>现场直击：部分地区出现排队现象，相关部门正积极应对。</p></article></div></section>
  </article>
</section>
```

```css
.report-paper-wrap {
  padding: 12px 18px 16px;
  background: rgba(255,255,255,.50);
  border:1px solid var(--color-border);
  border-radius:14px;
  overflow:auto;
}
.report-paper {
  max-width: 860px;
  margin: 0 auto;
  min-height: 640px;
  padding: 34px 56px 28px;
  background: #F8F0DF url('/assets/decor/paper-texture.png') center/cover;
  border: 1px solid #D8C3A4;
  box-shadow: 0 8px 24px rgba(90,60,30,.16), inset 0 0 0 1px rgba(255,255,255,.5);
  color: #2A241E;
  font-family: var(--font-heading);
}
.report-paper h1 { text-align:center; margin:0 0 22px; font:700 28px/1.2 var(--font-heading); letter-spacing:8px; }
.paper-meta { text-align:center; padding-bottom:10px; border-bottom:2px solid #C8B89A; font-size:12px; color:#5C5044; }
.paper-seal { display:inline-grid; place-items:center; margin-left:8px; border:1px solid var(--color-primary); color:var(--color-primary); padding:2px 4px; }
.report-paper h2 { margin:14px 0 8px; font-size:16px; }
.report-paper p,.report-paper li { font-size:13px; line-height:1.72; }
.paper-chart { height:130px; background:rgba(255,255,255,.35) url('/assets/decor/chart-mountain.svg') right top/200px auto no-repeat; }
.paper-two-cols { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
.observation { border:1px solid var(--color-border); border-radius:6px; padding:10px 14px; background:rgba(255,255,255,.42); }
.observation.positive { background:#F5FBF1; } .observation.warning { background:#FFF7E6; }
.risk-box { border:1px solid #EF9A9A; background:#FFF0F0; border-radius:6px; padding:10px 14px; color:var(--color-primary); }
.paper-suggestions { margin:0; padding-left:22px; }
.evidence-row { display:grid; grid-template-columns:repeat(3, 1fr); gap:10px; }
.evidence-row article { border:1px solid var(--color-border); border-radius:6px; background:rgba(255,255,255,.45); padding:8px 10px; font-size:12px; }
.evidence-row time { display:block; color:var(--color-text-muted); font-size:11px; }
```

------

## 五、右侧栏：导出与定稿

```html
<aside class="right-panel report-export">
  <section class="right-section export-card">
    <h2 class="panel-title">导出与定稿</h2>
    <div class="button-group"><b>报告类型</b><button>简报</button><button class="active">专报</button><button>日报</button></div>
    <div class="button-group"><b>版式风格</b><button class="active">政务版</button><button>企业版</button><button>学术版</button></div>
    <div class="draft-status"><b>定稿状态</b><p><span class="green-dot"></span>草稿中 <em>未定稿</em><button>标记为终稿</button></p></div>
    <div class="report-stats"><span><b>12</b>页数</span><span><b>48</b>引证数</span><span><b>6</b>图表数</span></div>
    <section class="quick-actions"><h3>快捷操作</h3><button>生成摘要</button><button>一键润色</button><button>添加页眉</button><button>校核引证</button></section>
    <div class="export-actions"><button class="btn-primary full-width">导出 PDF</button><button class="btn-secondary full-width">导出 Word</button><button class="btn-outline full-width">生成长图</button></div>
  </section>
</aside>
```

```css
.button-group { margin:12px 0; }
.button-group b { display:block; margin-bottom:8px; font-size:14px; }
.button-group button { height:34px; min-width:72px; margin-right:8px; border:1px solid var(--color-border); border-radius:6px; background:rgba(255,255,255,.65); }
.button-group button.active { color:var(--color-primary); border-color:var(--color-primary); background:#FFF0F0; font-weight:700; }
.draft-status { margin:14px 0; padding:12px 0; border-top:1px solid var(--color-divider); border-bottom:1px solid var(--color-divider); }
.green-dot { display:inline-block; width:9px; height:9px; border-radius:50%; background:#21A366; margin-right:8px; }
.draft-status em { margin-left:46px; color:var(--color-text-muted); font-style:normal; }
.draft-status button { float:right; height:30px; border:1px solid var(--color-border-strong); border-radius:6px; background:rgba(255,255,255,.65); color:var(--color-gold); }
.report-stats { display:grid; grid-template-columns:repeat(3,1fr); text-align:center; border-bottom:1px solid var(--color-divider); padding-bottom:12px; }
.report-stats span { border-right:1px solid var(--color-divider); font-size:12px; color:var(--color-text-muted); }
.report-stats span:last-child { border-right:0; }
.report-stats b { display:block; font:700 22px/1 var(--font-mono); color:var(--color-text-primary); margin-bottom:4px; }
.quick-actions { margin:16px 0; display:grid; gap:10px; }
.quick-actions h3 { margin:0 0 4px; font-size:14px; }
.quick-actions button { height:36px; text-align:left; padding:0 14px; border:1px solid var(--color-border); border-radius:6px; background:rgba(255,255,255,.65); }
.export-actions { display:grid; gap:10px; margin-top:16px; }
.export-actions .btn-primary { height:48px; font-size:18px; font-weight:700; }
.export-actions .btn-secondary,.export-actions .btn-outline { height:42px; font-size:16px; }
```

------

## 六、图表与导出实现建议

1. 中间报告预览可以先用 HTML/CSS 实现，导出 PDF 时使用 `html2canvas + jsPDF` 或后端渲染。
2. 报告纸张宽度固定，外部容器滚动，避免在浏览器缩放时正文错位。
3. 工具条按钮需联动报告内容：自动生成摘要、润色、插入图表、引用证据。
4. 导出按钮右侧固定，不随报告纸张滚动，保证操作可见。
5. “标记为终稿”点击后状态可变为：绿色 `已定稿`，按钮置灰或改为“撤回终稿”。

------

## 七、还原验收点

- 中间纸张必须具有宣纸质感、内阴影、边框和“报告”排版，不要做成普通白色卡片。
- 工具条为圆角长条，横向 4 个操作。
- 右侧“导出 PDF”按钮红色最大，“导出 Word”金色次之，“生成长图”为描边。
- 左侧结构导航从“执行摘要”到“附录证据”一共 8 项，执行摘要 active。
- 报告中必须包含趋势折线图、媒体/论坛观察双栏、风险判断红框、附证摘录卡片。
