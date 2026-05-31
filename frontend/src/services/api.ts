export async function postChat(baseUrl: string, query: string): Promise<any> {
  const url = `${baseUrl.replace(/\/$/, '')}/chat`
  const resp = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
  })
  if (!resp.ok) {
    const text = await resp.text()
    throw new Error(`HTTP ${resp.status}: ${text}`)
  }
  return resp.json()
}

export async function postChatSql(baseUrl: string, query: string): Promise<any> {
  // Calls a backend endpoint that should return SQL for the given query if implemented.
  const url = `${baseUrl.replace(/\/$/, '')}/chat/sql`
  const resp = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query })
  })
  if (!resp.ok) {
    // if endpoint not implemented, surface a readable message
    const text = await resp.text()
    throw new Error(`HTTP ${resp.status}: ${text}`)
  }
  return resp.json()
}

export async function getHealth(baseUrl: string): Promise<any> {
  const url = `${baseUrl.replace(/\/$/, '')}/health`
  const resp = await fetch(url)
  if (!resp.ok) throw new Error('Health check failed')
  return resp.json()
}
