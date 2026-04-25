import React, { useState, useEffect } from 'react';
import { Wind, Circle, Feather, Mountain, Cloud } from 'lucide-react';

/**
 * 墨韵 - Ink Realm
 * 一个展示中国传统水墨美学的 React 组件
 */

export default function InkRealm() {
  const [activeSection, setActiveSection] = useState('intro');
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });

  // 模拟宣纸纹理的噪点背景
  const paperTexture = `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.05'/%3E%3C/svg%3E")`;

  useEffect(() => {
    const handleMouseMove = (e) => {
      // 简单的视差移动效果
      const x = (e.clientX / window.innerWidth - 0.5) * 20;
      const y = (e.clientY / window.innerHeight - 0.5) * 20;
      setMousePos({ x, y });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <div className="min-h-screen bg-[#F8F5F0] text-[#1a1a1a] overflow-x-hidden selection:bg-[#C41E3A] selection:text-white relative font-sans">
      {/* 字体加载 */}
      <style dangerouslySetInnerHTML={{__html: `
        @import url('https://fonts.googleapis.com/css2?family=Liu+Jian+Mao+Cao&family=Ma+Shan+Zheng&family=Zhi+Mang+Xing&family=ZCOOL+XiaoWei&family=ZCOOL+KuaiLe&family=Noto+Serif+SC:wght@300;700&display=swap');

        /* 字体类定义 */
        .font-cao { font-family: 'Liu Jian Mao Cao', cursive; }
        .font-xing { font-family: 'Ma Shan Zheng', cursive; }
        .font-xingcao { font-family: 'Zhi Mang Xing', cursive; }
        .font-kai { font-family: 'ZCOOL XiaoWei', serif; }
        .font-seal { font-family: 'ZCOOL KuaiLe', cursive; }
        .font-serif { font-family: 'Noto Serif SC', serif; }

        /* 竖排文字工具类 */
        .vertical-rl {
          writing-mode: vertical-rl;
          text-orientation: mixed;
        }

        /* 水墨扩散动画 */
        @keyframes ink-spread {
          0% { transform: scale(0.9); opacity: 0.8; filter: blur(2px); }
          100% { transform: scale(1.1); opacity: 0; filter: blur(8px); }
        }

        .ink-spread-hover:hover::after {
          content: '';
          position: absolute;
          inset: -10px;
          background: radial-gradient(circle, rgba(0,0,0,0.1) 0%, rgba(0,0,0,0) 70%);
          border-radius: 50%;
          animation: ink-spread 1s ease-out forwards;
        }

        /* 模拟毛笔边缘 */
        .brush-edge {
          mask-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M0,50 Q50,0 100,50 T200,50 V100 H0 Z' fill='black' filter='url(%23noiseFilter)'/%3E%3C/svg%3E");
        }
      `}} />

      {/* 背景纹理层 */}
      <div
        className="fixed inset-0 pointer-events-none z-50 mix-blend-multiply opacity-40"
        style={{ backgroundImage: paperTexture }}
      />

      {/* 导航栏 - 极简印章风格 */}
      <nav className="fixed top-0 left-0 w-full p-8 z-40 flex justify-between items-start pointer-events-none">
        <div className="pointer-events-auto cursor-pointer group">
          <div className="w-12 h-12 border-2 border-[#C41E3A] flex items-center justify-center rounded-sm bg-white/50 backdrop-blur-sm transition-transform duration-500 group-hover:rotate-12">
            <span className="font-seal text-[#C41E3A] text-2xl">墨</span>
          </div>
        </div>
        <div className="flex gap-8 pointer-events-auto vertical-rl h-48 pt-4">
          {['意境', '技法', '字体', '联系'].map((item, idx) => (
            <a key={idx} href={`#${item}`} className="font-xing text-lg text-[#666666] hover:text-[#1a1a1a] transition-colors duration-300 hover:font-bold tracking-widest py-2 relative group">
              {item}
              <span className="absolute -left-2 top-1/2 -translate-y-1/2 w-1 h-1 bg-[#C41E3A] rounded-full opacity-0 group-hover:opacity-100 transition-opacity" />
            </a>
          ))}
        </div>
      </nav>

      {/* 第一幕：主视觉 (Hero Section) */}
      <section className="relative w-full h-screen flex flex-col items-center justify-center overflow-hidden">

        {/* 背景墨韵动画 */}
        <div className="absolute inset-0 z-0">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-[#999999] rounded-full mix-blend-multiply filter blur-[80px] opacity-20 animate-pulse" style={{ animationDuration: '8s' }}></div>
          <div className="absolute bottom-1/3 right-1/4 w-64 h-64 bg-[#333333] rounded-full mix-blend-multiply filter blur-[60px] opacity-10"></div>
          {/* 远山淡影 */}
          <div
            className="absolute bottom-0 w-full h-[40vh] bg-gradient-to-t from-[#666666] to-transparent opacity-20 filter blur-[4px]"
            style={{ transform: `translateX(${mousePos.x * -0.5}px)` }}
          ></div>
          <div
            className="absolute -bottom-10 w-full h-[30vh] bg-gradient-to-t from-[#333333] to-transparent opacity-30 filter blur-[2px]"
            style={{
              clipPath: 'polygon(0% 100%, 20% 40%, 45% 80%, 60% 30%, 80% 60%, 100% 100%)',
              transform: `translateX(${mousePos.x * -1}px)`
            }}
          ></div>
        </div>

        {/* 核心标题区 */}
        <div className="z-10 relative text-center p-8">
          <div className="mb-4 flex items-center justify-center gap-2 opacity-60">
            <div className="h-[1px] w-12 bg-[#333333]"></div>
            <span className="font-serif text-sm tracking-[0.3em] uppercase">The Philosophy of Ink</span>
            <div className="h-[1px] w-12 bg-[#333333]"></div>
          </div>

          <h1 className="font-cao text-[15vw] leading-[0.8] text-[#1a1a1a] mix-blend-multiply relative select-none">
            <span className="inline-block" style={{ transform: `translateY(${mousePos.y * 0.5}px)` }}>气</span>
            <span className="inline-block text-[#333333]" style={{ transform: `translateY(${mousePos.y * -0.5}px)` }}>韵</span>
          </h1>

          <div className="mt-12 flex justify-center items-center gap-12">
             <div className="vertical-rl font-xingcao text-2xl text-[#666666] h-32 border-r border-[#999999]/30 pr-4">
               笔墨生万象
             </div>
             <div className="vertical-rl font-xingcao text-2xl text-[#666666] h-32 pr-4">
               虚实蕴真意
             </div>
          </div>
        </div>

        {/* 红色印章装饰 */}
        <div className="absolute bottom-20 right-20 z-10 opacity-80 hover:opacity-100 transition-opacity duration-500">
           <div className="w-16 h-16 border-[3px] border-[#C41E3A] rounded-lg p-1">
             <div className="w-full h-full border border-[#C41E3A] flex flex-col items-center justify-center bg-[#C41E3A] text-[#F8F5F0]">
                <span className="font-seal text-2xl leading-none">得</span>
                <span className="font-seal text-2xl leading-none">意</span>
             </div>
           </div>
        </div>
      </section>

      {/* 第二幕：墨分五色 (Colors & Philosophy) */}
      <section className="relative py-32 px-8 max-w-7xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-12">
          {/* 左侧说明 */}
          <div className="md:col-span-4 space-y-8 sticky top-32 h-fit">
            <h2 className="font-xing text-5xl text-[#1a1a1a] mb-2">墨分五色</h2>
            <p className="font-serif text-[#666666] italic text-lg">Five Shades of Ink</p>
            <div className="w-12 h-1 bg-[#1a1a1a]"></div>
            <p className="font-kai text-xl text-[#333333] leading-loose text-justify">
              墨本无色，因水而生神。焦、浓、重、淡、清，五色交织，绘尽世间万物。设计亦如运墨，在深浅变化中构建层次，在黑白交错间寻找平衡。
            </p>
          </div>

          {/* 右侧色卡展示 */}
          <div className="md:col-span-8 grid grid-cols-2 md:grid-cols-3 gap-6">
            {[
              { name: '焦墨', hex: '#1a1a1a', desc: 'Burnt Ink', class: 'bg-[#1a1a1a] text-white' },
              { name: '浓墨', hex: '#333333', desc: 'Thick Ink', class: 'bg-[#333333] text-white' },
              { name: '重墨', hex: '#4d4d4d', desc: 'Heavy Ink', class: 'bg-[#4d4d4d] text-white' },
              { name: '淡墨', hex: '#666666', desc: 'Light Ink', class: 'bg-[#666666] text-white' },
              { name: '清墨', hex: '#999999', desc: 'Clear Ink', class: 'bg-[#999999] text-[#1a1a1a]' },
              { name: '朱红', hex: '#C41E3A', desc: 'Vermilion', class: 'bg-[#C41E3A] text-white' },
            ].map((color, idx) => (
              <div key={idx} className="group relative aspect-[3/4] overflow-hidden rounded-sm cursor-pointer transition-all duration-700 hover:-translate-y-2">
                <div className={`absolute inset-0 ${color.class} transition-all duration-700 group-hover:scale-110`}></div>

                {/* 模拟墨水扩散效果 (SVG遮罩) */}
                <div className="absolute inset-0 opacity-0 group-hover:opacity-20 transition-opacity duration-500 bg-white filter blur-xl scale-50 group-hover:scale-150 rounded-full origin-center"></div>

                <div className="absolute bottom-0 left-0 p-6 w-full">
                  <div className="vertical-rl h-24 mb-4">
                     <span className="font-xing text-3xl tracking-widest">{color.name}</span>
                  </div>
                  <div className="border-t border-current opacity-30 w-full mb-2"></div>
                  <span className="font-serif text-xs opacity-70 tracking-widest block">{color.desc.toUpperCase()}</span>
                  <span className="font-mono text-xs opacity-50 block mt-1">{color.hex}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* 第三幕：字体美学 (Typography System) */}
      <section className="relative py-32 bg-[#FAF0E6] overflow-hidden">
        {/* 背景装饰：巨大的"书"字 */}
        <div className="absolute -right-20 top-20 text-[40rem] font-cao text-[#1a1a1a] opacity-[0.03] pointer-events-none select-none leading-none">
          书
        </div>

        <div className="max-w-7xl mx-auto px-8 relative z-10">
          <div className="flex flex-col md:flex-row justify-between items-end mb-24 border-b border-[#1a1a1a]/10 pb-8">
            <div>
               <h2 className="font-xing text-5xl mb-4">字体表情</h2>
               <p className="font-kai text-xl text-[#666666]">字如其人，形神兼备</p>
            </div>
            <div className="font-seal text-4xl text-[#C41E3A] opacity-80 mt-6 md:mt-0">笔歌墨舞</div>
          </div>

          <div className="space-y-24">

            {/* 1. 刘建毛草 */}
            <div className="group flex flex-col md:flex-row gap-12 items-center ink-spread-hover">
              <div className="w-full md:w-1/3 text-right order-2 md:order-1">
                <h3 className="font-serif font-bold text-lg mb-2">Liu Jian Mao Cao</h3>
                <p className="font-kai text-[#666666]">狂草风格，如疾风骤雨，适合展现力量与冲击力的主标题。</p>
              </div>
              <div className="w-full md:w-2/3 order-1 md:order-2">
                <div className="font-cao text-7xl md:text-8xl text-[#1a1a1a] leading-tight transition-all duration-500 group-hover:tracking-widest">
                  大江东去浪淘尽
                </div>
              </div>
            </div>

            {/* 2. 马善政 */}
            <div className="group flex flex-col md:flex-row gap-12 items-center">
              <div className="w-full md:w-2/3 text-right">
                <div className="font-xing text-6xl text-[#333333] leading-tight transition-all duration-500 group-hover:skew-x-6 origin-bottom">
                  明月几时有 把酒问青天
                </div>
              </div>
              <div className="w-full md:w-1/3">
                 <h3 className="font-serif font-bold text-lg mb-2">Ma Shan Zheng</h3>
                 <p className="font-kai text-[#666666]">行书风格，行云流水，端正而不失灵动，适用于副标题。</p>
              </div>
            </div>

            {/* 3. 智蟒行 */}
            <div className="group flex flex-col md:flex-row gap-12 items-center">
               <div className="w-full md:w-1/3 text-right order-2 md:order-1">
                <h3 className="font-serif font-bold text-lg mb-2">Zhi Mang Xing</h3>
                <p className="font-kai text-[#666666]">行草风格，笔意连绵，极富韵律感，适合诗词引用与装饰。</p>
              </div>
              <div className="w-full md:w-2/3 order-1 md:order-2 pl-8 border-l-2 border-[#C41E3A]">
                 <div className="font-xingcao text-4xl text-[#4d4d4d] leading-relaxed vertical-rl h-48">
                    采菊东篱下，悠然见南山。
                 </div>
              </div>
            </div>

            {/* 4. 站酷小薇 */}
            <div className="bg-white/60 p-8 rounded-sm shadow-sm border border-[#E5E5E5]">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                 <div>
                    <h3 className="font-serif font-bold text-lg mb-4 text-[#C41E3A]">ZCOOL XiaoWei (正文)</h3>
                    <p className="font-kai text-xl text-[#333333] leading-8 text-justify">
                      楷书风格，如端坐贤者。正文排版讲究疏朗，字间距略宽，行高宜大（leading-loose），以体现呼吸感。此处展示正文阅读体验，文字清晰工整，带有古典韵味，却不失现代可读性。
                    </p>
                 </div>
                 <div className="flex items-center justify-center">
                    <div className="w-32 h-32 border-4 border-[#1a1a1a] flex items-center justify-center rounded-full relative">
                        <span className="font-seal text-6xl text-[#1a1a1a]">圆融</span>
                        <div className="absolute -bottom-4 -right-4 w-12 h-12 bg-[#C41E3A] text-white font-seal flex items-center justify-center text-sm rounded-sm shadow-lg">
                           印章
                        </div>
                    </div>
                 </div>
              </div>
            </div>

          </div>
        </div>
      </section>

      {/* 第四幕：布局与留白 (Layout Demo) */}
      <section className="min-h-screen py-32 px-8 flex items-center justify-center relative">
        {/* 背景圆 */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[60vh] h-[60vh] rounded-full border border-[#999999] opacity-20 pointer-events-none"></div>
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[58vh] h-[58vh] rounded-full border border-[#999999] opacity-10 pointer-events-none transform rotate-45"></div>

        <div className="max-w-5xl w-full grid grid-cols-1 md:grid-cols-2 gap-16 items-center">
           {/* 图片/视觉占位 */}
           <div className="relative group cursor-pointer">
              <div className="aspect-[3/4] bg-[#e6e6e6] overflow-hidden relative grayscale hover:grayscale-0 transition-all duration-1000 ease-in-out">
                 {/* 模拟山水画效果 */}
                 <div className="absolute inset-0 bg-gradient-to-b from-transparent via-[#999999]/20 to-[#1a1a1a]/80"></div>
                 <div className="absolute bottom-0 w-full h-1/2 bg-[#1a1a1a] mask-image-gradient filter blur-md opacity-60 rounded-[50%] transform scale-150 translate-y-1/4"></div>
                 <div className="absolute bottom-10 right-10 w-32 h-32 bg-[#333333] rounded-full filter blur-xl opacity-80"></div>

                 {/* 居中文字 */}
                 <div className="absolute inset-0 flex items-center justify-center">
                    <span className="font-cao text-white text-6xl opacity-0 group-hover:opacity-100 transition-opacity duration-700 transform translate-y-4 group-hover:translate-y-0">
                       禅意
                    </span>
                 </div>
              </div>
              {/* 装饰线 */}
              <div className="absolute -top-4 -left-4 w-8 h-8 border-t-2 border-l-2 border-[#1a1a1a]"></div>
              <div className="absolute -bottom-4 -right-4 w-8 h-8 border-b-2 border-r-2 border-[#1a1a1a]"></div>
           </div>

           {/* 文字排版 */}
           <div className="space-y-12">
              <div className="flex gap-4">
                 <div className="w-1 h-16 bg-[#C41E3A]"></div>
                 <div>
                    <h2 className="font-xing text-4xl mb-2">留白之美</h2>
                    <span className="font-serif text-sm tracking-widest text-[#999999]">NEGATIVE SPACE</span>
                 </div>
              </div>

              <p className="font-kai text-xl leading-10 text-[#333333]">
                 画留三分白，生气随之发。界面设计中的留白不是空白，而是思维的延伸。
                 它引导视线，构建层级，赋予用户思考的空间。
              </p>

              <div className="flex gap-8 pt-8 border-t border-[#999999]/30">
                 <button className="group relative px-8 py-3 overflow-hidden border border-[#1a1a1a] transition-colors duration-300 hover:text-white">
                    <span className="relative z-10 font-xing text-xl">进入画境</span>
                    <div className="absolute inset-0 bg-[#1a1a1a] transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left"></div>
                 </button>
                 <button className="px-8 py-3 font-xing text-xl text-[#666666] hover:text-[#C41E3A] transition-colors flex items-center gap-2">
                    <Feather size={18} />
                    <span>更多作品</span>
                 </button>
              </div>
           </div>
        </div>
      </section>

      {/* 页脚 */}
      <footer className="bg-[#1a1a1a] text-[#999999] py-16 px-8 text-center relative overflow-hidden">
        <div className="relative z-10 flex flex-col items-center gap-8">
           <div className="w-16 h-16 bg-[#C41E3A] text-[#F8F5F0] flex items-center justify-center rounded-sm shadow-[0_0_20px_rgba(196,30,58,0.5)]">
              <span className="font-seal text-3xl">墨</span>
           </div>
           <p className="font-kai text-lg tracking-widest opacity-80">传承东方美学，重塑数字体验</p>
           <div className="flex gap-6 font-serif text-sm opacity-50 mt-8">
              <span>© 2023 INK REALM UI</span>
              <span>•</span>
              <span>DESIGNED BY GEMINI</span>
           </div>
        </div>

        {/* 页脚装饰雾气 */}
        <div className="absolute bottom-0 left-0 w-full h-full pointer-events-none opacity-10 mix-blend-screen">
            <div className="absolute bottom-[-50%] left-[-20%] w-[80%] h-[80%] bg-gradient-to-r from-transparent via-white to-transparent rounded-full filter blur-[100px] animate-pulse"></div>
        </div>
      </footer>
    </div>
  );
}
