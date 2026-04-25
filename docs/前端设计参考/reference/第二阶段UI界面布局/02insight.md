# 维舆 · 洞察页（insight）还原规范

> 参考图：`insight.png` · 导航激活项：**洞察** · 最终标题统一为 **维舆-新时代高效通用多维度舆论平台**。

------

## 一、页面目标

洞察页用于呈现“总体态势、风险指数、情绪结构、事件演进、核心主体与研判建议”。整体采用三栏布局：左侧筛选，中间分析，右侧结论。

- 左侧：洞察维度 + 研判条件
- 中间：洞察引擎主工作台（KPI、趋势图、时间轴、矩阵、观点摘录）
- 右侧：洞察摘要、风险等级、关键主体、导出/深入研判按钮
- Footer：`察 微 知 著 ， 以 舆 定 策`

------

## 二、整体布局

```css
.insight-page .workspace.three-column {
  grid-template-columns: 280px minmax(760px, 1fr) 356px;
  gap: 14px;
  padding: 16px 24px 0;
}
.insight-page .left-panel { padding: 16px 14px; }
.insight-page .main-panel { padding: 16px; }
.insight-page .right-panel { padding: 16px 14px; }
```

> 参考图实际左栏约 280px、右栏约 350px，比旧版全局规范的 220/260 更宽；实现时洞察页可覆盖全局尺寸，以便接近效果图。

------

## 三、左侧栏：洞察维度 + 研判条件

### 3.1 洞察维度

```html
<aside class="sidebar left-panel">
  <section class="sidebar-section">
    <h2 class="sidebar-section-title">洞察维度</h2>
    <nav class="sidebar-nav">
      <button class="sidebar-nav-item active"><i>▥</i>总体态势</button>
      <button class="sidebar-nav-item"><i>♡</i>情感分布</button>
      <button class="sidebar-nav-item"><i>△</i>风险异动</button>
      <button class="sidebar-nav-item"><i>⌁</i>热点演进</button>
      <button class="sidebar-nav-item"><i>♙</i>关键主体</button>
      <button class="sidebar-nav-item"><i>▧</i>核心观点</button>
    </nav>
  </section>
</aside>
```

```css
.insight-page .sidebar-nav-item { height: 40px; font-size: 14px; }
.insight-page .sidebar-nav-item i { width: 22px; text-align:center; font-style:normal; font-size:18px; color:currentColor; }
```

### 3.2 研判条件

```html
<section class="sidebar-section filter-card">
  <h2 class="sidebar-section-title">研判条件</h2>
  <label class="filter-group"><span>时间范围</span><div class="date-picker-row">近7天（2024-05-21 ~ 2024-05-27） <b>▣</b></div></label>
  <label class="filter-group"><span>事件类别</span><select><option>全部事件类别</option></select></label>
  <label class="filter-group"><span>数据来源</span><select><option>全平台（自动汇聚）</option></select></label>
  <label class="filter-group"><span>区域</span><select><option>全国</option></select></label>
  <label class="filter-group"><span>风险等级</span><select><option>全部等级</option></select></label>
  <div class="sidebar-footer"><button class="btn-outline">保存视角</button><button class="btn-outline">重置</button></div>
</section>
```

------

## 四、中间主内容区

### 4.1 页面标题栏

```html
<div class="content-header">
  <div class="engine-banner">
    <h2>洞察引擎 · 察微知著</h2>
    <span>观其势，析其源，得其理。</span>
  </div>
  <div class="data-timestamp">数据更新：2024-05-27 21:46:20 <button>↻</button></div>
</div>
```

```css
.content-header {
  display:flex; align-items:center; justify-content:space-between;
  padding-bottom:12px;
  border-bottom:1px solid var(--color-border);
}
.engine-banner { display:flex; align-items:flex-end; gap:18px; }
.engine-banner h2 { margin:0; font:700 22px/1.1 var(--font-heading); letter-spacing:3px; }
.engine-banner h2::after { content:''; display:block; width:20px; height:2px; background:var(--color-primary); margin-top:10px; }
.engine-banner span { margin-bottom:3px; font:14px/1 var(--font-display); color:var(--color-text-muted); letter-spacing:2px; }
```

