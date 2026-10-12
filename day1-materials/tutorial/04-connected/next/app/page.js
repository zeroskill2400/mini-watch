import { Suspense } from "react";
import { connection } from "next/server";

async function Messages() {
  await connection();
  const response = await fetch(`${process.env.API_URL}/api/messages`, {
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error(`Flask 응답 오류: ${response.status}`);
  }
  const data = await response.json();
  return (
    <ul>
      {data.messages.map((message) => (
        <li key={message}>{message}</li>
      ))}
    </ul>
  );
}

export default function Home() {
  return (
    <main>
      <h1>Next.js → Flask → PostgreSQL</h1>
      <p>Next.js 서버가 Flask의 응답을 받아 만든 화면입니다.</p>
      <Suspense fallback={<p>문장을 불러오는 중입니다.</p>}>
        <Messages />
      </Suspense>
    </main>
  );
}
