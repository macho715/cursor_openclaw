# OpenClaw + Ollama Windows 설치·사용 요약

> `cursor_openclaw_ollama_windows.md` (10,239줄) 대화 로그 요약·정리  
> _Exported 2026-02-13 | Cursor 2.4.35_

---

## 문서 개요

| 항목 | 내용 |
|------|------|
| **원본** | Cursor 대화 내보내기 (User ↔ Cursor Q&A) |
| **주제** | OpenClaw + Ollama Windows 원샷 설치, 설정, 사용, 트러블슈팅 |
| **핵심 흐름** | Node → Ollama → 모델 pull → OpenClaw 설치 → 온보딩 → 대시보드/Telegram |

---

## 1. 설치 흐름

```
Node 확인 → Ollama 확인 → (선택) OLLAMA_MODELS → 모델 pull → OpenClaw 설치 → 온보딩 → 대시보드
```

### 1.1 설치 스크립트 실행

```powershell
cd C:\Users\jichu\Downloads
.\install_openclaw_ollama.ps1 -ModelDir "D:\ollama\models"
```

- `D:` 드라이브 없으면 `OLLAMA_MODELS` 생략, 기본 경로 사용
- 온보딩 건너뛰기: `-SkipOnboard`

### 1.2 해결된 설치 오류

| 오류 | 원인 | 조치 |
|------|------|------|
| `byte[]` → `Command` 변환 불가 | `Invoke-WebRequest` 응답이 `byte[]` | UTF-8 문자열로 디코딩 후 `iex` |
| `$RepoDir` 미설정 | 원격 스크립트가 `$RepoDir` 사용 | `$RepoDir = %LOCALAPPDATA%\OpenClaw` 설정 후 실행 |

---

## 2. 온보딩 (한 번만)

```powershell
openclaw onboard --install-daemon
```

| 단계 | 선택/입력 |
|------|-----------|
| Onboarding mode | `QuickStart` |
| Model/auth provider | `Ollama` (로컬 사용 시) |
| Ollama endpoint | `http://localhost:11434` |
| Default model | `llama3.1:8b` 또는 `qwen2.5:7b-instruct` |
| Telegram | 봇 토큰 입력 또는 건너뛰기 |

- **관리자 권한 필요**: 서비스(schtasks) 설치 시 "액세스 거부" 나오면 **관리자 PowerShell**에서 재실행
- **서비스 없이 사용**: `openclaw gateway` 수동 실행 → `openclaw dashboard`

---

## 3. 대시보드·게이트웨이

| 항목 | 내용 |
|------|------|
| **주소** | `http://127.0.0.1:18789/?token=<토큰>` |
| **토큰** | 온보딩 시 발급, 쿼리에 반드시 포함 |
| **다시 열기** | `openclaw dashboard` |
| **게이트웨이 수동 실행** | `openclaw gateway` (창 유지) |
| **게이트웨이 중지** | `openclaw gateway stop` |
| **이미 실행 중** | `gateway already running` → `openclaw gateway stop` 후 재실행 |

---

## 4. Ollama ↔ OpenClaw 연동

### 4.1 한 번에 실행 (권장)

```powershell
ollama launch openclaw
```

### 4.2 수동 설정 (Unknown model 오류 시)

**설정 순서:** `baseUrl` → `apiKey` (순서 바꾸면 검증 실패)

```powershell
openclaw config set models.providers.ollama.baseUrl "http://localhost:11434/v1"
openclaw config set models.providers.ollama.apiKey "ollama-local"
```

**설정 파일 직접 수정** (CLI로 `models` 배열 넣기 어려울 때):

- 경로: `C:\Users\jichu\.openclaw\openclaw.json`
- Ollama provider 블록 예시 (JSON):

```json
"models": {
  "providers": {
    "ollama": {
      "baseUrl": "http://localhost:11434/v1",
      "apiKey": "ollama-local",
      "models": [
        {"id": "llama3.1:8b", "name": "llama3.1:8b", "contextWindow": 65536},
        {"id": "qwen2.5:7b-instruct", "name": "qwen2.5:7b-instruct", "contextWindow": 65536}
      ]
    }
  }
}
```

