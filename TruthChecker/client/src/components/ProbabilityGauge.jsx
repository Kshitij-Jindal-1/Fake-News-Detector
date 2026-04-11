import React, { useState, useEffect, useRef } from 'react';
import { useTheme } from '../context/ThemeContext';

/**
 * ProbabilityGauge Component
 *
 * Displays a semicircular gauge that fills based on probability.
 * Features:
 * - Animated count-up from 0 to final value
 * - Confetti effect for high TRUE scores (>70%)
 * - Shake effect for high FAKE scores (<30%)
 */
const ProbabilityGauge = ({ probability, confidenceLabel }) => {
  const { theme } = useTheme();
  const [animatedValue, setAnimatedValue] = useState(0);
  const [showConfetti, setShowConfetti] = useState(false);
  const [showShake, setShowShake] = useState(false);
  const animationRef = useRef(null);
  const startTimeRef = useRef(null);

  // Animate the value counting up
  useEffect(() => {
    setAnimatedValue(0);
    setShowConfetti(false);
    setShowShake(false);
    startTimeRef.current = null;

    const duration = 1500; // 1.5 seconds

    const animate = (timestamp) => {
      if (!startTimeRef.current) startTimeRef.current = timestamp;
      const elapsed = timestamp - startTimeRef.current;
      const progress = Math.min(elapsed / duration, 1);

      // Ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      const currentValue = eased * probability;
      setAnimatedValue(currentValue);

      if (progress < 1) {
        animationRef.current = requestAnimationFrame(animate);
      } else {
        // Animation complete — trigger effects
        if (probability > 0.7) {
          setShowConfetti(true);
          setTimeout(() => setShowConfetti(false), 3000);
        } else if (probability < 0.3) {
          setShowShake(true);
          setTimeout(() => setShowShake(false), 800);
        }
      }
    };

    animationRef.current = requestAnimationFrame(animate);
    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [probability]);

  const percentage = Math.round(animatedValue * 100);
  const fillAngle = animatedValue * 180;

  const getColor = () => {
    const isLight = theme === 'light';
    if (animatedValue < 0.4) return isLight ? '#dc2626' : '#ef4444'; // Red 600 : Red 500
    if (animatedValue < 0.6) return isLight ? '#d97706' : '#eab308'; // Amber 600 : Yellow 500
    return isLight ? '#16a34a' : '#22c55e'; // Green 600 : Green 500
  };

  const color = getColor();

  const describeArc = (cx, cy, radius, startAngle, endAngle) => {
    if (endAngle <= startAngle) return '';
    const start = polarToCartesian(cx, cy, radius, startAngle);
    const end = polarToCartesian(cx, cy, radius, endAngle);
    const largeArcFlag = endAngle - startAngle > 180 ? "1" : "0";
    return [
      "M", start.x, start.y,
      "A", radius, radius, 0, largeArcFlag, 1, end.x, end.y
    ].join(" ");
  };

  const polarToCartesian = (cx, cy, radius, angleInDegrees) => {
    const angleInRadians = (angleInDegrees - 180) * Math.PI / 180.0;
    return {
      x: cx + (radius * Math.cos(angleInRadians)),
      y: cy + (radius * Math.sin(angleInRadians))
    };
  };

  const cx = 100;
  const cy = 100;
  const radius = 80;
  const strokeWidth = 20;

  // Generate confetti particles
  const confettiParticles = showConfetti ? Array.from({ length: 30 }, (_, i) => ({
    id: i,
    left: `${Math.random() * 100}%`,
    delay: `${Math.random() * 0.5}s`,
    duration: `${1.5 + Math.random() * 1.5}s`,
    color: ['#22c55e', '#52C41A', '#86efac', '#fbbf24', '#60a5fa'][Math.floor(Math.random() * 5)],
    size: 4 + Math.random() * 6,
  })) : [];

  return (
    <div className={`flex flex-col items-center py-6 relative overflow-hidden ${showShake ? 'animate-shake' : ''}`}>

      {/* Confetti */}
      {showConfetti && (
        <div className='absolute inset-0 pointer-events-none overflow-hidden'>
          {confettiParticles.map(p => (
            <div
              key={p.id}
              className='absolute top-0 animate-confetti rounded-sm'
              style={{
                left: p.left,
                animationDelay: p.delay,
                animationDuration: p.duration,
                backgroundColor: p.color,
                width: `${p.size}px`,
                height: `${p.size}px`,
              }}
            />
          ))}
        </div>
      )}

      {/* Gauge SVG */}
      <div className='relative'>
        <svg width="200" height="120" viewBox="0 0 200 120">
          {/* Background track */}
          <path
            d={describeArc(cx, cy, radius, 0, 180)}
            fill="none"
            stroke="var(--gauge-track)"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />

          {/* Filled portion */}
          {fillAngle > 0 && (
            <path
              d={describeArc(cx, cy, radius, 0, fillAngle)}
              fill="none"
              stroke={color}
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              style={{
                filter: `drop-shadow(0 0 6px ${color}40)`,
              }}
            />
          )}

          {/* Needle */}
          <g transform={`rotate(${fillAngle}, ${cx}, ${cy})`}>
            <line
              x1={cx}
              y1={cy}
              x2={cx - radius + 10}
              y2={cy}
              stroke="var(--text-primary)"
              strokeWidth="3"
              strokeLinecap="round"
            />
          </g>

          {/* Center circle */}
          <circle cx={cx} cy={cy} r="8" fill={color} style={{ filter: `drop-shadow(0 0 4px ${color}60)` }} />
        </svg>
      </div>

      {/* Percentage display */}
      <div
        className='text-4xl font-bold mt-2 transition-colors duration-300'
        style={{ color }}
      >
        {percentage}%
      </div>

      {/* Label */}
      <div className='text-[var(--text-secondary)] text-sm mt-1'>
        Likelihood of being TRUE
      </div>

      {/* Confidence badge */}
      <div
        className='mt-4 px-4 py-2 rounded-lg text-sm font-medium'
        style={{
          backgroundColor: `${color}20`,
          color: color,
          border: `1px solid ${color}`
        }}
      >
        {confidenceLabel}
      </div>

      {/* Legend */}
      <div className='flex gap-4 mt-4 text-xs text-[var(--text-muted)]'>
        <div className='flex items-center gap-1'>
          <div className='w-3 h-3 rounded-full bg-red-500' />
          <span>0-40%</span>
        </div>
        <div className='flex items-center gap-1'>
          <div className='w-3 h-3 rounded-full bg-yellow-500' />
          <span>40-60%</span>
        </div>
        <div className='flex items-center gap-1'>
          <div className='w-3 h-3 rounded-full bg-green-500' />
          <span>60-100%</span>
        </div>
      </div>
    </div>
  );
};

export default ProbabilityGauge;
