# 维舆 · 检索页（query）还原规范

> 参考图：`query.png` · 导航激活项：**检索** · 最终标题统一为 **维舆-新时代高效通用多维度舆论平台**。

------

## 一、页面目标

检索页强调“输入关键词 → 展示聚类/结果 → 查看详情与快速操作”。参考图主题为“新能源车 起火 自燃”，但实现应支持任意关键词。

Footer 口号：`钩 沉 索 隐 ， 求 其 本 末`。

------

## 二、整体布局

```css
.query-page .workspace.three-column {
  grid-template-columns: 276px minmax(780px, 1fr) 340px;
  gap: 14px;
  padding: 16px 24px 0;
}
```

------

## 三、左侧栏：检索条件

```html
<aside class="left-panel sidebar query-sidebar">
  <section class="sidebar-section">
    <h2 class="sidebar-section-title">检索条件</h2>
    <label class="filter-group keyword-search">
      <span>关键词检索</span>
      <div class="keyword-box"><input value="新能源汽车 起火 自燃"/><button>⌕</button></div>
      <small>示例：新能源汽车 起火 自燃</small>
    </label>
    <label class="filter-group"><span>时间范围</span><div class="date-picker-row">2024-05-20 ~ 2024-05-27</div></label>
    <label class="filter-group"><span>数据来源</span><select><option>全部来源（自动汇聚）</option></select></label>
    <label class="filter-group"><span>情感倾向</span><select><option>全部情感</option></select></label>
    <label class="filter-group"><span>热度等级</span><select><option>全部等级</option></select></label>
    <label class="filter-group"><span>平台类型</span><select><option>全部平台</option></select></label>
    <label class="filter-group"><span>相关主题</span><select><option>全部主题</option></select></label>
  </section>
  <section class="advanced-search">
    <h3>高级检索 <input type="checkbox" checked /></h3>
    <label><input type="checkbox" /> 布尔检索 <input placeholder="示例：（起火 OR 自燃）AND 新能源" /></label>
    <label><input type="checkbox" /> 精确短语 <input placeholder="示例：电池热失控" /></label>
    <label><input type="checkbox" checked /> 相似内容召回 <input type="range" /></label>
    <label><input type="checkbox" checked /> 去重聚合 <select><option>语义去重（相似度 0.85）</option></select></label>
  </section>
  <div class="sidebar-footer"><button class="btn-outline">保存格式</button><button class="btn-outline">重置</button></div>
</aside>
```

```css
.keyword-box { height:36px; display:grid; grid-template-columns:1fr 34px; border:1px solid var(--color-border-strong); border-radius:8px; overflow:hidden; background:rgba(255,255,255,.72); }
.keyword-box input { border:0; background:transparent; padding:0 12px; }
.keyword-box button { border:0; border-left:1px solid var(--color-border); background:transparent; color:var(--color-text-muted); }
.advanced-search { margin-top:14px; padding-top:12px; border-top:1px solid var(--color-divider); }
.advanced-search h3 { display:flex; justify-content:space-between; align-items:center; font:700 16px/1 var(--font-heading); }
.advanced-search label { display:grid; grid-template-columns:20px 78px 1fr; gap:6px; align-items:center; margin:10px 0; font-size:12px; }
.advanced-search input:not([type]), .advanced-search select { height:28px; border:1px solid var(--color-border); border-radius:5px; padding:0 8px; font-size:11px; }
```

------

## 四、中间主内容区

### 4.1 搜索栏与保存视角

```html
<div class="content-header query-header">
  <div class="engine-banner"><h2>检索引擎 · 穷源索隐</h2><span>数如泉来，先求其本；脉络其变，当考其迹。</span></div>
  <div class="data-timestamp">数据更新：2024-05-27 21:46:20 <button>↻</button></div>
</div>
<div class="search-command-row">
  <input value="新能源汽车 起火 自燃" />
  <button class="btn-primary">⌕ 开始检索</button>
  <button class="btn-outline">保存为视角</button>
</div>
```

```css
.search-command-row { display:grid; grid-template-columns:1fr 142px 142px; gap:14px; margin-top:12px; }
.search-command-row input { height:40px; border:1px solid var(--color-border-strong); border-radius:8px; background:rgba(255,255,255,.75); padding:0 16px; font-size:16px; }
```

### 4.2 KPI 指标

五项指标：检索结果、高相关命中、风险相关、可疑扩散源、已归档证据。

