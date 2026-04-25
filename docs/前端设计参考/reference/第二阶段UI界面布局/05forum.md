# 维舆 · 论坛页（forum）还原规范

> 参考图：`forum.png` · 导航激活项：**论坛** · 最终标题统一为 **维舆-新时代高效通用多维度舆论平台**。

------

## 一、页面目标

论坛页用于分析社区讨论、热帖、阵营分布、情绪温度与争议焦点。页面强调“人群观点”和“讨论场域”。

Footer 口号：`察 众 议 之 所 归 ， 以 辨 舆 场 之 势`。

------

## 二、整体布局

```css
.forum-page .workspace.three-column {
  grid-template-columns: 286px minmax(800px, 1fr) 350px;
  gap: 14px;
  padding: 16px 24px 0;
}
```

------

## 三、左侧栏：论坛维度 + 场域筛选

```html
<aside class="left-panel sidebar forum-sidebar">
  <section class="sidebar-section">
    <h2 class="sidebar-section-title">论坛维度</h2>
    <nav class="sidebar-nav">
      <button class="sidebar-nav-item active"><i>♨</i>热帖榜</button>
      <button class="sidebar-nav-item"><i>♨</i>观点阵营</button>
      <button class="sidebar-nav-item"><i>▣</i>高互动讨论</button>
      <button class="sidebar-nav-item"><i>☼</i>情绪爆点</button>
      <button class="sidebar-nav-item"><i>♙</i>用户画像</button>
      <button class="sidebar-nav-item"><i>▧</i>争议焦点</button>
    </nav>
  </section>
  <section class="sidebar-section filter-card">
    <h2 class="sidebar-section-title">场域筛选</h2>
    <label class="filter-group"><span>时间范围</span><div class="date-picker-row">近7天（2024-05-21 ~ 2024-05-27）</div></label>
    <label class="filter-group"><span>社区平台</span><select><option>全平台（自动汇聚）</option></select></label>
    <label class="filter-group"><span>主题标签</span><select><option>全部</option></select></label>
    <label class="filter-group"><span>情绪倾向</span><select><option>全部</option></select></label>
    <label class="filter-group"><span>互动等级</span><select><option>全部等级</option></select></label>
    <div class="sidebar-footer"><button class="btn-outline">保存视角</button><button class="btn-outline">重置</button></div>
  </section>
</aside>
```

------

## 四、中间主内容区

### 4.1 页面标题栏 + KPI

```html
<div class="content-header"><div class="engine-banner"><h2>论坛引擎 · 察众议之所归</h2><span>行能藏否，或素定怀抱，或得之舆论。</span></div><div class="data-timestamp">数据更新：2024-05-27 21:46:20 <button>↻</button></div></div>
<div class="kpi-bar">
  <article class="kpi-card"><div class="kpi-header"><i>☵</i><span>讨论总量</span></div><strong>128,456</strong><em>较昨日 ▲ 12.35%</em></article>
  <article class="kpi-card"><div class="kpi-header"><i>♨</i><span>高热帖子</span></div><strong>2,356</strong><em>较昨日 ▲ 8.41%</em></article>
  <article class="kpi-card"><div class="kpi-header"><i>⌁</i><span>情绪峰值</span></div><strong>18.72万</strong><em>较昨日 ▲ 15.33%</em></article>
  <article class="kpi-card"><div class="kpi-header"><i>盾</i><span>争议指数</span></div><strong>78.6</strong><em>较昨日 ▲ 6.56%</em></article>
  <article class="kpi-card"><div class="kpi-header"><i>♙</i><span>活跃用户</span></div><strong>56,723</strong><em>较昨日 ▲ 9.28%</em></article>
</div>
```

### 4.2 顶部两列：热帖流 + 观点阵营分布

```css
.forum-top-grid { display:grid; grid-template-columns:.92fr 1.08fr; gap:14px; margin-top:14px; }
.hot-posts-panel,
.camp-panel { padding:14px 16px; }
```

#### 4.2.1 热帖流

```html
<section class="hot-posts-panel panel-card">
  <h3 class="section-title">热帖流</h3>
  <ol class="hot-post-list">
    <li><span>1</span><div><h4><em class="tag tag-media">知乎</em>人工智能是否会取代大量人类岗位？</h4><p>AI技术加速发展，就业岗位在多个行业显现，未来十年哪些职业最可能被替代？</p><footer>▱ 2,568 回复　♡ 1.8万　♧ 6,432 <b>高热</b><b>争议</b></footer></div></li>
    <li><span>2</span><div><h4><em class="tag tag-hot">微博</em>某地教育改革新政引发家长热议</h4><p>新政涉及学区调整与课程改革，家长意见分化明显。</p><footer>▱ 1,985 回复　♡ 1.2万　♧ 3,998 <b>热议</b><b>分歧</b></footer></div></li>
    <li><span>3</span><div><h4><em class="tag tag-media">贴吧</em>新能源车续航虚标问题集中反馈</h4><p>多位车主反映续航里程与官方数据差距较大，厂家回应引争议。</p><footer>▱ 1,742 回复　♡ 9,876　♧ 2,311 <b>争议</b><b>负向</b></footer></div></li>
    <li><span>4</span><div><h4><em class="tag tag-hot">虎扑</em>CBA 总决赛裁判判罚引发球迷讨论</h4><p>关键判罚争议不断，球迷对裁判尺度持不同意见。</p><footer>▱ 1,238 回复　♡ 7,654　♧ 1,982 <b>热议</b><b>争议</b></footer></div></li>
    <li><span>5</span><div><h4><em class="tag tag-positive">豆瓣</em>电影《归途》口碑跨级分化明显</h4><p>剧情与叙事手法引发不同解读，豆瓣评分争议较大。</p><footer>▱ 1,016 回复　♡ 6,343　♧ 1,274 <b>分歧</b><b>负向</b></footer></div></li>
  </ol>
</section>
```

