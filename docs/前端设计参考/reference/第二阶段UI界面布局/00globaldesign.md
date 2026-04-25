# 维舆 · Veyrafish · 全局设计系统规范

> 适用范围：总览、洞察、媒析、检索、论坛、报告六个页面。参考图仍保留旧标题样式，但最终实现统一替换为：**维舆-新时代高效通用多维度舆论平台**。

------

## 0. 品牌统一替换规则

本阶段所有页面必须先完成品牌替换，再进入布局还原。

| 项目 | 新规范 |
|---|---|
| 中文名 | **维舆** |
| 英文名 | **Veyrafish** |
| Header 主标题 | **维舆-新时代高效通用多维度舆论平台** |
| Logo 红印文字 | 建议使用两行：`维` / `舆`；若空间不足可用单字 `维` |
| Header 左侧品牌名 | `维舆` |
| Header 英文辅助名 | `Veyrafish`，可小字置于中文名下方或右侧 |
| 旧文案替换 | 所有旧品牌文案均替换为 `维舆 / Veyrafish / 维舆-新时代高效通用多维度舆论平台` |

> 注意：本文件按用户本次给定原文保留“**高效通用**”四字，不擅自替换为“高效通用”。若后续确认应为“高效”，只需改 `--brand-title` 或常量即可全局替换。

------

## 一、品牌定位与视觉基调

- **平台名称**：维舆（Veyrafish）
- **平台标题**：维舆-新时代高效通用多维度舆论平台
- **核心定位**：面向高效场景的通用、多维度、可视化舆论分析平台
- **副标题 / 小标语**：以微知著 · 以舆定策
- **风格主题**：新中式水墨 + 现代数据可视化 + 卡片化工作台
- **气质关键词**：沉稳、权威、古典、精准、克制、数据化
- **视觉关键词**：米白宣纸、朱砂印章、金棕边线、水墨山水、细线图表、低饱和按钮

------

## 二、全局 CSS 变量

```css
:root {
  /* 品牌 */
  --brand-cn: '维舆';
  --brand-en: 'Veyrafish';
  --brand-title: '维舆-新时代高效通用多维度舆论平台';
  --brand-motto: '以微知著 · 以舆定策';

  /* 主色调 */
  --color-primary:        #8B1A1A;   /* 朱砂深红：主按钮、激活态、Logo红印 */
  --color-primary-light:  #C0392B;   /* 悬停红 */
  --color-primary-dark:   #5C0F0F;   /* 按下红 */

  /* 辅助色 */
  --color-gold:           #B8956A;   /* 金棕：次按钮、描边、图标 */
  --color-gold-light:     #D4AA7D;
  --color-gold-bg:        #F5EDD8;   /* 米金背景 */
  --color-ink:            #1A1A1A;   /* 墨黑 */

  /* 背景色 */
  --color-bg-page:        #F7F3EC;   /* 宣纸米白 */
  --color-bg-card:        #FFFFFF;
  --color-bg-sidebar:     #FDFAF4;
  --color-bg-header:      rgba(255,255,255,0.94);
  --color-bg-soft:        #FBF7EF;

  /* 文字色 */
  --color-text-primary:   #1A1A1A;
  --color-text-secondary: #4A4A4A;
  --color-text-muted:     #8A8A8A;
  --color-text-placeholder:#AAAAAA;

  /* 语义色 */
  --color-positive:       #2E7D32;
  --color-positive-light: #4CAF50;
  --color-negative:       #C62828;
  --color-negative-light: #E53935;
  --color-neutral:        #757575;
  --color-warning:        #F57F17;
  --color-hot:            #D84315;
  --color-dispute:        #6A1B9A;
  --color-blue:           #1565C0;
  --color-teal:           #00897B;

  /* 边框与分割 */
  --color-border:         #E8DDD0;
  --color-border-strong:  #C8B89A;
  --color-divider:        #EDE8E0;

  /* 字体 */
  --font-display:   'STKaiti', 'KaiTi', '楷体', serif;
  --font-heading:   'STSong', 'SimSun', 'Source Han Serif SC', serif;
  --font-body:      'PingFang SC', 'Noto Sans SC', 'Microsoft YaHei', sans-serif;
  --font-mono:      'JetBrains Mono', 'Fira Code', monospace;
  --font-en:        'Georgia', 'Times New Roman', serif;

  /* 字号 */
  --text-xs:    11px;
  --text-sm:    12px;
  --text-base:  13px;
  --text-md:    14px;
  --text-lg:    16px;
  --text-xl:    18px;
  --text-2xl:   22px;
  --text-3xl:   28px;
  --text-hero:  36px;

  /* 间距 */
  --space-1: 4px; --space-2: 8px; --space-3: 12px; --space-4: 16px;
  --space-5: 20px; --space-6: 24px; --space-8: 32px; --space-10: 40px;

  /* 圆角与阴影 */
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
  --radius-xl: 12px;
  --radius-2xl: 16px;
  --shadow-card:   0 1px 4px rgba(0,0,0,0.08), 0 0 0 1px var(--color-border);
  --shadow-hover:  0 4px 12px rgba(139,26,26,0.12);
  --shadow-panel:  2px 0 8px rgba(0,0,0,0.06);
}
```

