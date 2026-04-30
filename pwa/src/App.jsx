import { useEffect, useState } from "react"
import { supabase } from "./lib/supabase"

function App() {
  const [status, setStatus] = useState("connecting...")

  useEffect(() => {
    async function test() {
      // Try fetching from a table that exists (may be empty)
      const { data, error } = await supabase.from('signals').select('id', { count: 'exact' })
      if (error) setStatus("Error: " + error.message)
      else setStatus(`Connected! Signals count: ${data.length}`)
    }
    test()
  }, [])

  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1>🚀 MemTrack Sniper</h1>
      <p>Supabase status: {status}</p>
    </div>
  )
}

export default App