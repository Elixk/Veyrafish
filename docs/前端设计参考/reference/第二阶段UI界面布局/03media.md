# 维舆 · 媒析页（media）还原规范

> 参考图：`media.png` · 导航激活项：**媒析** · 最终标题统一为 **维舆-新时代高效通用多维度舆论平台**。

------

## 一、页面目标

媒析页用于展示媒体传播诊断：传播源、转载路径、媒体声量、立场分布、地域热度与重点媒体原文。页面整体是三栏：左侧筛选，中间传播分析，右侧传播诊断。

Footer 口号：`观 澜 辨 势 ， 以 媒 明 势`。

------

## 二、整体布局

```css
.media-page .workspace.three-column {
  grid-template-columns: 260px minmax(820px, 1fr) 340px;
  gap: 14px;
  padding: 16px 24px 0;
}
.media-page .main-panel { padding: 16px; }
```

------

## 三、左侧栏：媒析维度 + 筛选条件

### 3.1 媒析维度

```html
<section class="sidebar-section">
  <h2 class="sidebar-section-title">媒析维度</h2>
  <nav class="sidebar-nav">
    <button class="sidebar-nav-item active"><i>▥</i>传播概览</button>
    <button class="sidebar-nav-item"><i>◎</i>媒体分布</button>
    <button class="sidebar-nav-item"><i>⌘</i>传播路径</button>
    <button class="sidebar-nav-item"><i>盾</i>媒体立场</button>
    <button class="sidebar-nav-item"><i>▤</i>重点报道</button>
    <button class="sidebar-nav-item"><i>⌖</i>区域来源</button>
  </nav>
</section>
```

### 3.2 筛选条件

```html
<section class="sidebar-section filter-card">
  <h2 class="sidebar-section-title">筛选条件</h2>
  <label class="filter-group"><span>时间范围</span><div class="date-picker-row">2024-05-20 ~ 2024-05-27</div></label>
  <label class="filter-group"><span>媒体类型</span><select><option>全部（含传统与新媒体）</option></select></label>
  <label class="filter-group"><span>平台来源</span><select><option>全部（含网站+客户端+新媒体）</option></select></label>
  <label class="filter-group"><span>地域</span><select><option>全国</option></select></label>
  <label class="filter-group"><span>影响等级</span><select><option>全部等级</option></select></label>
  <div class="sidebar-footer"><button class="btn-outline">保存视角</button><button class="btn-outline">重置</button></div>
</section>
```

------

## 四、中间主内容区

### 4.1 页面标题栏

```html
<div class="content-header">
  <div class="engine-banner">
    <h2>媒析引擎 · 观澜辨势</h2>
    <span>众声并起，其源可辨；百端纷陈，其势可辨。</span>
  </div>
  <div class="data-timestamp">数据更新：2024-05-27 21:46:20 <button>↻</button></div>
</div>
```

### 4.2 KPI 行

五项指标：媒体声量、转载量、首发媒体数、高影响报道、扩散速度。

```html
<div class="kpi-bar">
  <article class="kpi-card"><div class="kpi-header"><i>◴</i><span>媒体声量</span></div><strong>128,456</strong><em>较昨日 ▲ 12.35%</em></article>
  <article class="kpi-card"><div class="kpi-header"><i>↻</i><span>转载量</span></div><strong>260,782</strong><em>较昨日 ▲ 18.92%</em></article>
  <article class="kpi-card"><div class="kpi-header"><i>叶</i><span>首发媒体数</span></div><strong>786</strong><em>较昨日 ▲ 8.41%</em></article>
  <article class="kpi-card"><div class="kpi-header"><i>♨</i><span>高影响报道</span></div><strong>1,256</strong><em>较昨日 ▲ 14.21%</em></article>
  <article class="kpi-card"><div class="kpi-header"><i>◷</i><span>扩散速度</span></div><strong>1.83x</strong><em>较昨日 ▲ 16.75%</em></article>
</div>
```

### 4.3 上方两列：传播路径图 + 媒体声量排行

```css
.media-top-grid { display:grid; grid-template-columns: 1.08fr .92fr; gap:14px; margin-top:14px; }
.path-panel,
.rank-panel { padding:14px 16px; }
```

#### 4.3.1 媒体传播路径图

参考图是“首发源 → 媒体节点 → 平台节点”的关系路径，左侧为人民日报，右侧为微信、微博、今日头条、抖音、百度资讯等。

