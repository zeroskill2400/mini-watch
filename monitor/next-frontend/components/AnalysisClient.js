"use client";
import { useState } from "react";
import { requestJson } from "../api/client";
export default function AnalysisClient() {
  const [afterId, setAfterId] = useState(null);
  const [threshold, setThreshold] = useState(10);
  const [report, setReport] = useState(null);
  const [message, setMessage] = useState("");
  async function start() {
    try {
      const state = await requestJson("/api/analysis/start");
      setAfterId(state.after_id); setReport(null);
      setMessage("기존 기록을 지우지 않고 새 관찰을 시작했습니다. 일반 목록을12회 조회한 뒤1분 안에 분석해 주세요.");
    } catch (e) { setMessage(e.message); }
  }
  async function load() {
    try {
      const sameWindow = report?.reference_time ? `&reference_time=${encodeURIComponent(report.reference_time)}` : "";
      const data = await requestJson(`/api/analysis?after_id=${afterId}&threshold=${threshold}${sameWindow}`);
      setReport(data); setMessage(data.ready ? "출처별 결과를 불러왔습니다. 같은 관찰 구간을 유지하며 기준을 비교합니다." : data.message);
    } catch (e) { setMessage(e.message); }
  }
  return <section aria-label="분석 결과">
    <h2>분석 결과</h2>
    <button onClick={start}>새 관찰 시작</button>
    <label>HTTP 조회 기준<input aria-label="HTTP 조회 기준" type="number" min="1" max="100" value={threshold} onChange={e => setThreshold(e.target.value)} /></label>
    <button onClick={load} disabled={afterId === null}>분석 결과 불러오기</button>
    <p role="status">{message}</p>
    {afterId !== null && <p>시작ID: {afterId} / 이후 기록·첫 결과 조회시각의 최근60초 / 시각은 감시DB 수신 기준</p>}
    {report?.ready && <p>관찰 기준시각: {report.reference_time} / 새 관찰 시작 전까지 이 구간을 유지합니다.</p>}
    {report?.ready && report.results.map(item => <article key={item.rule} style={{border:"1px solid #bbb",padding:"1rem",margin:"1rem 0"}}>
      <h3>{item.rule}</h3><p>출처: {item.source}</p>
      <p>관찰값: {item.observed} / {item.triggered ? "검토 후보" : "기준 미해당"}</p>
      <p>기준: {item.basis}</p><p>{item.reason}</p>
      <details><summary>근거 보기</summary><p>{item.evidence.length ? item.evidence.join(", ") : "해당 근거 없음"}</p></details>
    </article>)}
    <p>독립된 자료의 결과를 출처별로 표시합니다. 후보 표시만으로 침해를 확정하거나 자동 조치하지 않습니다.</p>
  </section>;
}
