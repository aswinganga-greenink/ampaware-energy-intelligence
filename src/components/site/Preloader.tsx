import { useEffect, useRef, useState } from "react";
import { Zap } from "lucide-react";

export function Preloader() {
  const [isComplete, setIsComplete] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const svgWrapperRef = useRef<HTMLDivElement>(null);
  const textRef = useRef<HTMLDivElement>(null);
  const barRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Only play once per session to avoid annoying the user on every reload
    if (sessionStorage.getItem('ampaware_preloaded')) {
      setIsComplete(true);
      return;
    }

    // Dynamically import animejs only on the client to avoid SSR export errors
    import("animejs").then((module) => {
      const anime = module.default || module;
      const tl = anime.timeline({
        easing: 'easeOutExpo',
      });

      // Extract paths from Lucide icon dynamically for drawing
      const paths = svgWrapperRef.current?.querySelectorAll('path');
      if (paths) {
        tl.add({
          targets: paths,
          strokeDashoffset: [anime.setDashoffset, 0],
          easing: 'easeInOutSine',
          duration: 1500,
          delay: function(el: any, i: number) { return i * 300 },
        });
      }

      // Fade in text and glow
      tl.add({
        targets: [textRef.current, barRef.current],
        opacity: [0, 1],
        translateY: [20, 0],
        duration: 1200,
        easing: 'easeOutQuad'
      }, '-=800')
      // Fill the progress bar
      .add({
        targets: barRef.current?.querySelector('.progress-fill'),
        width: ['0%', '100%'],
        easing: 'easeInOutQuart',
        duration: 1200,
      }, '-=600')
      // Final fade out of the entire loading screen instead of sliding up
      .add({
        targets: containerRef.current,
        opacity: [1, 0],
        scale: [1, 1.05],
        easing: 'easeInOutSine',
        duration: 1200,
        complete: () => {
          sessionStorage.setItem('ampaware_preloaded', 'true');
          setIsComplete(true);
        }
      }, '-=300');
    });

  }, []);

  if (isComplete) return null;

  return (
    <div 
      ref={containerRef}
      className="fixed inset-0 z-[99999] flex flex-col items-center justify-center bg-background text-foreground overflow-hidden"
    >
      {/* Dynamic Backgrounds matching Hero */}
      <div className="absolute inset-0 -z-10 bg-gradient-hero" />
      <div className="absolute inset-0 -z-10 grid-pattern opacity-30" />
      <div className="absolute -left-40 top-20 -z-10 h-96 w-96 rounded-full bg-primary/30 blur-3xl" />
      <div className="absolute -right-32 bottom-0 -z-10 h-96 w-96 rounded-full bg-success/20 blur-3xl" />
      
      {/* SVG Icon */}
      <div ref={svgWrapperRef} className="mb-8 relative">
        <div className="absolute inset-0 blur-xl bg-primary/40 rounded-full opacity-50 scale-150 animate-pulse" />
        <Zap 
          className="h-20 w-20 text-primary relative z-10" 
          strokeWidth={1}
          style={{ strokeDasharray: '400', strokeDashoffset: '400' }} // Prepare for AnimeJS
        />
      </div>

      {/* Loading Text */}
      <div ref={textRef} className="text-xl font-medium tracking-[0.3em] text-foreground mb-6 opacity-0">
        AMPAWARE
      </div>

      {/* Progress bar */}
      <div ref={barRef} className="w-64 h-[2px] bg-foreground/10 rounded-full overflow-hidden opacity-0">
        <div className="progress-fill h-full bg-primary relative">
          <div className="absolute inset-0 bg-white/50 blur-[2px]" />
        </div>
      </div>
    </div>
  );
}