```html
<section class="path-panel panel-card">
  <div class="section-header"><h3 class="section-title">媒体传播路径图 <span class="help">i</span></h3><div class="legend">— 首发源　— 放大节点　→ 传播方向</div></div>
  <div class="media-flow">
    <div class="source-node">人民日报<br/><small>05-24 09:18<br/>首发</small></div>
    <div class="middle-nodes">
      <div>新华社<br/><small>放大 05-24 10:37</small></div>
      <div>央视新闻<br/><small>放大 05-24 11:05</small></div>
      <div>澎湃新闻<br/><small>放大 05-24 11:42</small></div>
      <div>观察者网<br/><small>放大 05-24 12:18</small></div>
    </div>
    <div class="platform-nodes">
      <div>微信 <b>48,732</b></div><div>微博 <b>36,815</b></div><div>今日头条 <b>28,906</b></div><div>抖音 <b>21,470</b></div><div>百度资讯 <b>18,329</b></div>
    </div>
  </div>
</section>
```

```css
.media-flow { height:200px; display:grid; grid-template-columns:150px 1fr 150px; align-items:center; gap:22px; position:relative; }
.source-node { width:74px; height:74px; border:2px solid var(--color-primary); border-radius:50%; display:grid; place-items:center; text-align:center; color:var(--color-primary); font-weight:700; }
.middle-nodes,.platform-nodes { display:flex; flex-direction:column; gap:10px; }
.middle-nodes div,.platform-nodes div { min-height:32px; border:1px solid var(--color-border); border-radius:999px; background:rgba(255,255,255,.65); padding:6px 12px; font-size:12px; }
.platform-nodes b { float:right; color:var(--color-text-secondary); }
```

> SVG 实现建议：用 `<svg class="flow-lines">` 画贝塞尔曲线，线条灰色；关键首发路径使用红/橙色实线，二次扩散使用灰色虚线。

#### 4.3.2 媒体声量排行

```html
<section class="rank-panel panel-card">
  <div class="section-header"><h3 class="section-title">媒体声量排行 <span class="help">i</span></h3><span>单位：声量</span></div>
  <ol class="media-rank-list">
    <li><b>人民日报</b><span style="--w:100%">18,723</span></li>
    <li><b>新华社</b><span style="--w:87%">16,285</span></li>
    <li><b>央视新闻</b><span style="--w:73%">13,642</span></li>
    <li><b>澎湃新闻</b><span style="--w:53%">9,876</span></li>
    <li><b>观察者网</b><span style="--w:42%">7,845</span></li>
    <li><b>光明日报</b><span style="--w:35%">6,498</span></li>
  </ol>
</section>
```

```css
.media-rank-list { list-style:none; padding:0; margin:0; display:flex; flex-direction:column; gap:13px; }
.media-rank-list li { display:grid; grid-template-columns:110px 1fr 54px; align-items:center; gap:8px; counter-increment:rank; }
.media-rank-list li::before { content:counter(rank); width:18px; height:18px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center; background:#E53935; color:#fff; font-size:11px; }
.media-rank-list b { font-size:14px; }
.media-rank-list span { position:relative; text-align:right; font:13px/1 var(--font-mono); }
.media-rank-list span::before { content:''; position:absolute; left:0; right:58px; top:50%; height:7px; border-radius:999px; transform:translateY(-50%); background:linear-gradient(90deg,var(--color-primary) var(--w), var(--color-divider) var(--w)); }
```

### 4.4 中部两列：媒体立场分布 + 传播地域热度

```css
.media-middle-grid { display:grid; grid-template-columns: .95fr 1.05fr; gap:14px; margin-top:14px; }
```

#### 4.4.1 媒体立场分布

```html
<section class="stance-panel panel-card">
  <div class="section-header"><h3 class="section-title">媒体立场分布 <span class="help">i</span></h3></div>
  <div class="stance-content">
    <div class="stance-stat positive"><b>正面</b><strong>45.3%</strong><span>58,191</span></div>
    <div class="donut-chart">媒体总数<br/><b>2,145</b></div>
    <div class="stance-stat"><b>中性</b><strong>40.1%</strong><span>51,279</span></div>
    <div class="stance-stat negative"><b>负面</b><strong>14.6%</strong><span>18,986</span></div>
  </div>
</section>
```

```css
.stance-content { display:grid; grid-template-columns:1fr 180px 1fr; align-items:center; gap:18px; min-height:170px; }
.donut-chart { width:150px; height:150px; border-radius:50%; margin:auto; display:grid; place-items:center; text-align:center; background:conic-gradient(#4CAF50 0 45.3%, #9E9E9E 45.3% 85.4%, #E53935 85.4% 100%); position:relative; }
.donut-chart::after { content:''; position:absolute; inset:28px; border-radius:50%; background:#fff; }
.donut-chart * { position:relative; z-index:1; }
.stance-stat strong { display:block; font:700 22px/1.3 var(--font-mono); }
```

#### 4.4.2 传播地域热度