```html
<div class="kpi-bar query-kpis">
  <article class="kpi-card"><div class="kpi-header"><i>▤</i><span>检索结果</span></div><strong>128,456</strong><em>较昨日 ▲ 12.35%</em></article>
  <article class="kpi-card"><div class="kpi-header"><i>◎</i><span>高相关命中</span></div><strong>86,732</strong><em>较昨日 ▲ 15.82%</em></article>
  <article class="kpi-card"><div class="kpi-header"><i>盾</i><span>风险相关</span></div><strong>7,845</strong><em>较昨日 ▲ 8.21%</em></article>
  <article class="kpi-card"><div class="kpi-header"><i>⌘</i><span>可疑扩散源</span></div><strong>326</strong><em>较昨日 ▲ 6.17%</em></article>
  <article class="kpi-card"><div class="kpi-header"><i>▰</i><span>已归档证据</span></div><strong>12,873</strong><em>较昨日 ▲ 10.45%</em></article>
</div>
```

### 4.3 结果聚类概览

```html
<section class="cluster-panel panel-card">
  <div class="section-header"><h3 class="section-title">结果聚类概览 <span class="help">?</span></h3><a>更多聚类 ＋</a></div>
  <div class="cluster-grid">
    <article><i class="hot">♨</i><b># 电池热失控致起火</b><span>32,684 条（25.45%）</span></article>
    <article><i class="shield">盾</i><b># 充电安全隐患</b><span>28,417 条（22.12%）</span></article>
    <article><i class="car">车</i><b># 车型与品牌事件</b><span>21,795 条（16.93%）</span></article>
    <article><i class="argue">⚖</i><b># 维权与售后争议</b><span>18,936 条（14.75%）</span></article>
  </div>
</section>
```

```css
.cluster-panel { margin-top:14px; padding:14px 16px; }
.cluster-grid { display:grid; grid-template-columns:repeat(4, 1fr); gap:12px; }
.cluster-grid article { min-height:58px; display:grid; grid-template-columns:42px 1fr; align-items:center; gap:8px; padding:10px 12px; border:1px solid var(--color-border); border-radius:8px; background:rgba(255,255,255,.58); }
.cluster-grid i { grid-row:span 2; width:34px; height:34px; border-radius:50%; display:grid; place-items:center; font-style:normal; }
.cluster-grid b { font-size:13px; }
.cluster-grid span { font-size:11px; color:var(--color-text-muted); }
```

### 4.4 检索结果列表

```html
<section class="results-panel panel-card">
  <div class="section-header"><h3 class="section-title">检索结果（共 128,456 条）</h3><div class="sort-tools">排序：<select><option>相关度</option></select><button>☰</button><button>▦</button></div></div>
  <div class="result-list">
    <article class="result-item active"><span class="rank">1</span><div class="result-body"><h4>某品牌新能源汽车路边自燃，官方回应：正在调查原因</h4><p>来源：澎湃新闻　2024-05-27 19:32</p><p>5月27日，某市一辆新能源汽车在行驶途中突然起火，现场浓烟滚滚……</p><div class="tags"><em>负向</em><em>高热</em><em>新闻</em></div></div><div class="result-actions"><button>查看原文</button><button>加入卷宗</button><button>关联分析</button></div></article>
    <article class="result-item"><span class="rank orange">2</span><div class="result-body"><h4>车主发视频称新能源车充电后冒烟起火，4S店称非质量问题</h4><p>来源：抖音　2024-05-27 18:14</p><p>车主视频展示，车辆在自家车库充电完成后不久冒出烟并起火……</p><div class="tags"><em>负向</em><em>高热</em><em>短视频</em></div></div><div class="result-actions"><button>查看原文</button><button>加入卷宗</button><button>关联分析</button></div></article>
    <article class="result-item"><span class="rank yellow">3</span><div class="result-body"><h4>官方通报：一新能源汽车在地下车库起火，无人员伤亡</h4><p>来源：南方都市报　2024-05-27 17:02</p><p>通报称，火灾原因仍在进一步调查，相关部门已妥善处理……</p><div class="tags"><em>中性</em><em>中热</em><em>新闻</em></div></div><div class="result-actions"><button>查看原文</button><button>加入卷宗</button><button>关联分析</button></div></article>
  </div>
  <button class="load-more">加载更多 ↓</button>
</section>
```

