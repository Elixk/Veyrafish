import React, { useState, useEffect } from 'react';
import { Menu, ChevronDown, Mail, User, Send, Search, Sparkles, MoveRight } from 'lucide-react';

// --- 视觉核心组件 (SVG & Canvas Effects) ---

const InkSplash = ({ className, style }) => (
  <svg viewBox="0 0 200 200" className={className} style={style}>
    <defs>
      <filter id="inkBlur" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur in="SourceGraphic" stdDeviation="4" />
        <feColorMatrix type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 20 -8" />
      </filter>
    </defs>
    <path
      d="M100,40 C150,30 180,60 170,100 C190,140 150,180 100,170 C50,190 20,150 30,110 C10,70 50,30 100,40"
      fill="currentColor"
      filter="url(#inkBlur)"
      opacity="0.5"
    />
  </svg>
);

const BrushStroke = ({ width = 200, height = 12, className = "" }) => (
  <svg viewBox={`0 0 ${width} ${height}`} className={className} style={{ width, height }}>
    <defs>
      <filter id="brushTexture">
        <feTurbulence type="fractalNoise" baseFrequency="0.08" numOctaves="4" result="noise" />
        <feDisplacementMap in="SourceGraphic" in2="noise" scale="6" />
      </filter>
    </defs>
    <path
      d={`M4,${height / 2} C${width * 0.3},${height * 0.05} ${width * 0.6},${height * 0.95} ${width - 4},${height / 2}`}
      stroke="currentColor"
      strokeWidth={height * 0.5}
      fill="none"
      strokeLinecap="round"
      filter="url(#brushTexture)"
    />
  </svg>
);

const Seal = ({ text, variant = 'square', size = 60, className = "" }) => (
  <div
    className={`flex items-center justify-center p-1 select-none shadow-lg transition-all duration-500 hover:rotate-0 ${className}`}
    style={{
      width: size,
      height: size,
      backgroundColor: '#C41E3A',
      borderRadius: variant === 'square' ? '1px' : '50%',
      boxShadow: 'inset 0 0 15px rgba(0,0,0,0.3)',
      transform: `rotate(${Math.random() * 6 - 3}deg)`,
    }}
  >
    <span
      className="text-white font-seal leading-none text-center font-bold"
      style={{
        fontSize: size * 0.38,
        writingMode: 'vertical-rl',
        textOrientation: 'upright',
        fontFamily: '"ZCOOL KuaiLe", cursive',
        filter: 'drop-shadow(1px 1px 1px rgba(0,0,0,0.2))'
      }}
    >
      {text}
    </span>
  </div>
);

const Mountain = ({ opacity, blur, yOffset, color, variant = 0 }) => {
  const paths = [
    'M0,100 L0,40 C15,30 30,55 50,25 C70,5 90,45 100,20 L100,100 Z',
    'M0,100 L0,60 C20,50 40,70 60,40 C80,20 90,50 100,30 L100,100 Z',
    'M0,100 L0,70 C30,60 50,85 70,55 C85,30 95,65 100,45 L100,100 Z',
  ];
  return (
    <div
      className="absolute bottom-0 left-0 right-0 h-[600px] pointer-events-none transition-all duration-[2s] ease-out"
      style={{
        background: `linear-gradient(to bottom, transparent, ${color})`,
        opacity,
        filter: `blur(${blur}px)`,
        clipPath: `path('${paths[variant % 3]}')`,
        transform: `translateY(${yOffset}px)`,
      }}
    />
  );
};

const InkDropEffect = ({ x, y, onComplete }) => {
  const [active, setActive] = useState(false);
  useEffect(() => {
    setActive(true);
    const timer = setTimeout(onComplete, 1400);
    return () => clearTimeout(timer);
  }, [onComplete]);

  return (
    <div
      className="fixed pointer-events-none z-[9999]"
      style={{
        left: x - 60,
        top: y - 60,
        width: 120,
        height: 120,
        background: 'radial-gradient(circle, rgba(26,26,26,0.4) 0%, transparent 75%)',
        transform: active ? 'scale(4)' : 'scale(0.1)',
        opacity: active ? 0 : 0.7,
        transition: 'transform 1.2s cubic-bezier(0.19, 1, 0.22, 1), opacity 1.2s ease-out',
        filter: 'blur(8px)'
      }}
    />
  );
};

