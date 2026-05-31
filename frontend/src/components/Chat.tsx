import React, { useState, useEffect, useRef } from 'react'
import { postChat, postChatSql } from '../services/api'
import BottomBar from './BottomBar'
import Button from './Button'

type Message = { role: 'user' | 'assistant'; text: string; intent?: string; query?: string; hasSql?: boolean; sql?: string; sqlLoading?: boolean }

function ChatMessage({ m, onShowSql }: { m: Message; onShowSql?: () => void }) {
  return (
    <div className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-xl p-3 rounded-xl ${m.role === 'user' ? 'bg-teal-400 text-slate-900' : 'bg-slate-700 text-slate-100'}`}>
        <div className="text-xs text-slate-300 mb-1">{m.role === 'user' ? 'You' : 'Assistant'}</div>
        <div className="whitespace-pre-wrap">{m.text}</div>
        {m.intent && <div className="mt-2 text-xs text-slate-300">Intent: <strong>{m.intent}</strong></div>}
        {m.role === 'assistant' && (m.hasSql || m.sql) && (
          <div className="mt-4 flex flex-col gap-2">
            {!m.sql ? (
              <div className="flex justify-end">
                <Button size="sm" variant="secondary" onClick={onShowSql} disabled={m.sqlLoading}>
                  {m.sqlLoading ? 'Loading SQL...' : 'Show SQL'}
                </Button>
              </div>
            ) : null}
            {m.sql && (
              <div className="rounded-2xl bg-slate-800 p-3 text-sm text-slate-200">
                <div className="text-xs text-slate-400 mb-2">SQL</div>
                <pre className="whitespace-pre-wrap">{m.sql}</pre>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default function Chat(): JSX.Element {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  const bottomRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), [messages])

  useEffect(() => { /* no-op */ }, [])

  async function send() {
    if (!input.trim()) return
    const text = input.trim()
    setMessages(prev => [...prev, { role: 'user', text }])
    setInput('')
    setLoading(true)
    try {
      const res = await postChat(baseUrl, text)
      setMessages(prev => [...prev, {
        role: 'assistant',
        text: res.response || 'No response',
        intent: res.intent,
        query: text,
        hasSql: Boolean(res.sql),
        sql: res.sql ?? undefined,
      }])
    } catch (err: any) {
      setMessages(prev => [...prev, { role: 'assistant', text: 'Error: ' + (err.message || String(err)), query: text }])
    } finally {
      setLoading(false)
    }
  }

  function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      send()
    }
  }

  async function fetchSqlForMessage(index: number) {
    setMessages(prev => prev.map((m, idx) => idx === index ? { ...m, sqlLoading: true } : m))
    const message = messages[index]
    if (!message?.query) return

    try {
      const r = await postChatSql(baseUrl, message.query)
      setMessages(prev => prev.map((m, idx) => idx === index ? { ...m, sql: r?.sql ?? 'SQL not available from backend', sqlLoading: false } : m))
    } catch (e: any) {
      setMessages(prev => prev.map((m, idx) => idx === index ? { ...m, sql: 'SQL request failed: ' + (e.message || String(e)), sqlLoading: false } : m))
    }
  }

  return (
    <div className="flex h-full flex-col rounded-[28px] border border-slate-800 bg-slate-950/80 shadow-2xl overflow-hidden">
      <div className="border-b border-slate-800 px-6 py-5 bg-slate-950/95">
        <div className="text-sm uppercase tracking-[0.24em] text-slate-400">Assistant</div>
        <div className="mt-2 text-lg font-semibold">Retail traffic root-cause analysis</div>
      </div>

      <div className="flex-1 overflow-hidden">
        <div className="h-full overflow-y-auto px-6 py-5 pb-40 space-y-4 bg-slate-950">
          {messages.map((m, i) => (
            <React.Fragment key={i}>
              <ChatMessage m={m} onShowSql={m.role === 'assistant' ? () => fetchSqlForMessage(i) : undefined} />
              {loading && i === messages.length - 1 && m.role === 'user' ? (
                <div className="flex justify-end">
                  <div className="max-w-xl rounded-2xl border border-slate-800 bg-slate-900/80 px-4 py-2 text-sm text-slate-400 italic">
                    Thinking...
                  </div>
                </div>
              ) : null}
            </React.Fragment>
          ))}
          <div ref={bottomRef}></div>
        </div>
      </div>

      <BottomBar>
        <div className="mb-4 flex flex-col gap-3">
          <textarea className="min-h-[80px] w-full resize-y rounded-2xl border border-slate-800 bg-slate-950 px-4 py-3 text-slate-100 placeholder:text-slate-500 focus:border-cyan-400 focus:outline-none focus:ring-2 focus:ring-cyan-500/20" value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKeyDown} placeholder={messages.length === 0 ? 'What is the total sales?' : ''} />
          <div className="flex justify-end">
              <Button onClick={send} disabled={loading} aria-label="Send message">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 19l9-7-9-7-2 4-6 1 8 9z" />
              </svg>
            </Button>
          </div>
        </div>
      </BottomBar>
    </div>
  )
}