------

## 三、全局页面骨架

### 3.1 标准三栏页

适用于：洞察、媒析、检索、论坛、报告。

```html
<div class="app-shell page-[name]">
  <header class="app-header">...</header>
  <main class="workspace three-column">
    <aside class="sidebar left-panel">...</aside>
    <section class="main-panel">...</section>
    <aside class="right-panel">...</aside>
  </main>
  <footer class="app-footer">...</footer>
</div>
```

```css
.app-shell {
  min-height: 100vh;
  background: var(--color-bg-page);
  color: var(--color-text-primary);
  font-family: var(--font-body);
  position: relative;
  overflow: hidden;
}
.workspace.three-column {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr) 260px;
  gap: 16px;
  padding: 16px 24px 0;
  min-height: calc(100vh - 104px);
  position: relative;
  z-index: 1;
}
.left-panel,
.main-panel,
.right-panel {
  background: rgba(255,255,255,0.82);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
}
.left-panel,
.right-panel { padding: 16px 14px; }
.main-panel { padding: 16px; }
```

### 3.2 总览页特殊两列骨架

适用于：总览页。

```css
.workspace.overview {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px 24px 0;
}
.top-panels {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1.25fr);
  gap: 16px;
}
.engine-modules {
  background: rgba(255,255,255,0.86);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  padding: 14px 22px 12px;
}
```

------

## 四、Header 规范

### 4.1 结构

```html
<header class="app-header">
  <div class="logo-area">
    <div class="logo-seal" aria-label="维舆印章">维<br/>舆</div>
    <div class="logo-copy">
      <div class="brand-name">维舆</div>
      <div class="brand-sub">Veyrafish · 以微知著，以舆定策</div>
    </div>
  </div>

  <h1 class="page-title">维舆-新时代高效通用多维度舆论平台</h1>
  <span class="title-seal">维<br/>明</span>

  <nav class="main-nav">
    <a class="nav-item active">总览</a>
    <a class="nav-item">洞察</a>
    <a class="nav-item">媒析</a>
    <a class="nav-item">检索</a>
    <a class="nav-item">论坛</a>
    <a class="nav-item">报告</a>
  </nav>
</header>
```

### 4.2 样式

```css
.app-header {
  height: 56px;
  padding: 0 28px;
  display: grid;
  grid-template-columns: 260px 1fr 420px;
  align-items: center;
  background: var(--color-bg-header);
  border-bottom: 1px solid var(--color-border);
  box-shadow: 0 2px 10px rgba(80, 60, 40, 0.08);
  position: sticky;
  top: 0;
  z-index: 10;
  backdrop-filter: blur(8px);
}
.logo-area { display: flex; align-items: center; gap: 10px; }
.logo-seal {
  width: 40px; height: 40px;
  background: var(--color-primary);
  color: #fff;
  border-radius: 4px;
  display: grid;
  place-items: center;
  line-height: 1.05;
  font-family: var(--font-heading);
  font-weight: 700;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,.22);
}
.brand-name { font: 700 20px/1 var(--font-heading); letter-spacing: 3px; }
.brand-sub { margin-top: 5px; font-size: 11px; color: var(--color-text-muted); letter-spacing: 3px; }
.page-title {
  margin: 0;
  text-align: center;
  font: 700 31px/1.1 var(--font-heading);
  letter-spacing: 4px;
  color: var(--color-ink);
}
.title-seal {
  display: inline-grid; place-items: center;
  width: 22px; height: 22px;
  margin-left: 8px;
  border: 1px solid var(--color-primary);
  color: var(--color-primary);
  font-size: 9px;
  line-height: 1;
  font-family: var(--font-display);
}
.main-nav { display: flex; justify-content: flex-end; align-items: center; gap: 24px; }
.nav-item {
  position: relative;
  padding: 20px 0 14px;
  color: var(--color-text-primary);
  text-decoration: none;
  font: 600 17px/1 var(--font-heading);
  letter-spacing: 2px;
}
.nav-item.active { color: var(--color-primary); }
.nav-item.active::after {
  content: '';
  position: absolute;
  left: 0; right: 0; bottom: 6px;
  height: 2px;
  background: var(--color-primary);
}
```

