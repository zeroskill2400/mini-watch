async function forward(method, body) {
  try {
    const base = process.env.API_BASE;
    if (!base) throw new Error("API_BASE를 설정하세요.");
    const response = await fetch(new URL("/api/messages", base), {
      method,
      cache: "no-store",
      headers: { "Content-Type": "application/json" },
      body,
      signal: AbortSignal.timeout(90000),
    });
    const data = await response.json();
    return Response.json(data, { status: response.status });
  } catch (error) {
    console.error("Flask 요청 실패:", error.message);
    return Response.json(
      { error: "API에 연결하지 못했습니다. 잠시 뒤 목록을 새로고침하세요." },
      { status: 502 },
    );
  }
}

export async function GET() {
  return forward("GET");
}

export async function POST(request) {
  return forward("POST", await request.text());
}
