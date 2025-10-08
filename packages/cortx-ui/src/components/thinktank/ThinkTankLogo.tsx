"use client"

export interface ThinkTankLogoProps {
  size?: 'sm' | 'md' | 'lg'
  className?: string
  id?: string
}

/**
 * Two-tone ThinkTank Logo Component
 * Displays "ThinkTank" with "Think" in teal and "Tank" in white
 */
export function ThinkTankLogo({
  size = 'lg',
  className = '',
  id
}: ThinkTankLogoProps) {
  const sizeClasses = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-4xl'
  }

  return (
    <div
      id={id}
      className={`font-heading font-semibold tracking-tight leading-none ${sizeClasses[size]} ${className}`}
    >
      <span className="text-sinergy-teal font-bold">Think</span>
      <span className="text-white font-bold">Tank</span>
    </div>
  )
}
