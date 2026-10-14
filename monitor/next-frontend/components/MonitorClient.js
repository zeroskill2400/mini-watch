"use client";
import { useState } from "react";
import { requestJson } from "../api/client";
import AnalysisClient from "./AnalysisClient";

export default function MonitorClient() {
  const [user, setUser] = useState(null);
  const [username, setUsername] = useState("class-operator");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [pending, setPending] = useState(false);

  async function checkSession() {
    setPending(true);
    try {
      const result = await requestJson("/api/auth/me");
      setUser(result.user);
      setMessage(result.user ? "로그인 상태를 확인했습니다." : "로그인해 주세요.");
    } catch (error) {
      setMessage(error.message);
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
    <h1>Day3 · 로그 정규화와 통합 조회</h1>
    <div className="actions">
      <button onClick={checkSession} disabled={pending}>현재 로그인 확인</button>
      {user && <button onClick={logout} disabled={pending}>로그아웃</button>}
    </div>
    <p role="status">{message}</p>
    {!user ? <form onSubmit={login} className="login-form">
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
      <p>{user.username} 사용자</p>
      <AnalysisClient />
    </>}
  </main>;
}
