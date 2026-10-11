/** Authenticate a native TUI process without exporting the human password. */
export async function loginWithPassword(loginUrl: string, password: string): Promise<string> {
  let statusResponse: Response | null = null
  try {
    const statusUrl = new URL("/auth/status", loginUrl).toString()
    statusResponse = await fetch(statusUrl, { cache: "no-store" })
  } catch {
    // Login below reports the actionable connection failure.
  }
  if (statusResponse?.ok) {
    let status: unknown = null
    try {
      status = await statusResponse.json()
    } catch {
      // Login below reports malformed/unsupported status responses.
    }
    if (status && typeof status === "object" && "configured" in status
      && (status as { configured?: unknown }).configured === false) {
      throw new Error("instance password is not initialized; run `nanobot auth init` on the gateway host")
    }
  }
  let response: Response
  try {
    response = await fetch(loginUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ password }),
      cache: "no-store",
    })
  } catch {
    throw new Error("gateway login request failed")
  }
  if (!response.ok) {
    throw new Error(`gateway login failed: HTTP ${response.status}`)
  }
  let payload: unknown
  try {
    payload = await response.json()
  } catch {
    throw new Error("gateway login response is invalid")
  }
  if (!payload || typeof payload !== "object" || !("session_id" in payload)) {
    throw new Error("gateway login response is invalid")
  }
  const sessionId = (payload as { session_id?: unknown }).session_id
  if (typeof sessionId !== "string" || !sessionId) {
    throw new Error("gateway login response is invalid")
  }
  return `percival_session=${sessionId}`
}

/** Read a password without terminal echo before the renderer enters raw mode. */
export async function promptInstancePassword(): Promise<string> {
  const input = process.stdin
  if (!input.isTTY || !process.stdout.isTTY) {
    throw new Error("instance password requires an interactive terminal")
  }
  const wasRaw = input.isRaw
  input.setRawMode(true)
  input.setEncoding("utf8")
  input.resume()
  process.stdout.write("Instance password: ")

  return await new Promise<string>((resolve, reject) => {
    let value = ""
    let settled = false
    const finish = (error?: Error) => {
      if (settled) return
      settled = true
      input.off("data", onData)
      input.setRawMode(wasRaw)
      process.stdout.write("\n")
      if (error) reject(error)
      else resolve(value)
    }
    const onData = (chunk: string | Buffer) => {
      const text = typeof chunk === "string" ? chunk : chunk.toString("utf8")
      for (const character of text) {
        if (character === "\u0003") {
          finish(new Error("login cancelled"))
          return
        }
        if (character === "\r" || character === "\n") {
          finish()
          return
        }
        if (character === "\u007f" || character === "\b") {
          value = Array.from(value).slice(0, -1).join("")
        } else if (character === "\u0015") {
          value = ""
        } else if (character >= " ") {
          value += character
        }
      }
    }
    input.on("data", onData)
  })
}
