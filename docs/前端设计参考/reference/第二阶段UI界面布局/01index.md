# 维舆 · 总览页（index）还原规范

> 参考图：`index.png` · 导航激活项：**总览** · 最终标题统一为 **维舆-新时代高效通用多维度舆论平台**。

------

## 一、页面目标

总览页是 Veyrafish 的入口页，重点是“一屏完成输入、配置、概览、进入引擎”。参考图旧文案需要全部替换为新品牌：

- Header 左侧：`维舆` + `Veyrafish · 以微知著，以舆定策`
- Header 中心：`维舆-新时代高效通用多维度舆论平台`
- Logo：红色印章，两行 `维 / 舆`
- Footer：`以 微 知 著 · 以 舆 定 策`

页面由三块组成：

1. **上半左侧**：舆情输入与配置区
2. **上半右侧**：舆情洞察概览区
3. **底部整行**：五大核心引擎模块入口

------

## 二、布局结构

```text
┌──────────────────────────────────────────────────────────────┐
│ HEADER：Logo + 新标题 + 导航，总览 active                     │
├─────────────────────────────┬────────────────────────────────┤
│ 舆情输入与配置               │ 舆情洞察概览                    │
│ width: 43%~45%              │ width: 55%~57%                 │
├─────────────────────────────┴────────────────────────────────┤
│ 核心引擎模块：5 列卡片                                         │
├──────────────────────────────────────────────────────────────┤
│ FOOTER：水墨山水 + 口号 + 印章 + 小船                          │
└──────────────────────────────────────────────────────────────┘
```

```css
.index-page .workspace.overview {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px 24px 0;
}
.index-page .top-panels {
  display: grid;
  grid-template-columns: minmax(480px, .9fr) minmax(620px, 1.15fr);
  gap: 16px;
}
.index-page .panel-card {
  min-height: 450px;
  padding: 20px 26px;
  background: rgba(255,255,255,.86);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
}
```

------

## 三、左侧：舆情输入与配置

### 3.1 标题栏

左侧标题为 `舆情输入与配置`，后接水墨云纹小图标；标题下方左侧有红色短线。

```html
<div class="section-header input-header">
  <h2 class="section-title">舆情输入与配置</h2>
  <div class="header-actions">
    <button class="btn-outline">◎ LLM配置</button>
    <button class="btn-primary">开始分析</button>
    <button class="btn-outline">上传模板</button>
  </div>
</div>
```

```css
.input-header { align-items: flex-start; }
.header-actions { display: flex; align-items: center; gap: 14px; }
.input-header .btn-primary { min-width: 112px; font-weight: 700; }
.input-header .btn-outline { min-width: 112px; background: rgba(255,255,255,.55); }
```

### 3.2 输入区

```html
<div class="input-panel">
  <div class="input-label-row">
    <label>请输入要分析的内容</label>
    <span class="char-count">0 / 5000</span>
    <button class="edit-icon">⌁</button>
  </div>
  <textarea
    class="content-textarea"
    placeholder="请输入要分析的文本、事件、话题或链接等内容。\A可粘贴新闻报道、社交媒体内容、用户评论、论坛帖子等，\A平台将为您提供多维度的舆情洞察与研判。"
  ></textarea>
</div>
```

```css
.input-label-row { display: grid; grid-template-columns: 1fr auto auto; gap: 12px; align-items: center; margin-bottom: 10px; }
.input-label-row label { font: 600 14px/1 var(--font-heading); letter-spacing: 1px; }
.char-count { font-size: 12px; color: var(--color-text-primary); }
.content-textarea {
  width: 100%;
  height: 138px;
  resize: none;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-lg);
  background: rgba(255,255,255,.55);
  padding: 18px 20px;
  font-size: 13px;
  line-height: 1.8;
  color: var(--color-text-secondary);
  white-space: pre-line;
  background-image: url('/assets/decor/ink-mountain-input.svg');
  background-repeat: no-repeat;
  background-position: right bottom;
  background-size: 240px auto;
}
```

### 3.3 分析配置

```html
<section class="analysis-config">
  <h3 class="sub-title">分析配置</h3>
  <div class="config-grid">
    <label class="config-item"><span>模型选择</span><select><option>舆析智脑-Large（推荐）</option></select></label>
    <label class="config-item"><span>分析深度</span><select><option>深度研判（全面深入）</option></select></label>
    <label class="config-item"><span>时间范围</span><div class="date-range">2024-05-20 <b>~</b> 2024-05-27</div></label>
    <label class="config-item"><span>数据来源范围</span><select><option>全网（新闻 + 社媒 + 论坛）</option></select></label>
  </div>
  <div class="other-options">
    <span>其他选项</span>
    <label><input type="checkbox" checked /> 情感分析</label>
    <label><input type="checkbox" checked /> 热点趋势</label>
    <label><input type="checkbox" /> 趋势预测</label>
    <label><input type="checkbox" /> 关联事件挖掘</label>
  </div>
</section>
```

