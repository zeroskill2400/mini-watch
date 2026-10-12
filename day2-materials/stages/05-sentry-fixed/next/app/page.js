"use client";

import { useEffect, useState } from "react";

async function readMessages() {
  const response = await fetch("/api/messages", { cache: "no-store" });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "목록을 읽지 못했습니다.");
  return data.messages;
}

export default function Home() {
  const [messages, setMessages] = useState([]);
  const [content, setContent] = useState("");
  const [notice, setNotice] = useState("목록을 불러오는 중입니다.");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let active = true;
    readMessages()
      .then((rows) => { if (active) { setMessages(rows); setNotice(""); } })
      .catch((error) => { if (active) setNotice(error.message); });
    return () => { active = false; };
  }, []);

  async function refresh() {
    setBusy(true);
    try {
      setMessages(await readMessages());
      setNotice("목록을 새로 불러왔습니다.");
    } catch (error) {
      setNotice(error.message);
    } finally {
      setBusy(false);
    }
  }

  async function save(event) {
    event.preventDefault();
    setBusy(true);
    setNotice("저장 중입니다. 서버 첫 응답은 늦을 수 있습니다.");
    try {
      const response = await fetch("/api/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "저장하지 못했습니다.");
      setMessages((rows) => [data, ...rows]);
      setContent("");
      setNotice(`저장 완료: ${data.id}번`);
    } catch (error) {
      setNotice(error.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main>
      <h1>메시지 보관함</h1>
      <p>메시지를 남기고 저장된 목록을 확인하세요.</p>
      <form onSubmit={save}>
        <label htmlFor="content">메시지</label>
        <input id="content" value={content} maxLength={200} required
          onChange={(event) => setContent(event.target.value)} />
        <button disabled={busy}>저장</button>
      </form>
      <p role="status">{notice}</p>
      <button type="button" onClick={refresh} disabled={busy}>목록 새로고침</button>
      <ul>{messages.map((message) => (
        <li key={message.id}><strong>{message.id}번</strong> {message.content}</li>
      ))}</ul>
    </main>
  );
}
