import React from 'react'

export default function BottomBar({ children }: { children: React.ReactNode }): JSX.Element {
  return (
    <div className="fixed inset-x-0 bottom-4 z-40 flex justify-center pointer-events-none">
      <div className="w-full max-w-6xl px-6 pointer-events-auto">
        <div className="rounded-2xl bg-slate-900/95 backdrop-blur-md border border-slate-800 p-4 shadow-2xl">
          {children}
        </div>
      </div>
    </div>
  )
}