// --- 布局组件 ---

const Navigation = ({ activeSection, onNavigate }) => {
  const items = [
    { id: 'hero', label: '卷首', en: 'Hero' },
    { id: 'philosophy', label: '致理', en: 'Tao' },
    { id: 'gallery', label: '意境', en: 'Art' },
    { id: 'colors', label: '墨变', en: 'Ink' },
    { id: 'contact', label: '问道', en: 'Join' }
  ];

  return (
    <nav className="fixed right-16 top-1/2 -translate-y-1/2 z-50 flex flex-col items-end gap-16">
      {items.map((item) => (
        <button
          key={item.id}
          onClick={() => onNavigate(item.id)}
          className="group flex flex-col items-end focus:outline-none"
        >
          <span className={`font-calligraphy-行 text-3xl transition-all duration-700 ${activeSection === item.id ? 'text-seal-red -translate-x-2' : 'text-pale-ink opacity-30 hover:opacity-100'}`}>
            {item.label}
          </span>
          <div className={`h-[1px] mt-2 transition-all duration-700 bg-seal-red ${activeSection === item.id ? 'w-16' : 'w-0'}`} />
          <span className={`font-serif text-[8px] tracking-[0.4em] uppercase mt-1 transition-all duration-700 ${activeSection === item.id ? 'opacity-100 text-seal-red' : 'opacity-0'}`}>
            {item.en}
          </span>
        </button>
      ))}
    </nav>
  );
};

const SectionHeader = ({ title, subtitle, english, align = "left" }) => (
  <div className={`mb-32 relative flex flex-col ${align === 'right' ? 'items-end' : 'items-start'}`}>
    <div className={`flex gap-8 ${align === 'right' ? 'flex-row-reverse' : 'flex-row'}`}>
      <div className="vertical-text font-calligraphy-行 text-7xl text-burnt-ink pt-4">
        {title}
      </div>
      <div className={`pt-4 ${align === 'right' ? 'text-right' : 'text-left'}`}>
        <h2 className="text-sm font-serif tracking-[0.8em] text-gold uppercase mb-3">{english}</h2>
        <div className={`h-[2px] bg-seal-red mb-6 ${align === 'right' ? 'w-24 ml-auto' : 'w-24'}`} />
        <p className="font-body-楷 text-2xl text-light-ink max-w-md italic leading-relaxed">
          {subtitle}
        </p>
      </div>
    </div>
  </div>
);

// --- 页面章节 ---

