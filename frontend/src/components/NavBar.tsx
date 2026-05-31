import React from 'react'

export default function NavBar(): JSX.Element {
  return (
    <div className="fixed inset-x-0 top-0 z-30 border-b border-slate-800 bg-slate-950/95 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 text-slate-50">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-2xl bg-emerald-400 text-slate-950 grid place-items-center font-bold">S</div>
          <div>
            <div className="text-base font-semibold">Smart Traffic Chat</div>
            <div className="text-xs text-slate-400">Retail root-cause analyzer</div>
          </div>
        </div>
        <div className="flex items-center gap-3 text-sm text-slate-300">
          <button className="rounded-full bg-slate-800/80 px-3 py-2 hover:bg-slate-700">Open</button>
          <button className="rounded-full bg-slate-800/80 px-3 py-2 hover:bg-slate-700">History</button>
        </div>
      </div>
    </div>
  )
}
