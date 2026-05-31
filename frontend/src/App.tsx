import React from 'react'
import Chat from './components/Chat'
import NavBar from './components/NavBar'

export default function App(): JSX.Element {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-800 text-slate-50">
      <NavBar />

      <div className="pt-20 pb-36">
        <div className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-6xl flex-col px-4 py-4">
          <main className="flex-1">
            <Chat />
          </main>
          <footer className="mt-6 text-center text-sm text-slate-400">Powered by Smart Store Traffic Analyzer</footer>
        </div>
      </div>
    </div>
  )
}