```html
<section class="region-panel panel-card">
  <div class="section-header"><h3 class="section-title">传播地域热度</h3><span>单位：声量</span></div>
  <div class="region-layout">
    <div class="china-map-placeholder">中国地图热力图</div>
    <table class="region-table"><tr><th>排名</th><th>地区</th><th>声量</th><th>占比</th></tr><tr><td>1</td><td>广东省</td><td>15,823</td><td>12.32%</td></tr><tr><td>2</td><td>北京市</td><td>12,456</td><td>9.69%</td></tr><tr><td>3</td><td>江苏省</td><td>10,782</td><td>8.40%</td></tr><tr><td>4</td><td>浙江省</td><td>9,314</td><td>7.25%</td></tr><tr><td>5</td><td>山东省</td><td>8,721</td><td>6.79%</td></tr></table>
  </div>
</section>
```

### 4.5 底部：重点媒体原文摘录

```html
<section class="article-excerpts panel-card">
  <div class="section-header"><h3 class="section-title">重点媒体原文摘录 <span class="help">i</span></h3><button class="round-next">〉</button></div>
  <div class="article-grid">
    <article><header><b>人民日报</b><em class="tag tag-hot">首发</em><time>05-24 09:18</time></header><h4>推动高质量发展，稳中求进的未来</h4><p>文章指出，要坚持以新发展理念为引领，牢牢把握高质量发展这一首要任务……</p><footer>传播量：18,723 <a>查看原文 〉</a></footer></article>
    <article><header><b>新华社</b><em class="tag tag-high">放大</em><time>05-24 10:37</time></header><h4>各地多措并举促进经济稳步回升</h4><p>报道从政策、产业、消费等多维度解析各地稳增长的务实举措与成效……</p><footer>传播量：16,285 <a>查看原文 〉</a></footer></article>
    <article><header><b>澎湃新闻</b><em class="tag tag-high">放大</em><time>05-24 11:42</time></header><h4>专家：政策协同发力是关键支撑</h4><p>多位专家认为，当前政策组合与时机增长形成有力支撑，后续需持续发力……</p><footer>传播量：9,876 <a>查看原文 〉</a></footer></article>
  </div>
</section>
```

```css
.article-excerpts { margin-top:14px; padding:14px 16px; }
.article-grid { display:grid; grid-template-columns:repeat(3, 1fr); gap:14px; }
.article-grid article { border:1px solid var(--color-border); border-radius:8px; padding:12px; background:rgba(255,255,255,.58); }
.article-grid header { display:flex; align-items:center; gap:8px; }
.article-grid time { margin-left:auto; font-size:11px; color:var(--color-text-muted); }
.article-grid h4 { margin:10px 0 6px; font-size:14px; }
.article-grid p { margin:0; font-size:12px; line-height:1.6; color:var(--color-text-secondary); }
.article-grid footer { display:flex; justify-content:space-between; margin-top:10px; font-size:12px; }
```

------

## 五、右侧栏：传播诊断 + 重点媒体

```html
<section class="right-section diagnose-card">
  <h2 class="panel-title">传播诊断 <span class="help">i</span></h2>
  <dl class="diagnose-list">
    <dt>首发源</dt><dd>人民日报 · 05-24 09:18 首发</dd>
    <dt>扩散高峰</dt><dd>05-25 14:00 ~ 16:00（声量峰值 18,723）</dd>
    <dt>媒体倾向</dt><dd>正面 45.3% · 中性 40.1% · 负面 14.6%</dd>
    <dt>关键放大节点</dt><dd>新华社、央视新闻、澎湃新闻、观察者网</dd>
  </dl>
  <div class="suggestions"><b>传播建议</b><ol><li>关注头部意见领袖的后续观点动向</li><li>加强正面权威信息的持续输出与扩散</li><li>引导重点平台社区讨论，防范负面放大</li></ol></div>
</section>
<section class="right-section key-media-card">
  <h2 class="panel-title">重点媒体 <small>单位：影响力</small></h2>
  <ol class="key-media-list"><li>人民日报 <em>央媒</em><progress value="96" max="100"></progress><span>96/100</span></li><li>新华社 <em>央媒</em><progress value="92" max="100"></progress><span>92/100</span></li><li>央视新闻 <em>央媒</em><progress value="89" max="100"></progress><span>89/100</span></li><li>澎湃新闻 <em>媒体</em><progress value="78" max="100"></progress><span>78/100</span></li></ol>
</section>
<div class="panel-actions"><button class="btn-primary full-width">导出媒析简报</button><button class="btn-secondary full-width">进入传播研判</button></div>
```

------

## 六、还原验收点

- 中间首屏必须可见：KPI、传播路径图、媒体声量排行、立场环图、地域热度、原文摘录。
- 传播路径图要有明显的“左源头 → 中媒体 → 右平台”层次，曲线不宜太粗。
- 地图可先用占位图，但要保留热力颜色、右下角低高图例和右侧排行表。
- 右侧传播诊断分组要有图标和分割线，底部两个按钮固定全宽。