```css
.results-panel { margin-top:14px; padding:14px 16px; }
.result-list { display:flex; flex-direction:column; gap:8px; }
.result-item { display:grid; grid-template-columns:28px 1fr 330px; gap:12px; padding:12px; border:1px solid var(--color-border); border-radius:8px; background:rgba(255,255,255,.6); }
.result-item.active { border-color:var(--color-negative-light); box-shadow:0 0 0 1px rgba(198,40,40,.1); }
.rank { width:22px; height:22px; border-radius:5px; background:var(--color-primary); color:#fff; display:grid; place-items:center; font-weight:700; }
.rank.orange { background:#F57C00; } .rank.yellow { background:#F9A825; }
.result-body h4 { margin:0 0 6px; font-size:16px; }
.result-body p { margin:4px 0; font-size:12px; color:var(--color-text-secondary); line-height:1.55; }
.tags { display:flex; gap:8px; margin-top:6px; }
.tags em { font-style:normal; padding:2px 8px; border-radius:4px; background:#FFF0F0; color:var(--color-primary); font-size:11px; }
.result-actions { display:grid; grid-template-columns:repeat(3, 1fr); gap:10px; align-self:center; }
.result-actions button { height:32px; border:1px solid var(--color-border); border-radius:6px; background:rgba(255,255,255,.65); }
.load-more { display:block; margin:12px auto 0; min-width:140px; height:32px; border:1px solid var(--color-border); border-radius:6px; background:rgba(255,255,255,.72); }
```

------

## 五、右侧栏：结果详情 + 快捷操作 + 相关结果

```html
<aside class="right-panel query-detail">
  <section class="right-section detail-card">
    <h2 class="panel-title">结果详情 <span class="star">☆</span><span class="more">⋮</span></h2>
    <article class="selected-detail"><h3><span>1</span>某品牌新能源汽车路边自燃，官方回应：正在调查原因</h3><p class="meta">来源：澎湃新闻　2024-05-27 19:32:18</p><p>5月27日，某市一辆新能源汽车在行驶途中突然起火，现场浓烟滚滚……</p><dl><dt>重点实体：</dt><dd>某品牌汽车、电池系统、热失控、车辆、消防</dd><dt>来源可信度：</dt><dd>★★★★☆ 4.2/5</dd><dt>相似内容：</dt><dd>1,236 条 〉</dd><dt>话题标签：</dt><dd>自燃事件、官方通报、电池问题、现场处置</dd></dl></article>
  </section>
  <section class="right-section quick-actions"><h2 class="panel-title">快捷操作</h2><div class="action-grid"><button>授为佐证</button><button>归入报告</button><button>加入研判</button><button>追其原帖</button></div></section>
  <section class="right-section related-card"><h2 class="panel-title">相关结果 <small>换一批 ↻</small></h2><ol><li>官方通报：一新能源汽车在地下车库起火… <time>05-27</time></li><li>车主发视频称新能源车充电后冒烟起火… <time>05-27</time></li><li>专家解读：高温天气下新能源车自燃… <time>05-27</time></li><li>新能源车连续起火引热议，网友质疑… <time>05-27</time></li><li>某小区多辆新能源车自燃，物业：正在… <time>05-26</time></li></ol></section>
</aside>
```

```css
.detail-card h3 { margin:0; font-size:16px; line-height:1.5; }
.detail-card h3 span { display:inline-grid; place-items:center; width:22px; height:22px; margin-right:6px; border-radius:5px; background:var(--color-primary); color:#fff; font-size:12px; }
.selected-detail p { font-size:12px; line-height:1.7; color:var(--color-text-secondary); }
.selected-detail dl { font-size:12px; }
.selected-detail dt { margin-top:10px; font-weight:700; }
.selected-detail dd { margin:5px 0 0; color:var(--color-text-secondary); }
.action-grid { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
.action-grid button { height:48px; border:1px solid var(--color-border); border-radius:8px; background:rgba(255,255,255,.65); font-size:14px; }
.related-card ol { padding:0; list-style:none; }
.related-card li { display:grid; grid-template-columns:20px 1fr 42px; gap:6px; padding:8px 0; border-bottom:1px solid var(--color-divider); font-size:12px; }
.related-card li::before { content:counter(item); counter-increment:item; width:16px; height:16px; border:1px solid var(--color-border); border-radius:3px; display:grid; place-items:center; }
.related-card ol { counter-reset:item; }
.related-card time { color:var(--color-text-muted); }
```

------

## 六、还原验收点

- 搜索命令行必须突出，红色“开始检索”按钮宽而醒目。
- 聚类卡片四列，图标圆形淡色底，卡片高度一致。
- 检索结果第 1 条有红色描边高亮，右侧详情同步展示第 1 条内容。
- 左侧高级检索开关保持红色开启状态，复选框与范围条风格统一。
- 右侧快捷操作为 2×2 宫格按钮。
