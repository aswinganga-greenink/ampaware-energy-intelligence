let audioCtx: AudioContext | null = null;

function getContext() {
  if (!audioCtx) {
    audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
  }
  if (audioCtx.state === 'suspended') {
    audioCtx.resume();
  }
  return audioCtx;
}

// Generates a very short, crisp mechanical "tick" or "thud" by rapidly sweeping frequency down
function playClickSound(startFreq: number, endFreq: number, duration: number, vol: number) {
  try {
    const ctx = getContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = 'sine';
    
    // Frequency sweep for tactile feel
    osc.frequency.setValueAtTime(startFreq, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(endFreq, ctx.currentTime + duration);
    
    // Fast envelope
    gain.gain.setValueAtTime(vol, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start();
    osc.stop(ctx.currentTime + duration + 0.01);
  } catch (e) {
    // Ignore errors if audio context is not allowed yet
  }
}

// Generates a very soft, pure-tone sweep (no noise, very smooth)
function playSubtleSweep(duration: number, maxVol: number) {
  try {
    const ctx = getContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    // Sine wave produces the cleanest, least "noisy" sound possible
    osc.type = 'sine';
    
    // Sweep pitch down gently in the low-mid register
    osc.frequency.setValueAtTime(300, ctx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(150, ctx.currentTime + duration);
    
    // Smooth envelope: soft attack, exponential decay
    gain.gain.setValueAtTime(0, ctx.currentTime);
    gain.gain.linearRampToValueAtTime(maxVol, ctx.currentTime + duration * 0.3);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + duration);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start();
    osc.stop(ctx.currentTime + duration + 0.05);
  } catch (e) {
  }
}

export function playHover() {
  // Extremely subtle sine sweep (barely audible, just tactile)
  playSubtleSweep(0.12, 0.004);
}

export function playClick() {
  // A deeper, more solid tactile "thud" or "click"
  playClickSound(800, 100, 0.02, 0.015);
}

export function initSounds() {
  if (typeof window === 'undefined') return;

  const handleMouseOver = (e: MouseEvent) => {
    const target = e.target as HTMLElement;
    if (target.tagName === 'BUTTON' || target.tagName === 'A' || target.closest('button') || target.closest('a')) {
      playHover();
    }
  };

  const handleClick = (e: MouseEvent) => {
    const target = e.target as HTMLElement;
    if (target.tagName === 'BUTTON' || target.tagName === 'A' || target.closest('button') || target.closest('a')) {
      playClick();
    }
  };

  document.addEventListener('mouseover', handleMouseOver);
  document.addEventListener('mousedown', handleClick);

  return () => {
    document.removeEventListener('mouseover', handleMouseOver);
    document.removeEventListener('mousedown', handleClick);
  };
}