------

## 五、通用组件规范

### 5.1 卡片 / 面板

```css
.panel-card {
  background: rgba(255,255,255,0.86);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-card);
}
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  min-height: 28px;
}
.section-title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font: 700 18px/1.2 var(--font-heading);
  letter-spacing: 2px;
}
.section-title::after {
  content: '';
  width: 22px; height: 12px;
  background: url('/assets/ink-cloud.svg') center/contain no-repeat;
  opacity: .55;
}
.section-title .red-line,
.section-header::after { display: none; }
```

### 5.2 左侧筛选栏

```css
.sidebar-section { margin-bottom: 16px; }
.sidebar-section-title {
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-divider);
  font: 700 17px/1.2 var(--font-heading);
  letter-spacing: 2px;
}
.sidebar-section-title::after {
  content: '';
  display: block;
  width: 18px;
  height: 2px;
  margin-top: 8px;
  background: var(--color-primary);
}
.sidebar-nav { display: flex; flex-direction: column; gap: 2px; }
.sidebar-nav-item {
  display: flex; align-items: center; gap: 10px;
  min-height: 38px;
  padding: 0 14px;
  border-radius: var(--radius-md);
  font-size: 14px;
  color: var(--color-text-secondary);
  cursor: pointer;
}
.sidebar-nav-item.active {
  background: #FFF0F0;
  color: var(--color-primary);
  border-left: 3px solid var(--color-primary);
  font-weight: 700;
}
.filter-group { margin: 12px 0; }
.filter-label { font-size: 12px; color: var(--color-text-secondary); margin-bottom: 6px; }
.filter-select,
.filter-input,
.date-picker-row {
  height: 32px;
  width: 100%;
  border: 1px solid var(--color-border-strong);
  border-radius: var(--radius-md);
  background: rgba(255,255,255,.74);
  padding: 0 10px;
  color: var(--color-text-secondary);
  font-size: 12px;
}
.sidebar-footer { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 18px; }
```

### 5.3 按钮

```css
.btn-primary,
.btn-secondary,
.btn-outline {
  height: 36px;
  border-radius: var(--radius-md);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 0 18px;
  font-size: 14px;
  cursor: pointer;
  transition: .18s ease;
}
.btn-primary { background: var(--color-primary); color: #fff; border: 1px solid var(--color-primary); }
.btn-primary:hover { background: var(--color-primary-light); box-shadow: var(--shadow-hover); }
.btn-secondary { background: var(--color-gold); color: #fff; border: 1px solid var(--color-gold); }
.btn-outline { background: rgba(255,255,255,.58); color: var(--color-text-secondary); border: 1px solid var(--color-border-strong); }
.full-width { width: 100%; }
```

### 5.4 KPI 卡

```css
.kpi-bar { display: grid; grid-template-columns: repeat(5, minmax(0,1fr)); gap: 12px; }
.kpi-card {
  min-height: 82px;
  padding: 14px 16px;
  background: linear-gradient(180deg, rgba(255,255,255,.9), rgba(253,250,244,.9));
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
}
.kpi-header { display: flex; align-items: center; gap: 8px; margin-bottom: 6px; }
.kpi-icon { font-size: 24px; color: var(--color-primary); }
.kpi-label { font-size: 13px; color: var(--color-text-secondary); letter-spacing: 1px; }
.kpi-value { font: 700 26px/1.1 var(--font-mono); color: var(--color-text-primary); }
.kpi-change { margin-top: 6px; font-size: 11px; }
.kpi-change.up { color: var(--color-negative); }
.kpi-change.down { color: var(--color-positive); }
```

