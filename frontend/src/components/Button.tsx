import React from 'react'

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  loading?: boolean
  variant?: 'primary' | 'secondary'
  size?: 'sm' | 'md'
}

export default function Button({ loading, variant = 'primary', size = 'md', children, className, ...rest }: ButtonProps) {
  const base = 'rounded-full font-semibold transition inline-flex items-center justify-center'
  const sz = size === 'sm' ? 'px-3 py-1.5 text-xs' : 'px-5 py-3 text-sm'
  const v = variant === 'primary' ? 'bg-emerald-400 text-slate-950 hover:bg-emerald-300' : 'bg-indigo-500 text-white hover:bg-indigo-400'
  const disabled = rest.disabled ? 'opacity-70 cursor-not-allowed' : ''
  return (
    <button className={`${base} ${sz} ${v} ${disabled} ${className ?? ''}`} {...rest}>
      {loading ? 'Thinking...' : children}
    </button>
  )
}
