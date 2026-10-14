"use client";
import { useState } from "react";
import { requestJson } from "../api/client";

export default function AnalysisClient() {
  const [report, setReport] = useState(null);
  const [source, setSource] = useState("all");
  const [errorsOnly, setErrorsOnly] = useState(false);
  const [message, setMessage] = useState("");
  async function load() {
    setReport(null);
    try {
      const data = await requestJson("/api/analysis");
      setReport(data);
      setMessage(data.ready ? "두 출처의 로그를 불러왔습니다." : data.message);
    } catch (error) { setMessage(error.message); }
  }
  const visibleEvents = (report?.events || []).filter(event =>
    (source === "all" || event.source === source) && (!errorsOnly || event.status_code >= 400)
  );
  return <section aria-label="통합 로그">
    <h2>통합 로그</h2>
    <p>실제 요청 2건을 Flask와 Nginx가 각각 기록한 case.json을 읽습니다. 관측 4행은 요청 4건이 아닙니다.</p>
    <button onClick={load}>통합 로그 불러오기</button>
    <p role="status">{message}</p>
    {report?.ready && <>
      <p>전체 관측: {report.total_count} / 오류 관측: {report.error_count}</p>
      <label>출처<select aria-label="출처" value={source} onChange={event => setSource(event.target.value)}>
        <option value="all">전체</option><option value="app">app</option><option value="nginx">nginx</option>
      </select></label>
      <label style={{display:"flex",alignItems:"center",gap:"0.5rem"}}><input style={{width:"auto",margin:0}} type="checkbox" checked={errorsOnly} onChange={event => setErrorsOnly(event.target.checked)} />오류만 보기</label>
      <p>표시 관측: {visibleEvents.length}</p>
      <div style={{overflowX:"auto"}}>
        <table style={{borderSpacing:"0.75rem 0.4rem",textAlign:"left",whiteSpace:"nowrap"}}><thead><tr><th>ID</th><th>출처</th><th>시각(UTC)</th><th>방법</th><th>경로</th><th>상태</th><th>원본</th></tr></thead>
          <tbody>{visibleEvents.map(event => <tr key={event.id}>
            <td>{event.id}</td><td>{event.source}</td><td>{event.time ?? "원본에 없음"}</td>
            <td>{event.method}</td><td>{event.path}</td><td>{event.status_code}</td>
            <td><details><summary>원본 보기</summary><pre style={{whiteSpace:"pre-wrap",overflowWrap:"anywhere"}}>{typeof event.raw === "string" ? event.raw : JSON.stringify(event.raw, null, 2)}</pre></details></td>
          </tr>)}</tbody>
        </table>
      </div>
    </>}
    <p>SIEM의 수집·정규화·통합 조회 일부를 구현합니다. 공격 판정·자동 차단·XDR 탐지 기능은 아닙니다.</p>
  </section>;
}