### 5.5 标签 / 徽章

```css
.tag { display: inline-flex; align-items: center; justify-content: center; min-height: 18px; padding: 0 7px; border-radius: 4px; font-size: 11px; }
.tag-hot { background: #FFEBE6; color: #C62828; border: 1px solid #FFCDD2; }
.tag-high { background: #FFF3E0; color: #E65100; border: 1px solid #FFCC80; }
.tag-positive { background: #E8F5E9; color: #2E7D32; }
.tag-negative { background: #FFEBEE; color: #C62828; }
.tag-neutral { background: #F5F5F5; color: #757575; }
.tag-media { background: #E3F2FD; color: #1565C0; }
.tag-forum { background: #F3E5F5; color: #6A1B9A; }
```

------

## 六、图表统一规范

- **图表背景**：透明或白色，无厚重外框；允许叠加淡山水背景，透明度 `0.05 ~ 0.10`。
- **折线**：总量黑、正向绿、负向红、中性灰，节点空心圆，线宽 1.5~2px。
- **坐标轴**：浅灰 `#D8D0C6`，字号 11px。
- **图例**：居上、靠中或靠右，小线段 + 文本，不使用高饱和色块。
- **Tooltip**：白底、米棕边框、轻阴影、圆角 6px。
- **柱状 / 排行图**：圆角端点；序号 1~3 使用红、橙、绿，其后灰色。
- **地图热力**：浅米底图，热度由浅橙到深红，右下角加“低—高”渐变尺。

------

## 七、背景装饰

```css
.app-shell::before {
  content: '';
  position: fixed;
  right: 0;
  top: 56px;
  width: 120px;
  height: 120px;
  background: url('/assets/ink-bamboo.svg') right top/contain no-repeat;
  opacity: .35;
  pointer-events: none;
}
.app-shell::after {
  content: '';
  position: fixed;
  left: 0; right: 0; bottom: 0;
  height: 120px;
  background: url('/assets/ink-mountain-wide.svg') center bottom/cover no-repeat;
  opacity: .18;
  pointer-events: none;
}
.app-footer .boat {
  position: absolute;
  right: 170px;
  bottom: 3px;
  width: 90px;
  opacity: .55;
}
```

------

## 八、Footer 规范

```html
<footer class="app-footer">
  <span class="footer-motto">以 微 知 著 · 以 舆 定 策</span>
  <span class="footer-seal">维</span>
  <img class="boat" src="/assets/ink-boat.svg" alt="" />
</footer>
```

```css
.app-footer {
  height: 48px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  font: 16px/1 var(--font-display);
  color: var(--color-text-secondary);
  letter-spacing: 9px;
  z-index: 1;
}
.footer-seal {
  margin-left: 10px;
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
  font-size: 11px;
  letter-spacing: 0;
  padding: 2px 3px;
}
```

------

## 九、响应式与缩放约束

1. 设计稿参考分辨率为 `1672 × 941`，实现推荐以 `1440px` 作为最小桌面宽度。
2. `1200px ~ 1439px`：保持三栏，但左右栏可压缩为 `200px / 240px`，KPI 字号降 2px。
3. `< 1200px`：右侧面板下移到主内容下方，左栏可改为顶部横向筛选抽屉。
4. 避免写死主内容高度；图表容器使用 `height` 固定、外层可滚动。
5. 浏览器缩放时，Header 标题优先保持居中；导航间距可收缩，但不换行。

------

## 十、素材命名建议

```text
/assets/brand/logo-seal-veyu.svg
/assets/brand/title-seal-veyu.svg
/assets/decor/ink-bamboo.svg
/assets/decor/ink-cloud.svg
/assets/decor/ink-mountain-wide.svg
/assets/decor/ink-boat.svg
/assets/icons/engine-insight.svg
/assets/icons/engine-media.svg
/assets/icons/engine-query.svg
/assets/icons/engine-forum.svg
/assets/icons/engine-report.svg
```