```css
.sub-title { margin: 20px 0 12px; font: 700 15px/1 var(--font-heading); letter-spacing: 2px; }
.sub-title::after { content:''; display:block; width:18px; height:2px; background:var(--color-primary); margin-top:8px; }
.config-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px 28px; }
.config-item { display: grid; grid-template-columns: 78px minmax(0,1fr); align-items: center; gap: 8px; font-size: 13px; }
.config-item span { color: var(--color-text-primary); font-weight: 600; }
.config-item select,
.date-range {
  height: 34px;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: rgba(255,255,255,.65);
  padding: 0 12px;
  font-size: 13px;
}
.date-range { display:flex; align-items:center; justify-content:space-between; }
.other-options { display: flex; align-items: center; gap: 26px; margin-top: 22px; font-size: 14px; }
.other-options > span { font-weight: 700; }
.other-options label { display: inline-flex; align-items: center; gap: 8px; }
input[type="checkbox"] { width: 18px; height: 18px; accent-color: var(--color-primary); }
```

### 3.4 引言印章区

```html
<div class="quote-seal-area">
  <div class="seal-icon">维舆</div>
  <blockquote>“察微知著，观澜辨势，观其势，析其源，得其理。”</blockquote>
</div>
```

```css
.quote-seal-area { display:flex; align-items:center; gap:18px; margin-top:28px; }
.seal-icon {
  width: 34px; height: 34px;
  border: 2px solid var(--color-primary);
  color: var(--color-primary);
  display: grid; place-items: center;
  font: 700 12px/1.1 var(--font-display);
  transform: rotate(-2deg);
}
.quote-seal-area blockquote {
  margin: 0;
  font: 16px/1.8 var(--font-display);
  color: var(--color-text-secondary);
  letter-spacing: 2px;
}
```

------

## 四、右侧：舆情洞察概览

### 4.1 标题与时间戳

```html
<div class="section-header">
  <h2 class="section-title">舆情洞察概览</h2>
  <div class="data-timestamp">数据更新：2024-05-27 21:46:20 <button>↻</button></div>
</div>
```

### 4.2 左侧纵向维度导航 + 右侧图表面板

```html
<div class="overview-insight-layout">
  <nav class="insight-nav">
    <button class="active">⌁ 总体态势</button>
    <button>♡ 情感分布</button>
    <button>◷ 热点话题</button>
    <button>⌁ 趋势走向</button>
    <button>⌘ 传播来源</button>
    <button>▣ 核心观点</button>
  </nav>
  <section class="overview-chart-card">...</section>
</div>
```

```css
.overview-insight-layout {
  display: grid;
  grid-template-columns: 130px minmax(0,1fr);
  gap: 14px;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-lg);
  padding: 18px 18px 0 10px;
}
.insight-nav { display:flex; flex-direction:column; gap:10px; padding-top: 4px; }
.insight-nav button {
  height: 42px;
  text-align: left;
  padding: 0 12px;
  border: 0;
  border-radius: var(--radius-md);
  background: transparent;
  color: var(--color-text-secondary);
  font-size: 14px;
}
.insight-nav button.active {
  background: #FFF0F0;
  color: var(--color-primary);
  box-shadow: inset 3px 0 0 var(--color-primary);
  font-weight: 700;
}
```

### 4.3 KPI 指标

```html
<div class="kpi-row compact">
  <div class="kpi-item"><span>舆情总量</span><strong>128,456</strong><em>较昨日 ▲ 12.35%</em></div>
  <div class="kpi-item"><span>正面占比</span><strong>32.6%</strong><em>较昨日 ▲ 2.18%</em></div>
  <div class="kpi-item"><span>负面占比</span><strong>41.8%</strong><em>较昨日 ▼ 1.62%</em></div>
  <div class="kpi-item"><span>中性占比</span><strong>25.6%</strong><em>较昨日 ▼ 0.56%</em></div>
  <div class="kpi-item"><span>影响力指数</span><strong>78.6</strong><em>较昨日 ▲ 5.23</em></div>
</div>
```

```css
.kpi-row.compact { display:grid; grid-template-columns: repeat(5, 1fr); border:1px solid var(--color-divider); border-radius:10px; overflow:hidden; }
.kpi-item { text-align:center; padding:12px 8px; border-right:1px dashed var(--color-border-strong); }
.kpi-item:last-child { border-right:0; }
.kpi-item span { display:block; font-size:12px; color:var(--color-text-secondary); }
.kpi-item strong { display:block; margin:6px 0; font:700 23px/1 var(--font-mono); }
.kpi-item em { font-style:normal; font-size:10px; color:var(--color-negative); }
```

### 4.4 趋势图

图表区域高度 `170~190px`，右下叠加淡山水。Tooltip 固定示例点为 `05-25`：