```css
.hot-post-list { list-style:none; padding:0; margin:0; display:flex; flex-direction:column; gap:7px; }
.hot-post-list li { display:grid; grid-template-columns:24px 1fr; gap:10px; padding:8px 10px; border:1px solid var(--color-border); border-radius:8px; background:rgba(255,255,255,.58); }
.hot-post-list li>span { width:20px; height:20px; border-radius:5px; background:var(--color-primary); color:#fff; display:grid; place-items:center; font-size:12px; }
.hot-post-list h4 { margin:0; font-size:14px; }
.hot-post-list p { margin:5px 0; font-size:12px; color:var(--color-text-secondary); line-height:1.45; }
.hot-post-list footer { display:flex; gap:10px; align-items:center; font-size:11px; color:var(--color-text-muted); }
.hot-post-list footer b { margin-left:auto; color:var(--color-primary); border:1px solid #FFCDD2; border-radius:4px; padding:1px 6px; font-weight:400; }
```

#### 4.2.2 观点阵营分布

```html
<section class="camp-panel panel-card">
  <div class="section-header"><h3 class="section-title">观点阵营分布 <span class="help">?</span></h3></div>
  <div class="camp-layout">
    <div class="camp-info support"><b>支持阵营</b><strong>42.1%</strong><span>占比 42.1%（53,987）</span><ul><li>有助于行业升级</li><li>提升效率与创新</li><li>长期利大于弊</li></ul></div>
    <div class="triangle-camp"><div class="up">赞</div><div class="left">反</div><div class="right">中</div></div>
    <div class="camp-info neutral"><b>中立阵营</b><strong>23.4%</strong><span>占比 23.4%（30,012）</span><ul><li>需更多观察数据</li><li>视具体场景而定</li><li>保持审慎态度</li></ul></div>
    <div class="camp-info oppose"><b>反对阵营</b><strong>34.5%</strong><span>占比 34.5%（44,457）</span><ul><li>或加剧社会不平等</li><li>加剧隐私安全风险</li><li>存在伦理隐患</li></ul></div>
  </div>
</section>
```

```css
.camp-layout { display:grid; grid-template-columns:1fr 210px 1fr; grid-template-rows:auto auto; gap:10px 18px; align-items:center; }
.triangle-camp { grid-row:span 2; width:210px; height:190px; position:relative; margin:auto; }
.triangle-camp div { position:absolute; display:grid; place-items:center; color:#fff; font-size:28px; font-weight:700; }
.triangle-camp .up { left:65px; top:0; width:84px; height:86px; background:#43A87A; clip-path:polygon(50% 0,100% 100%,0 100%); }
.triangle-camp .left { left:20px; bottom:10px; width:84px; height:86px; background:#D9534F; clip-path:polygon(0 0,100% 0,50% 100%); }
.triangle-camp .right { right:20px; bottom:10px; width:84px; height:86px; background:#8A8A8A; clip-path:polygon(0 0,100% 0,50% 100%); }
.camp-info strong { display:block; font:700 27px/1 var(--font-mono); margin:6px 0; }
.camp-info li { font-size:12px; line-height:1.7; }
```

### 4.3 讨论演进折线图

```html
<section class="discussion-chart panel-card">
  <div class="section-header"><h3 class="section-title">讨论演进 <span class="help">?</span></h3></div>
  <div id="discussion-trend" class="line-chart"></div>
</section>
```

```js
const discussionTrend = {
  legend: { data:['讨论量（条）','情绪峰值（条）'] },
  xAxis: { data:['05-21','05-22','05-23','05-24','05-25','05-26','05-27'] },
  yAxis: [{ max:20000 }, { max:240000 }],
  series: [
    { name:'讨论量（条）', type:'line', data:[5600,11800,10500,13200,18500,14000,6200], color:'#1A1A1A' },
    { name:'情绪峰值（条）', type:'line', yAxisIndex:1, data:[48000,92000,80000,120000,178000,105000,52000], color:'#E53935' }
  ]
}
```