- **주의**: 각 모델에 `name` 필드 필수 (없으면 `expected string, received undefined`)

### 4.3 기본 모델 변경

- `openclaw.json` → `agents.defaults.model.primary` → `ollama/exaone3.5:7.8b` 등
- 변경 후 `openclaw gateway` 재시작

---

## 5. Telegram

| 단계 | 명령/동작 |
|------|-----------|
| Pairing | 봇에게 `/start` → code 수신 |
| 승인 | `openclaw pairing approve telegram <CODE>` |
| Allowlist | `@username` 대신 **숫자 ID** 권장 → [@userinfobot](https://t.me/userinfobot) 에서 확인 |
| Could not resolve | `@username` 해석 실패 시 숫자 ID만 입력 |

---

## 6. 웹 검색 (web_search)

- Brave Search API 키 필요
- `openclaw configure --section web` 또는 `BRAVE_API_KEY` 환경변수

---

## 7. 외부 접속

| 목적 | 방법 | 명령 |
|------|------|------|
| 같은 Tailnet만 | Tailscale Serve | `openclaw gateway --tailscale serve` |
| 공개 인터넷 | Tailscale Funnel + 비밀번호 | `OPENCLAW_GATEWAY_PASSWORD` 설정 후 `openclaw gateway --tailscale funnel --auth password` |
| SSH만 있을 때 | SSH 터널 | `ssh -N -L 18789:127.0.0.1:18789 user@host` |

---

## 8. 한국어 모델 (RTX 4060 8GB 기준)

| 모델 | pull 명령 | 비고 |
|------|-----------|------|
| **exaone3.5:7.8b** | `ollama pull exaone3.5:7.8b` | LG 공식, 영한 병렬 |
| **qwen2.5:7b-instruct** | `ollama pull qwen2.5:7b-instruct` | 다국어, 이미 설치 가능성 높음 |
| **SEOKDONG Llama3.1 한국어** | `ollama pull kwangsuklee/SEOKDONG-llama3.1_korean_Q5_K_M` | 한국 리더보드 상위 |
| **linkbricks Llama3.1 한국어** | `ollama pull benedict/linkbricks-llama3.1-korean:8b` | 한국어 파인튜닝 |

---

## 9. 트러블슈팅 요약

| 증상 | 확인/조치 |
|------|-----------|
| 연결 안 됨 / 타임아웃 | Ollama 실행, `http://localhost:11434` 접속 테스트 |
| Unknown model: ollama/llama3.1:8b | Ollama provider(baseUrl, models) 설정 추가 |
| baseUrl/models 검증 실패 | `baseUrl` 먼저, 그다음 `apiKey`; `models` 배열은 파일 직접 수정 |
| models.0.name undefined | 각 모델에 `name` 필드 추가 |
| gateway already running | `openclaw gateway stop` 또는 `Stop-Process -Id <pid> -Force` |
| 액세스 거부 (서비스 설치) | 관리자 PowerShell에서 `openclaw onboard --install-daemon` |
| token_missing | 대시보드 접속 시 `?token=...` 쿼리 포함 |

---

## 10. 핵심 명령 치트시트

```powershell
# Ollama
ollama list
ollama run llama3.1:8b
ollama pull exaone3.5:7.8b

# OpenClaw
openclaw onboard --install-daemon
openclaw dashboard
openclaw gateway
openclaw gateway stop
openclaw doctor --fix
openclaw pairing approve telegram <CODE>

# 연동
ollama launch openclaw
```

---

## 11. 관련 문서

| 문서 | 용도 |
|------|------|
| [OLLAMA_OPENCLAW_USAGE.md](./OLLAMA_OPENCLAW_USAGE.md) | 사용법 상세 |
| [LLAMALOMA.MD](../LLAMALOMA.MD) | Ollama + Sandbox 리소스 분리 |
| [smoke_test/OPENCLAW_GATEWAY_CHECKLIST.md](./smoke_test/OPENCLAW_GATEWAY_CHECKLIST.md) | 설치 검증 체크리스트 |