### 4.2 KPI 顶部指标行

```html
<div class="kpi-bar">
  <article class="kpi-card"><div class="kpi-header"><i>♨</i><span>综合热度</span></div><strong>128,456</strong><em>较昨日 ▲ 12.35%</em></article>
  <article class="kpi-card"><div class="kpi-header"><i>盾</i><span>风险指数</span></div><strong>78.6</strong><em>较昨日 ▲ 8.21%</em></article>
  <article class="kpi-card"><div class="kpi-header"><i>☺</i><span>正面占比</span></div><strong>32.6%</strong><em class="green">较昨日 ▲ 2.86%</em></article>
  <article class="kpi-card"><div class="kpi-header"><i>☹</i><span>负面占比</span></div><strong>41.8%</strong><em>较昨日 ▲ 1.62%</em></article>
  <article class="kpi-card"><div class="kpi-header"><i>⌁</i><span>传播峰值</span></div><strong>18,723</strong><em>较昨日 ▲ 15.33%</em></article>
</div>
```

```css
.insight-page .kpi-bar { margin:14px 0 14px; }
.insight-page .kpi-card strong { display:block; margin-left:42px; font:700 28px/1 var(--font-mono); }
.insight-page .kpi-card em { display:block; margin:7px 0 0 42px; font-style:normal; font-size:11px; color:var(--color-negative); }
.insight-page .kpi-card em.green { color:var(--color-positive); }
```

### 4.3 舆情趋势图

```html
<section class="chart-section panel-card">
  <div class="section-header">
    <h3 class="section-title">舆情趋势（近7天）</h3>
    <div class="chart-actions"><button>⌁</button><button>▥</button><button>⇩</button></div>
  </div>
  <div class="trend-chart" id="insight-trend-chart"></div>
</section>
```

```css
.chart-section { padding:12px 16px; }
.trend-chart { height:220px; background:url('/assets/decor/chart-mountain.svg') right top/260px auto no-repeat; }
.chart-actions { display:flex; gap:10px; color:var(--color-gold); }
.chart-actions button { border:0; background:transparent; color:var(--color-gold); font-size:18px; cursor:pointer; }
```

ECharts 数据建议：

```js
const x = ['05-21','05-22','05-23','05-24','05-25','05-26','05-27'];
const series = [
  { name:'总量',  data:[8500,13600,10800,12900,17200,12600,10900], color:'#1A1A1A' },
  { name:'正向',  data:[4100,4700,3500,5200,5800,4300,4100], color:'#4CAF50' },
  { name:'负向',  data:[5600,7200,5300,7400,9300,6500,6100], color:'#E53935' },
  { name:'中性',  data:[2600,2900,2000,3000,3400,2700,2600], color:'#9E9E9E' }
];
```

### 4.4 下方两列：事件演进 + 情绪风险矩阵

```css
.bottom-grid {
  display:grid;
  grid-template-columns: 1fr 1.1fr;
  gap:14px;
  margin-top:14px;
}
.timeline-section,
.matrix-section { padding:14px 16px; }
```

#### 4.4.1 事件演进时间轴

```html
<section class="timeline-section panel-card">
  <h3 class="section-title">事件演进时间轴</h3>
  <ol class="timeline">
    <li><time>05-21 09:12</time><span class="tag tag-hot">初始爆发</span><p>事件相关话题首次在社交平台扩散，引发关注。</p></li>
    <li><time>05-22 11:35</time><span class="tag tag-high">快速升温</span><p>多家媒体跟进报道，讨论量快速上升。</p></li>
    <li><time>05-24 14:20</time><span class="tag tag-dispute">舆论分化</span><p>正负面观点交替加剧，情绪开始明显分化。</p></li>
    <li><time>05-25 19:48</time><span class="tag tag-media">达到峰值</span><p>舆情热度达到近7天峰值，传播广泛。</p></li>
    <li><time>05-27 10:05</time><span class="tag tag-media">回落趋稳</span><p>官方回应及权威信息发布，舆情逐步回落。</p></li>
  </ol>
</section>
```