### 4.4 底部：高频热辞 + 争议焦点

```css
.forum-bottom-grid { display:grid; grid-template-columns:.9fr 1.1fr; gap:14px; margin-top:14px; }
```

```html
<section class="hotwords-panel panel-card"><h3 class="section-title">高频热辞 <span class="help">?</span></h3><div class="word-cloud"><span style="--s:22px">人工智能 · 12.6万</span><span>就业 9.8万</span><span>改革 8.2万</span><span>教育 7.1万</span><span>政策 6.7万</span><span>服务 5.6万</span><span>经济 5.1万</span><span>创新 4.8万</span><span>监管 4.3万</span><span>公平 3.9万</span><button>更多⌄</button></div></section>
<section class="dispute-panel panel-card"><h3 class="section-title">争议焦点</h3><ul><li>加速冲击就业：AI 自动化是否将导致大规模失业问题？</li><li>关注高龄学员培训能力，部分地区新政是否存在执行不均？</li><li>续航真实性与透明度：部分企业/机构数据披露能否服众？</li><li>热搜相关大V爆料：企业、用户与监管之间如何平衡利益？</li><li>伦理与社会影响：技术发展是否带来新的伦理与社会风险？</li></ul></section>
```

```css
.word-cloud { display:flex; flex-wrap:wrap; gap:9px; }
.word-cloud span,.word-cloud button { padding:6px 12px; border:1px solid var(--color-border); border-radius:6px; background:rgba(255,255,255,.62); font-size:var(--s, 13px); }
.dispute-panel li { margin:8px 0; font-size:13px; line-height:1.55; }
.dispute-panel li::marker { color:var(--color-primary); }
```

------

## 五、右侧栏：论坛研判 + 核心用户

```html
<section class="right-section forum-judge">
  <h2 class="panel-title">论坛研判</h2>
  <div class="temperature"><b>当前场域温度</b><strong>78.6 <small>/100</small></strong><em>高温区间</em><span>较昨日 ▲ 6.4</span></div>
  <div class="judge-item"><b>争议中心</b><p>人工智能与就业影响、教育改革、数据真实性等话题争议最为集中。</p></div>
  <div class="emotion-bars"><b>用户情绪</b><label>积极 <progress value="42.3" max="100"></progress>42.3%</label><label>中性 <progress value="26.8" max="100"></progress>26.8%</label><label>消极 <progress value="30.9" max="100"></progress>30.9%</label></div>
  <div class="potential-hot"><b>潜在爆点</b><p>新能源车维权 <em>高热</em></p><p>教育改革细则落地 <em>升温</em></p><p>AI 伦理与法规争议 <em>渐温</em></p></div>
  <div class="suggestions"><b>干预建议</b><ol><li>加强政策解释与科普，缓解信息不对称</li><li>关注高热争议话题，及时回应关切</li><li>引导理性讨论，避免情绪化对立升级</li><li>持续监测潜在爆点，提前研判风险</li></ol></div>
</section>
<section class="right-section core-users"><h2 class="panel-title">核心用户 <span class="help">?</span></h2><ol><li>知乎舍一 <em>知乎大V</em><progress value="92" max="100"></progress><span>影响力 92</span></li><li>财经观察员 <em>微博大V</em><progress value="88" max="100"></progress><span>影响力 88</span></li><li>理性思辨者 <em>贴吧活跃用户</em><progress value="76" max="100"></progress><span>影响力 76</span></li><li>数据洞察社 <em>豆瓣小组长</em><progress value="72" max="100"></progress><span>影响力 72</span></li></ol></section>
<div class="panel-actions"><button class="btn-primary full-width">导出论坛简报</button><button class="btn-secondary full-width">进入场域研判</button></div>
```

```css
.temperature strong { display:block; margin:6px 0; color:var(--color-primary); font:700 26px/1 var(--font-mono); }
.temperature em { float:right; border:1px solid var(--color-primary); color:var(--color-primary); border-radius:4px; padding:4px 8px; font-style:normal; }
.emotion-bars label { display:grid; grid-template-columns:38px 1fr 42px; gap:8px; align-items:center; margin:8px 0; font-size:12px; }
.potential-hot p { display:flex; justify-content:space-between; font-size:13px; }
.potential-hot em { font-style:normal; color:var(--color-primary); border:1px solid #FFCDD2; border-radius:4px; padding:1px 6px; }
.core-users ol { list-style:none; padding:0; }
.core-users li { display:grid; grid-template-columns:1fr auto; gap:6px; align-items:center; margin:10px 0; font-size:12px; }
.core-users progress { grid-column:1/3; width:100%; height:5px; }
```

------

## 六、还原验收点

- 观点阵营三角图是论坛页核心视觉，不应被简化成普通饼图。
- 热帖流需保留排名、平台标签、标题、摘要、互动数据、状态标签。
- 右侧“当前场域温度 78.6/100”必须红色醒目，旁边有“高温区间”标签。
- 高频热辞使用可换行标签云，不要做成纯表格。
