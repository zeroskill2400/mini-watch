"use client";
import { useState } from "react";
import { requestJson } from "../api/client";

const emptyMessage = "general에서 로그인하거나 페이지를 연 뒤 다시 불러오세요.";

function RawLogList({ entries, source }) {
  if (entries.length === 0) return <p>{emptyMessage}</p>;
  return <ol className="raw-log-list">
    {entries.map((entry, index) => <li key={index}>
      <span className="log-label">{source} 원본 {index + 1}행</span>
      <pre>{typeof entry === "string" ? entry : JSON.stringify(entry, null, 2)}</pre>
    </li>)}
  </ol>;
}

export default function AnalysisClient() {
  const [rawLogs, setRawLogs] = useState(null);
  const [report, setReport] = useState(null);
  const [source, setSource] = useState("all");
  const [errorsOnly, setErrorsOnly] = useState(false);
  const [rawMessage, setRawMessage] = useState("");
  const [reportMessage, setReportMessage] = useState("");
  const [loadingRaw, setLoadingRaw] = useState(false);
  const [loadingReport, setLoadingReport] = useState(false);

  async function loadRaw() {
    setLoadingRaw(true);
    setRawLogs(null);
    setReport(null);
    setReportMessage("");
    try {
      const data = await requestJson("/api/analysis/raw");
      setRawLogs(data);
      setRawMessage(data.app.length + data.nginx.length > 0
        ? "현재 원본 로그를 불러왔습니다."
        : emptyMessage);
    } catch (error) {
      setRawMessage(error.message);
    } finally {
      setLoadingRaw(false);
    }
  }

  async function loadReport() {
    setLoadingReport(true);
    setReport(null);
    try {
      const data = await requestJson("/api/analysis");
      setReport(data);
      setReportMessage(data.ready
        ? (data.events.length > 0 ? "현재 로그의 정규화 결과를 불러왔습니다." : emptyMessage)
        : data.message);
    } catch (error) {
      setReportMessage(error.message);
    } finally {
      setLoadingReport(false);
    }
  }

  const visibleEvents = (report?.events || []).filter(event =>
    (source === "all" || event.source === source) && (!errorsOnly || event.status_code >= 400)
  );

  return <>
    <p>general에서 직접 보낸 요청을 app과 Nginx가 어떻게 기록하는지 비교합니다. 새 요청을 보낸 뒤에는 원본과 통합 로그를 차례로 다시 불러오세요.</p>
    <section className="panel" aria-labelledby="raw-log-heading">
      <h2 id="raw-log-heading">1. 원본 로그</h2>
      <p>정규화 코드를 작성하기 전에도 두 출처의 현재 기록을 볼 수 있습니다.</p>
      <p>새 기록은 각 목록의 아래쪽에 추가됩니다. 목록 안에서 아래로 스크롤해 확인하세요.</p>
      <button onClick={loadRaw} disabled={loadingRaw || loadingReport}>원본 로그 불러오기</button>
      <p role="status">{loadingRaw ? "원본 로그를 불러오는 중입니다." : rawMessage}</p>
      {rawLogs && <div className="raw-log-grid">
        <section aria-labelledby="app-log-heading">
          <h3 id="app-log-heading">app · Flask JSON</h3>
          <p><code>classroom-logs/app.jsonl</code></p>
          <p>관측행: {rawLogs.app.length}행</p>
          <RawLogList entries={rawLogs.app} source="app" />
        </section>
        <section aria-labelledby="nginx-log-heading">
          <h3 id="nginx-log-heading">nginx · 접근 로그 문자열</h3>
          <p><code>classroom-logs/nginx.log</code></p>
          <p>관측행: {rawLogs.nginx.length}행</p>
          <RawLogList entries={rawLogs.nginx} source="nginx" />
        </section>
      </div>}
    </section>
    <section className="panel" aria-labelledby="normalized-log-heading">
      <h2 id="normalized-log-heading">2. 정규화한 통합 로그</h2>
      <p>두 형식을 같은 필드로 바꾼 뒤 한 표에서 조회합니다. 원본을 새로 불러오면 이전 표는 지워지므로 이 버튼도 다시 누르세요.</p>
      <button onClick={loadReport} disabled={loadingRaw || loadingReport}>통합 로그 불러오기</button>
      <p role="status">{loadingReport ? "통합 로그를 불러오는 중입니다." : reportMessage}</p>
      {report?.ready && <>
        <p className="observation-counts">전체 관측행: {report.total_count}행 / 오류 관측행: {report.error_count}행</p>
        <div className="log-filters">
          <label>출처
            <select value={source} onChange={event => setSource(event.target.value)}>
              <option value="all">전체</option>
              <option value="app">app</option>
              <option value="nginx">nginx</option>
            </select>
          </label>
          <label className="checkbox-label">
            <input type="checkbox" checked={errorsOnly} onChange={event => setErrorsOnly(event.target.checked)} />
            오류만 보기
          </label>
        </div>
        <p>표시 관측행: {visibleEvents.length}행</p>
        <p>표가 화면보다 넓으면 표 안에서 좌우로 스크롤하세요.</p>
        <div className="log-table-scroll" role="region" aria-label="정규화한 통합 로그 표" tabIndex={0}>
          <table className="log-table">
            <thead><tr><th>ID</th><th>출처</th><th>방법</th><th>경로</th><th>상태</th><th>원본</th></tr></thead>
            <tbody>{visibleEvents.map(event => <tr key={event.id}>
              <td>{event.id}</td><td>{event.source}</td><td>{event.method}</td>
              <td>{event.path}</td><td>{event.status_code}</td>
              <td><details><summary>원본 보기</summary><pre>{typeof event.raw === "string" ? event.raw : JSON.stringify(event.raw, null, 2)}</pre></details></td>
            </tr>)}</tbody>
          </table>
        </div>
        {visibleEvents.length === 0 && report.events.length > 0 && <p>선택한 조건에 맞는 관측행이 없습니다.</p>}
      </>}
      <p>관측행은 요청 수가 아닙니다. 같은 요청이 app과 nginx에 각각 기록될 수 있으며, 오류 응답도 공격으로 확정하지 않습니다.</p>
    </section>
    <p>SIEM의 로그 정규화·통합 조회 일부를 구현합니다. 공격 판정·자동 차단·XDR 탐지 기능은 아닙니다.</p>
  </>;
}