```css
.timeline { list-style:none; margin:12px 0 0; padding:0 0 0 24px; position:relative; }
.timeline::before { content:''; position:absolute; left:6px; top:4px; bottom:8px; width:2px; background:var(--color-border-strong); }
.timeline li { position:relative; display:grid; grid-template-columns:88px auto 1fr; gap:8px; align-items:start; margin-bottom:11px; font-size:12px; }
.timeline li::before { content:''; position:absolute; left:-22px; top:3px; width:10px; height:10px; border-radius:50%; background:var(--color-negative); border:2px solid #fff; }
.timeline time { color:var(--color-text-secondary); font-size:11px; }
.timeline p { margin:0; color:var(--color-text-secondary); line-height:1.5; }
```

#### 4.4.2 情绪与风险矩阵

```html
<section class="matrix-section panel-card">
  <div class="section-header">
    <h3 class="section-title">情绪与风险矩阵 <span class="help">?</span></h3>
    <span class="matrix-meta">气泡大小：讨论量　风险值：<b>78.6</b></span>
  </div>
  <div class="matrix-grid">
    <div class="quadrant tl"><b>低风险-积极</b><strong>32.6%<br/>45,812</strong><i class="bubble green large"></i></div>
    <div class="quadrant tr"><b>高风险-积极</b><strong>15.1%<br/>21,208</strong><i class="bubble orange medium"></i></div>
    <div class="quadrant bl"><b>低风险-消极</b><strong>10.5%<br/>14,758</strong><i class="bubble gray small"></i></div>
    <div class="quadrant br"><b>高风险-消极</b><strong>41.8%<br/>58,678</strong><i class="bubble red xlarge"></i></div>
  </div>
</section>
```

```css
.matrix-meta { font-size:12px; color:var(--color-text-muted); }
.matrix-meta b { color:var(--color-primary); }
.matrix-grid { display:grid; grid-template-columns:1fr 1fr; height:210px; border:1px solid var(--color-border-strong); border-radius:8px; overflow:hidden; }
.quadrant { position:relative; padding:16px; border-right:1px dashed var(--color-border-strong); border-bottom:1px dashed var(--color-border-strong); }
.quadrant:nth-child(2n) { border-right:0; }
.quadrant:nth-child(n+3) { border-bottom:0; }
.tl { background:#F1F8E9; } .tr { background:#FFF8E1; } .bl { background:#F5F5F5; } .br { background:#FFEBEE; }
.quadrant b { color:var(--color-primary); font-size:13px; }
.quadrant strong { display:block; margin-top:6px; font:700 16px/1.4 var(--font-mono); }
.bubble { position:absolute; right:36px; bottom:26px; border-radius:50%; opacity:.72; }
.bubble.green { background:#4CAF50; } .bubble.orange { background:#F57C00; } .bubble.gray { background:#8A8A8A; } .bubble.red { background:#C62828; }
.large { width:48px; height:48px; } .medium { width:34px; height:34px; } .small { width:26px; height:26px; } .xlarge { width:62px; height:62px; }
```

### 4.5 核心论点摘录

```html
<section class="viewpoints-section panel-card">
  <div class="section-header"><h3 class="section-title">核心论点摘录</h3><a>查看更多 〉</a></div>
  <div class="viewpoints-grid">
    <blockquote>“事件核心焦点在于责任认定与信息透明度，用户普遍呼吁公开调查结果。”</blockquote>
    <blockquote>“部分观点认为处理措施偏迟缓，期待更有力的管理与改进。”</blockquote>
    <blockquote>“也有声音肯定相关部门的及时回应，强调理性看待网络舆情。”</blockquote>
  </div>
</section>
```

```css
.viewpoints-section { margin-top:14px; padding:12px 16px; }
.viewpoints-grid { display:grid; grid-template-columns:repeat(3, 1fr); gap:16px; }
.viewpoints-grid blockquote { margin:0; padding:0 16px; border-right:1px solid var(--color-border); font:14px/1.7 var(--font-display); color:var(--color-text-secondary); }
.viewpoints-grid blockquote:last-child { border-right:0; }
```