const Hero = () => (
  <section id="hero" className="relative min-h-screen flex items-center justify-start px-24 md:px-48 overflow-hidden">
    <div className="absolute inset-0 opacity-15 mist-drift pointer-events-none" />
    
    {/* 远山背景 */}
    <Mountain opacity={0.12} blur={5} yOffset={20} color="#1a1a1a" variant={0} />
    <Mountain opacity={0.07} blur={12} yOffset={80} color="#555" variant={1} />
    <div className="absolute left-[-5%] bottom-0 opacity-10 scale-150">
       <InkSplash className="w-[800px] h-[800px] text-burnt-ink" />
    </div>

    <div className="relative z-10 w-full grid grid-cols-1 lg:grid-cols-12 gap-12">
      <div className="lg:col-span-7">
        <div className="mb-12 flex items-center gap-6 opacity-0 animate-fade-in">
          <span className="text-gold tracking-[0.8em] font-serif text-xs uppercase">岁在乙巳 · 墨韵重光</span>
          <BrushStroke width={120} height={4} className="text-gold/40" />
        </div>

        <h1 className="font-calligraphy-草 text-[13vw] leading-[0.9] text-burnt-ink mb-12 select-none animate-ink-bleed">
          水墨意境
        </h1>
        
        <div className="max-w-xl">
          <p className="font-body-楷 text-3xl text-dense-ink leading-relaxed mb-12">
            「气韵」乃水墨之魂。
            <br />
            于虚实之间，见山见水，见众生。
          </p>
          <div className="flex gap-12 items-center">
             <button className="px-10 py-4 border border-burnt-ink font-calligraphy-行 text-2xl hover:bg-burnt-ink hover:text-white transition-all duration-500">
               入 卷
             </button>
             <div className="flex gap-6">
                <Seal text="墨趣" size={60} />
                <Seal text="入画" variant="round" size={60} />
             </div>
          </div>
        </div>
      </div>

      <div className="lg:col-span-5 flex justify-end items-center relative">
         <div className="vertical-text font-calligraphy-行草 text-4xl text-pale-ink/30 tracking-[1.5em] leading-loose">
           虚实相生 · 无画处皆成妙境
         </div>
         <div className="absolute right-32 top-1/2 -translate-y-1/2 opacity-5 pointer-events-none">
            <span className="text-[30vw] font-calligraphy-草">意</span>
         </div>
      </div>
    </div>

    {/* 滚动引导 */}
    <div className="absolute bottom-16 right-48 flex flex-col items-center gap-6 opacity-30 animate-pulse">
      <span className="vertical-text font-calligraphy-行 text-sm tracking-widest">下 寻</span>
      <div className="w-[1px] h-24 bg-gradient-to-b from-dense-ink to-transparent" />
    </div>
  </section>
);