```js
const trendOption = {
  grid: { left: 42, right: 18, top: 38, bottom: 26 },
  legend: { top: 0, right: 180, itemWidth: 22, itemHeight: 2 },
  tooltip: { trigger: 'axis', backgroundColor: '#fff', borderColor: '#E8DDD0' },
  xAxis: { type: 'category', data: ['05-21','05-22','05-23','05-24','05-25','05-26','05-27'] },
  yAxis: { type: 'value', max: 20000, axisLabel: { formatter: v => v === 0 ? '0' : v/1000 + 'K' } },
  series: [
    { name:'总量', type:'line', data:[9560,14580,12600,16120,18723,11240,10580], color:'#1A1A1A' },
    { name:'正面', type:'line', data:[5100,5600,4180,6800,7600,5020,4800], color:'#4CAF50' },
    { name:'负面', type:'line', data:[6900,8200,6100,9600,13100,6250,5800], color:'#E53935' },
    { name:'中性', type:'line', data:[3300,3100,1800,3400,4776,2900,2850], color:'#9E9E9E' }
  ]
}
```

### 4.5 操作按钮与引言

```html
<div class="action-row two-buttons">
  <button class="btn-primary full-width">▧ 导出报告</button>
  <button class="btn-secondary full-width">深入研判 〉</button>
</div>
<blockquote class="platform-quote">“察微知著，观澜辨势，行能藏否，成事定所施，成得之舆论。<br/>观其势，析其源，得其理，以微知著，以舆定策。”</blockquote>
```

```css
.two-buttons { display:grid; grid-template-columns:1fr 1fr; gap:14px; margin-top:18px; }
.platform-quote {
  margin: 12px 0 0;
  padding: 12px 20px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  background: rgba(255,255,255,.55) url('/assets/decor/ink-boat-line.svg') right bottom/210px auto no-repeat;
  font: 15px/1.8 var(--font-display);
  letter-spacing: 2px;
}
```

------

## 五、底部核心引擎模块

```html
<section class="engine-modules">
  <h3 class="modules-title">核心引擎模块</h3>
  <div class="engines-grid">
    <article class="engine-card"><span class="status red"></span><img src="/assets/icons/engine-insight.svg"><b>Insight Engine</b><em>洞察引擎</em><p>多维度舆情态势感知，洞见风险信号，深度挖掘趋势。</p><button>进入 〉</button></article>
    <article class="engine-card"><span class="status red"></span><img src="/assets/icons/engine-media.svg"><b>Media Engine</b><em>媒析引擎</em><p>全媒体监测与解析，追踪传播路径，评估媒体影响。</p><button>进入 〉</button></article>
    <article class="engine-card"><span class="status red"></span><img src="/assets/icons/engine-query.svg"><b>Query Engine</b><em>检索引擎</em><p>精准检索全量资源，支持高级查询，快速定位信息。</p><button>进入 〉</button></article>
    <article class="engine-card"><span class="status green"></span><img src="/assets/icons/engine-forum.svg"><b>Forum Engine</b><em>论坛引擎</em><p>洞察论坛热帖，捕捉用户观点，挖掘社群动向。</p><button>进入 〉</button></article>
    <article class="engine-card"><span class="status gray"></span><img src="/assets/icons/engine-report.svg"><b>Report Engine</b><em>报告引擎</em><p>自动生成多维报告，支持导出分享，助力科学决策。</p><button>进入 〉</button></article>
  </div>
</section>
```

```css
.engines-grid { display:grid; grid-template-columns: repeat(5, 1fr); gap:14px; }
.engine-card {
  position: relative;
  min-height: 140px;
  padding: 18px 18px 14px 108px;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-lg);
  background: rgba(255,255,255,.62);
}
.engine-card img { position:absolute; left:22px; top:30px; width:68px; height:68px; object-fit:contain; }
.engine-card b { display:block; font:700 17px/1.1 var(--font-en); }
.engine-card em { display:block; margin:5px 0 6px; font-style:normal; font-size:14px; color:var(--color-text-primary); }
.engine-card p { margin:0; min-height:38px; font-size:12px; line-height:1.6; color:var(--color-text-secondary); }
.engine-card button { margin-top:8px; min-width:92px; height:28px; border:1px solid var(--color-border-strong); border-radius:5px; background:rgba(255,255,255,.62); }
.status { position:absolute; right:16px; top:16px; width:8px; height:8px; border-radius:50%; }
.status.red { background:var(--color-negative); } .status.green { background:#43A047; } .status.gray { background:#9E9E9E; }
```

------

## 六、还原验收点

- Header 新标题必须替换为 `维舆-新时代高效通用多维度舆论平台`，页面内不得残留旧品牌文案。
- 顶部两卡片高度基本一致；右侧图表区不可压扁。
- 总览页没有左侧筛选栏；只有上下分区。
- 五个引擎卡图标必须为水墨黑白风，位置左大右文。
- Footer 山水不能遮挡卡片内容，透明度控制在 `0.12~0.2`。