------

## 五、右侧栏：洞察摘要 + 关键主体

### 5.1 洞察摘要

```html
<section class="right-section summary-card">
  <h2 class="panel-title">洞察摘要</h2>
  <div class="summary-item"><i>◴</i><div><b>今日结论</b><p>近7天舆情总量上升后回落，负面占比维持高位，风险指数处于中高水平。</p></div></div>
  <div class="summary-item"><i>♧</i><div><b>异常提醒</b><ul><li>05-25 传播量达到峰值（18,723），较昨日上升 15.33%</li><li>高风险-消极板块占比 41.8%，需重点关注</li></ul></div></div>
  <div class="risk-level"><b>风险等级</b><span>中高</span><p>风险指数：78.6 / 100</p></div>
  <div class="suggestions"><b>建议动作</b><ol><li>加强权威信息发布，及时回应公众关切</li><li>关注重点平台与KOL动向，防范二次发酵</li><li>强化舆论引导，聚焦事实澄清与情绪疏导</li></ol></div>
</section>
```

```css
.right-section { border:1px solid var(--color-border); border-radius:var(--radius-lg); padding:14px; background:rgba(255,255,255,.66); margin-bottom:14px; }
.panel-title { margin:0 0 12px; font:700 20px/1 var(--font-heading); letter-spacing:2px; }
.summary-item { display:grid; grid-template-columns:28px 1fr; gap:8px; padding:10px 0; border-bottom:1px solid var(--color-divider); }
.summary-item i { color:var(--color-gold); font-style:normal; font-size:20px; }
.summary-item b { font-size:14px; }
.summary-item p,.summary-item li { font-size:12px; line-height:1.65; color:var(--color-text-secondary); }
.risk-level span { float:right; transform:rotate(-5deg); border:2px solid var(--color-primary); color:var(--color-primary); padding:6px 12px; font:700 20px/1 var(--font-display); }
.suggestions ol { padding-left:0; counter-reset:item; }
.suggestions li { list-style:none; counter-increment:item; display:flex; gap:8px; margin:7px 0; font-size:12px; }
.suggestions li::before { content:counter(item); width:17px; height:17px; border-radius:50%; background:var(--color-primary); color:#fff; display:inline-flex; align-items:center; justify-content:center; flex:0 0 17px; }
```

### 5.2 关键主体

```html
<section class="right-section kol-card">
  <h2 class="panel-title">关键主体 <span class="help">?</span></h2>
  <div class="kol-list">
    <div class="kol-item"><span class="avatar"></span><b>@观察者网</b><em class="tag tag-media">媒体</em><label>影响力 92</label><progress value="92" max="100"></progress></div>
    <div class="kol-item"><span class="avatar"></span><b>@财经头条</b><em class="tag tag-media">媒体</em><label>影响力 78</label><progress value="78" max="100"></progress></div>
    <div class="kol-item"><span class="avatar"></span><b>@清风明月</b><em class="tag tag-forum">意见领袖</em><label>影响力 65</label><progress value="65" max="100"></progress></div>
    <div class="kol-item"><span class="avatar"></span><b>@城市微视</b><em class="tag tag-positive">自媒体</em><label>影响力 49</label><progress value="49" max="100"></progress></div>
  </div>
</section>
<div class="panel-actions"><button class="btn-primary full-width">导出洞察简报</button><button class="btn-secondary full-width">进入深入研判</button></div>
```

------

## 六、还原验收点

- Header 必须完成 `维舆/Veyrafish` 替换，不残留旧名称。
- 三栏比例接近参考图：左 280px，中间最大，右 350px。
- 中间 KPI、趋势图、底部两栏、观点摘录必须在首屏内基本可见。
- 矩阵右下“高风险-消极”应最突出，气泡最大、淡红背景。
- 右侧“中高”风险章使用红色印章风，并带轻微旋转。