const Philosophy = () => {
  const items = [
    { char: '空', title: '留白', en: 'Negative Space', desc: '空白并非虚无，而是宇宙的呼吸，是意境无穷的延伸。' },
    { char: '墨', title: '五色', en: 'Five Shades', desc: '焦浓重淡清，以极致的一色演绎世间万象的绚烂。' },
    { char: '韵', title: '气韵', en: 'Spirit Resonance', desc: '不求形似，唯求神采，让生命力在笔尖自由流淌。' },
    { char: '道', title: '虚实', en: 'Void & Solid', desc: '相生相合，有墨处是生命，无墨处是天地。' },
  ];

  return (
    <section id="philosophy" className="relative min-h-screen py-48 px-24 md:px-48 bg-[#FFFFF0]">
      <SectionHeader 
        title="艺术致理" 
        english="Artistic Philosophy"
        subtitle="「笔墨本无情，因心而成境。心之所向，境之所造。」"
        align="left"
      />

      <div className="flex flex-col gap-40">
        {items.map((item, i) => (
          <div key={i} className={`flex flex-col lg:flex-row gap-20 items-center ${i % 2 === 1 ? 'lg:flex-row-reverse' : ''}`}>
            <div className="relative group">
               <span className="text-[220px] font-calligraphy-草 text-burnt-ink opacity-[0.03] group-hover:opacity-10 transition-all duration-1000 leading-none select-none">
                 {item.char}
               </span>
               <div className="absolute inset-0 flex items-center justify-center">
                  <Seal text={item.char} size={50} className="opacity-0 group-hover:opacity-100 transition-all duration-700" />
               </div>
            </div>
            <div className={`max-w-md ${i % 2 === 1 ? 'text-right' : 'text-left'}`}>
              <div className={`flex items-center gap-6 mb-8 ${i % 2 === 1 ? 'flex-row-reverse' : ''}`}>
                <h3 className="font-calligraphy-行 text-5xl text-dense-ink">{item.title}</h3>
                <div className="h-[1px] w-20 bg-seal-red/20" />
                <span className="font-serif text-[10px] tracking-widest text-pale-ink uppercase">{item.en}</span>
              </div>
              <p className="font-body-楷 text-2xl text-light-ink leading-relaxed">
                {item.desc}
              </p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};

const Gallery = () => {
  const artworks = [
    { title: '远山含黛', en: 'Distant Peaks', poem: '青山横北郭，白水绕东城' },
    { title: '清风徐来', en: 'Bamboo Breeze', poem: '虚心秉直节，不逐俗流迁' },
    { title: '暗香浮动', en: 'Plum Blossom', poem: '疏影横斜水清浅，暗香浮动月黄昏' },
    { title: '云烟浩渺', en: 'Mystic Mist', poem: '行到水穷处，坐看云起时' },
  ];

  return (
    <section id="gallery" className="relative min-h-screen py-48 px-24 md:px-48">
      <SectionHeader 
        title="水墨意象" 
        english="Visual Imagery"
        subtitle="以极简御至繁，于方寸间窥见万象。"
        align="right"
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-16">
        {artworks.map((work, i) => (
          <div key={i} className={`group relative aspect-[4/3] overflow-hidden bg-white shadow-2xl transition-all duration-1000 hover:-translate-y-4 ${i % 2 === 1 ? 'mt-24' : ''}`}>
            <div className="absolute inset-0 p-12 z-20 flex flex-col justify-between h-full bg-[#FAF0E6]/90 transition-all duration-700 group-hover:bg-[#FAF0E6]/10">
               <div className="flex justify-between items-start">
                  <div className="vertical-text font-calligraphy-行草 text-2xl text-dense-ink tracking-widest opacity-0 group-hover:opacity-60 transition-all duration-1000">
                    {work.poem}
                  </div>
                  <Seal text={work.title[0]} variant="round" size={40} className="opacity-0 group-hover:opacity-100 transition-opacity" />
               </div>
               <div>
                  <h4 className="font-calligraphy-行 text-5xl mb-4 text-burnt-ink group-hover:text-seal-red transition-colors">{work.title}</h4>
                  <p className="font-serif text-[11px] tracking-widest text-pale-ink uppercase">{work.en}</p>
               </div>
            </div>
            
            <div className="absolute inset-0 z-10 opacity-20 group-hover:opacity-100 transition-opacity duration-1000">
               <InkSplash className="w-full h-full text-dense-ink scale-150 rotate-45" />
            </div>
            
            {/* 纸张纹理 */}
            <div className="absolute inset-0 bg-repeat opacity-[0.03] pointer-events-none" style={{backgroundImage: 'url("https://www.transparenttextures.com/patterns/p6.png")'}} />
          </div>
        ))}
      </div>
    </section>
  );
};

const ColorPalette = () => {
  const colors = [
    { name: '焦墨', en: 'Burnt', hex: '#1a1a1a', desc: '至极之黑，苍劲有力' },
    { name: '浓墨', en: 'Dense', hex: '#333333', desc: '厚重沉稳，气势磅礴' },
    { name: '重墨', en: 'Heavy', hex: '#666666', desc: '浑厚润泽，富有神采' },
    { name: '淡墨', en: 'Light', hex: '#999999', desc: '明快清爽，层次分明' },
    { name: '清墨', en: 'Clear', hex: '#cccccc', desc: '灵动通透，妙趣横生' },
  ];

  return (
    <section id="colors" className="relative min-h-screen py-48 px-24 md:px-48 bg-[#FAF0E6]">
      <SectionHeader 
        title="墨分五色" 
        english="Shades of Black"
        subtitle="「墨即是色」。一滴浓墨入水，便是万物色彩的诞生。"
        align="left"
      />

      <div className="flex flex-col lg:flex-row h-[600px] border border-dense-ink/10">
        {colors.map((c, i) => (
          <div 
            key={i} 
            className="flex-1 group relative transition-all duration-[1s] hover:flex-[2] cursor-pointer"
            style={{ backgroundColor: c.hex }}
          >
             <div className="absolute inset-0 flex flex-col items-center justify-center text-white/20 group-hover:text-white transition-all duration-700">
                <span className="vertical-text font-calligraphy-行 text-6xl mb-8 group-hover:scale-110 transition-transform">{c.name}</span>
                <div className="opacity-0 group-hover:opacity-100 transition-opacity text-center px-6">
                  <p className="font-serif text-[10px] tracking-[0.5em] uppercase mb-4">{c.en}</p>
                  <p className="font-body-楷 text-lg whitespace-nowrap">{c.desc}</p>
                </div>
             </div>
          </div>
        ))}
      </div>
    </section>
  );
};

const Contact = () => (
  <section id="contact" className="relative min-h-screen bg-burnt-ink py-48 px-24 md:px-48 text-[#F8F5F0]">
    <div className="absolute top-0 right-0 w-1/2 h-full opacity-[0.02] pointer-events-none">
       <span className="text-[60vw] font-calligraphy-草 leading-none absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">缘</span>
    </div>

    <div className="relative z-10 max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-40 items-center">
      <div className="text-right flex flex-col items-end">
        <h2 className="font-calligraphy-行 text-[10vw] mb-12">问道</h2>
        <div className="h-[2px] w-32 bg-seal-red mb-12" />
        <p className="font-body-楷 text-3xl leading-loose text-pale-ink mb-16 max-w-lg">
          「墨香引知己，笔端叙平生。」
          <br />
          愿于这片方寸之地，与君结下一段笔墨奇缘。
        </p>
        <div className="flex gap-8">
           <Seal text="至诚" size={80} />
           <Seal text="问道" variant="round" size={80} />
        </div>
      </div>

      <div className="bg-white/5 p-16 backdrop-blur-sm border border-white/10">
        <div className="space-y-16">
          {['尊姓大名 / Your Name', '电子邮箱 / Your Email', '心中所言 / Your Message'].map((placeholder, idx) => (
            <div key={idx} className="relative group">
              {idx < 2 ? (
                <input 
                  type="text" 
                  placeholder={placeholder} 
                  className="w-full bg-transparent py-6 font-body-楷 text-2xl border-b border-white/20 outline-none placeholder:text-white/10 transition-all group-focus-within:border-seal-red group-focus-within:pl-4"
                />
              ) : (
                <textarea 
                  rows={3} 
                  placeholder={placeholder} 
                  className="w-full bg-transparent py-6 font-body-楷 text-2xl border-b border-white/20 outline-none placeholder:text-white/10 transition-all group-focus-within:border-seal-red group-focus-within:pl-4 resize-none"
                />
              )}
            </div>
          ))}
          <button className="w-full py-8 bg-transparent border border-white/30 font-calligraphy-行 text-4xl tracking-[0.6em] hover:bg-seal-red hover:border-seal-red hover:text-white transition-all duration-700">
            投 帖
          </button>
        </div>
      </div>
    </div>

    <footer className="absolute bottom-16 left-24 right-48 flex flex-col md:flex-row justify-between items-center opacity-30 text-[11px] font-serif uppercase tracking-[0.5em] border-t border-white/10 pt-10">
      <div className="flex items-center gap-6">
        <span>© 2025 水墨意境</span>
        <div className="w-8 h-[1px] bg-white/40" />
        <span>INK RESONANCE GALLERY</span>
      </div>
      <div className="flex gap-12">
        <span>气韵生动</span>
        <span>虚实相生</span>
        <span>计白当黑</span>
      </div>
    </footer>
  </section>
);

// --- 主应用入口 ---

export default function App() {
  const [activeSection, setActiveSection] = useState('hero');
  const [inkDrops, setInkDrops] = useState([]);

  // 滚动监听
  useEffect(() => {
    const handleScroll = () => {
      const sections = ['hero', 'philosophy', 'gallery', 'colors', 'contact'];
      const current = sections.find(id => {
        const el = document.getElementById(id);
        if (el) {
          const rect = el.getBoundingClientRect();
          return rect.top <= 200 && rect.bottom >= 200;
        }
        return false;
      });
      if (current) setActiveSection(current);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  // 点击水墨效果
  const handleClick = (e) => {
    const drop = { id: Date.now(), x: e.clientX, y: e.clientY };
    setInkDrops(prev => [...prev, drop]);
  };

  const navigateTo = (id) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <>
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      <link href="https://fonts.googleapis.com/css2?family=Liu+Jian+Mao+Cao&family=Ma+Shan+Zheng&family=Zhi+Mang+Xing&family=ZCOOL+XiaoWei&family=ZCOOL+KuaiLe&family=Noto+Serif+SC:wght@300;700&display=swap" rel="stylesheet" />

      <style>{`
        :root {
          --burnt-ink: #1a1a1a;
          --dense-ink: #333333;
          --seal-red: #C41E3A;
          --gold: #D4AF37;
        }

        .font-calligraphy-草 { font-family: 'Liu Jian Mao Cao', cursive; }
        .font-calligraphy-行 { font-family: 'Ma Shan Zheng', cursive; }
        .font-calligraphy-行草 { font-family: 'Zhi Mang Xing', cursive; }
        .font-body-楷 { font-family: 'ZCOOL XiaoWei', serif; }
        .font-seal { font-family: 'ZCOOL KuaiLe', cursive; }

        .vertical-text {
          writing-mode: vertical-rl;
          text-orientation: mixed;
        }

        body {
          background-color: #F8F5F0;
          background-image: url("https://www.transparenttextures.com/patterns/p6.png");
          overflow-x: hidden;
        }

        @keyframes drift {
          0%, 100% { transform: translate(-3%, -3%); opacity: 0.15; }
          50% { transform: translate(3%, 3%); opacity: 0.35; }
        }
        .mist-drift {
          background: radial-gradient(circle, white 0%, transparent 80%);
          filter: blur(100px);
          animation: drift 20s infinite ease-in-out;
        }

        @keyframes inkBleed {
          0% { filter: blur(15px); opacity: 0; transform: translateY(20px) scale(0.95); }
          100% { filter: blur(0); opacity: 1; transform: translateY(0) scale(1); }
        }
        .animate-ink-bleed {
          animation: inkBleed 3s cubic-bezier(0.19, 1, 0.22, 1) forwards;
        }

        .animate-fade-in {
          animation: fadeIn 4s ease-out forwards;
        }

        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: #F8F5F0; }
        ::-webkit-scrollbar-thumb { background: #C41E3A; }
      `}</style>

    <div className="bg-[#F8F5F0] min-h-screen selection:bg-seal-red/30 scroll-smooth cursor-crosshair" onClick={handleClick}>
      {/* 点击交互 */}
      {inkDrops.map(drop => (
        <InkDropEffect
          key={drop.id}
          x={drop.x}
          y={drop.y}
          onComplete={() => setInkDrops(prev => prev.filter(d => d.id !== drop.id))}
        />
      ))}

      {/* 顶部标号 */}
      <header className="fixed top-0 left-0 w-full z-50 p-16 flex justify-between items-center pointer-events-none">
        <div className="flex items-center gap-8 pointer-events-auto">
          <Seal text="意境" size={55} />
          <div className="flex flex-col">
             <span className="font-calligraphy-行 text-4xl text-burnt-ink">墨韵展馆</span>
             <span className="font-serif text-[9px] tracking-[0.6em] text-dense-ink/50 uppercase mt-1">Ink Essence Gallery</span>
          </div>
        </div>
        
        <div className="pointer-events-auto flex items-center gap-12 group cursor-pointer">
           <span className="font-calligraphy-行 text-2xl text-burnt-ink opacity-0 group-hover:opacity-100 transition-opacity">目录</span>
           <div className="flex flex-col gap-2 items-end">
              <div className="w-10 h-[2px] bg-burnt-ink" />
              <div className="w-14 h-[2px] bg-burnt-ink" />
              <div className="w-6 h-[2px] bg-burnt-ink" />
           </div>
        </div>
      </header>

      <Navigation activeSection={activeSection} onNavigate={navigateTo} />

      <main>
        <Hero />
        
        <div className="py-24 flex justify-center opacity-10">
           <BrushStroke width={500} height={18} className="text-burnt-ink" />
        </div>

        <Philosophy />
        <Gallery />
        <ColorPalette />
        <Contact />
      </main>

      {/* 侧边装饰 */}
      <div className="fixed left-16 bottom-32 hidden xl:block opacity-30 vertical-text font-calligraphy-行草 text-2xl text-light-ink pointer-events-none tracking-[1.2em]">
         笔墨本无情 · 意在笔先 · 气韵生动
      </div>
    </div>
    </>
  );
}
