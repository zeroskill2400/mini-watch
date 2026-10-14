"use client";
import { useEffect, useState } from "react";
import { requestJson } from "../api/client";
import AnalysisClient from "./AnalysisClient";
import DetectionClient from "./DetectionClient";

export default function MonitorClient() {
  const [user, setUser] = useState(null);
  const [username, setUsername] = useState("class-operator");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [pending, setPending] = useState(false);
  const [sessionStatus, setSessionStatus] = useState("checking");

  useEffect(() => {
    let active = true;
    requestJson("/api/auth/me")
      .then(result => {
        if (!active) return;
        setUser(result.user);
        setSessionStatus("ready");
      })
      .catch(error => {
        if (!active) return;
        setMessage(error.message);
        setSessionStatus("error");
      });
    return () => { active = false; };
  }, []);

  async function checkSession() {
    setPending(true);
    setSessionStatus("checking");
    setMessage("");
    try {
      const result = await requestJson("/api/auth/me");
      setUser(result.user);
      setSessionStatus("ready");
    } catch (error) {
      setMessage(error.message);
      setSessionStatus("error");
    } finally {
      setPending(false);
    }
  }

  async function login(event) {
    event.preventDefault();
    setPending(true);
    try {
      const result = await requestJson("/api/auth/login", "POST", { username, password });
      setUser(result.user);
      setPassword("");
      setMessage("로그인했습니다.");
    } catch (error) {
      setMessage(error.message);
    } finally {
      setPending(false);
    }
  }

  async function logout() {
    setPending(true);
    try {
      await requestJson("/api/auth/logout", "POST");
      setUser(null);
      setMessage("로그아웃했습니다.");
    } catch (error) {
      setMessage(error.message);
    } finally {
      setPending(false);
    }
  }

  return <main>
    <h1>로그인 실패 탐지 화면</h1>
    {sessionStatus === "checking" && <p role="status">로그인 상태를 확인하고 있습니다.</p>}
    {sessionStatus === "error" && <div>
      <p role="alert">{message}</p>
      <button onClick={checkSession} disabled={pending}>다시 확인</button>
    </div>}
    {sessionStatus === "ready" && message && <p role="status">{message}</p>}
    {sessionStatus === "ready" && (!user ? <form onSubmit={login} className="login-form">
      <h2>감시 서비스 로그인</h2>
      <p>준비된 수업 계정으로 로그인합니다. 회원가입은 하지 않습니다.</p>
      <p>아이디: <code>class-operator</code> / 수업용 비밀번호: <code>classroom1234!</code></p>
      <label>아이디
        <input autoComplete="username" value={username} onChange={event => setUsername(event.target.value)} required />
      </label>
      <label>비밀번호
        <input type="password" autoComplete="current-password" value={password} onChange={event => setPassword(event.target.value)} required />
      </label>
      <button disabled={pending}>로그인</button>
    </form> : <>
      <div className="monitor-session">
        <span>{user.username} 사용자</span>
        <button onClick={logout} disabled={pending}>로그아웃</button>
      </div>
      <DetectionClient />
      <details className="detection-log-review">
        <summary>Day3 통합 로그 다시 보기</summary>
        <AnalysisClient />
      </details>
    </>)}
  </main>;
}
