### 판정: **조건부(AMBER)**

### 근거: **정확한 분리 설계는 가능하나, Docker Desktop(WSL2)·GPU/CPU 스케줄링·현재 OpenClaw 설정값 미제공 → ⚠️AMBER:[가정: Windows Host + Docker Desktop + Sandbox=Linux 컨테이너, Ollama=Host GPU 실행]**

### 다음행동: 아래 **Option A/B/C 중 1개 선택 → 즉시 적용 가능한 리소스 제한/우선순위/IO 분리** 순서로 진행

> **설치 검증:** OpenClaw Gateway/Ollama/Docker 설치가 정상인지 확인하려면 [docs/smoke_test/OPENCLAW_GATEWAY_CHECKLIST.md](docs/smoke_test/OPENCLAW_GATEWAY_CHECKLIST.md) 참조.

---

# Executive Summary

* 목표는 **Ollama(LLM 추론)** 과 **Sandbox(exec/read/write/process)** 가 서로 자원을 뺏지 않게 **CPU/RAM/IO/네트워크/프로세스 우선순위**를 분리하는 것.
* 권장 기본은 **Option A: Docker Sandbox에 CPU/RAM/IO 상한** + **Ollama는 GPU 우선(Host)** 유지.
* 병목이 파일 IO(대용량 정리/스캔)면 **Option B: IO 경로 분리(전용 SSD/볼륨)** 가 체감이 큼.
* 장기적으로는 **Option C: Sandbox 2단(경량/중량) + 작업 큐(승인형 DRY_RUN→APPLY)** 로 안정화.

---

# EN Sources (≤3)

* ⚠️AMBER: 이번 답변은 **일반적인 Windows+Docker+LLM 로컬 운영 베스트프랙티스 기반**이며, **OpenClaw/Docker Desktop/WSL2 버전별 차이**는 확인하지 못함(웹조회 미실시).

---

# Visual 1 — 실제 프로세스 흐름 다이어그램(심화)

```mermaid
flowchart LR
  U[User / WebChat / Telegram] -->|WS 18789| G[OpenClaw Gateway (Windows Host)]
  G -->|HTTP 127.0.0.1:11434| O[Ollama (Host GPU)]
  G -->|Docker API| D[Docker Engine / Desktop (WSL2)]
  D --> S[Sandbox Container (bookworm-slim)]
  S -->|exec| SH[Shell Cmd]
  S -->|read/write/edit| FS[Sandbox FS Volume]
  S -->|process| BG[Background Proc]
  FS -->|optional mount| W[(Host Workspace)]
  O --> GPU[(RTX 4060 8GB)]
  G --> LOG[Audit Log / Diff / Approvals]
```

---

# Visual 2 — 자원 경쟁 포인트(무조건 잡아야 하는 4곳)

| No | Item       | Value                          | Risk           | Evidence                          |
| -: | ---------- | ------------------------------ | -------------- | --------------------------------- |
|  1 | CPU 경쟁     | Sandbox `exec`가 CPU 100% 사용 가능 | Ollama 토큰속도 급락 | ⚠️AMBER:[일반 현상]                   |
|  2 | RAM 경쟁     | 32GB에서 대용량 파일 스캔/정렬            | 스왑/페이지파일 발생    | ⚠️AMBER:[일반 현상]                   |
|  3 | IO 경쟁      | 대량 파일 `stat/list/read`         | 모델 응답 지연/끊김    | ⚠️AMBER:[일반 현상]                   |
|  4 | WSL2/볼륨 경로 | `/mnt/c` 등 Windows 마운트 접근      | IO 매우 느려질 수 있음 | ⚠️AMBER:[가정: Docker Desktop+WSL2] |

---

# Options (A/B/C) — Pros/Cons/Cost/Risk/Time

(비용은 내부 인건비 기준 **AED 0.00**으로 표기, 외부 구매 없음 가정)

| Option | 핵심                                         | Pros          | Cons              |     Cost | Risk     | Time  |
| ------ | ------------------------------------------ | ------------- | ----------------- | -------: | -------- | ----- |
| A      | **Sandbox 상한( CPU/RAM/PIDs ) + Ollama 우선** | 즉시 효과, 안정적    | 상한이 낮으면 도구 작업 느려짐 | AED 0.00 | Low      | 0.50h |
| B      | **IO 경로 분리(전용 볼륨/SSD) + 마운트 최소화**          | 대량 파일정리 체감 최대 | 디스크/폴더 구조 재정비 필요  | AED 0.00 | Med      | 2.00h |
| C      | **Sandbox 2단(경량/중량) + 큐/승인형 배치**           | 대규모 자동화에 최적   | 설계/운영 복잡도 상승      | AED 0.00 | Med-High | 6.00h |

---

# Steps — “Ollama + Sandbox 분리” 적용 순서 (바로 실행형)

## 1) Sandbox 컨테이너에 상한 걸기 (Option A 핵심)

* **CPU**: 6~8 threads만 허용(나머지는 Ollama/Host 여유)
* **RAM**: 8~12GB 상한(파일 스캔 폭주 방지)
* **PIDs**: 256~512 제한(프로세스 폭주 방지)

예시(컨테이너 생성 시 적용 개념):

```bash
docker run --cpus="6.00" --memory="12g" --pids-limit=512 ...
```

## 2) Windows 우선순위 분리

* **Ollama 프로세스 우선순위: High**
* **Docker Desktop/WSL VM 우선순위: Normal**
* **Sandbox 내부 작업은 nice/ionice로 낮춤(리눅스 내부 가능 시)**

## 3) IO 경로 “느린 마운트” 차단 (Option B 핵심)

* `workspaceAccess: "none"` 유지가 맞음(호스트 파일 직접 마운트 금지)
* 샌드박스 내부에서는 **볼륨(리눅스 파일시스템)** 에서만 대량 스캔/정리 수행
* Windows 경로(`/mnt/c` 계열)에서 대량 `stat`/`glob` 금지

## 4) Ollama 안정화(추론 지연 방지)

* 컨텍스트는 **4k 기본**, 8k는 “필요 시만”
* 8k 필요 시: **KV offload**로 VRAM 보호(성능-안정 trade-off)

(개념 예시)

```bash
setx OLLAMA_CONTEXT_LENGTH 4096
setx OLLAMA_KV_OFFLOAD true
```

## 5) 동시성 제한

* Sandbox “대량 작업”은 **동시에 1개만**
* Gateway는 **LLM 호출(채팅)과 파일정리 배치의 동시 실행을 금지**(큐로 순차화)

---

# 운영 KPI (분리 최적화가 성공했는지 바로 보는 지표)

| KPI                         | Target     |
| --------------------------- | ---------- |
| Ollama tokens/sec 변동폭       | ±20.00% 이내 |
| Sandbox 파일 스캔 시 Host UI 프리징 | 0.00회      |
| 페이지파일/스왑 사용                 | 0.00~최소    |
| DRY_RUN 대비 APPLY 일치율        | ≥99.00%    |

---

# Automation Hooks (RPA/LLM/Sheets/TG)

* **TG 알림**: “Sandbox 배치 시작/종료 + 리소스 사용률 스냅샷”
* **승인 게이트**: DRY_RUN 결과가 `manifest.json`/`diff.patch`로 생성되면 “APPLY 승인 버튼”만 노출
* **작업 큐**: `heavy_scan`(단독) ↔ `chat_llm`(상시) 분리 라우팅

---

# QA 체크리스트(데이터 공백/재검증)

* Docker Desktop이 **WSL2 기반인지**(거의 대부분)
* Sandbox가 **호스트 폴더를 마운트하는지 여부**(현재 none이라 했으나 확정 필요)
* Sandbox 컨테이너 생성 시점에 **리소스 제한 플래그가 실제로 적용되는지**
* 대량 스캔 대상 폴더가 **OneDrive/클라우드 동기화 경로인지**(IO 병목 발생 가능)

---

# CmdRec (3개)

* `/switch_mode BRIEF + /logi-master report --deep` (현재 구성 “리소스 분리 설계” 리포트화)
* `/logi-master kpi-dash --fast` (tokens/sec, CPU, RAM, IO 지표 템플릿 생성)
* `/redo step 1` (Option A 상한값을 “권장 수치”로 다시 산정)

---

# ZERO(중단) 로그 — 해당 없음

현재 요청은 고위험 규정/통관/HS/안전 항목이 아니라 **설정 최적화**라 중단 불필요.

---

→ **A안 고정값(한 장 표)** 은 `config/policy/RESOURCE_LIMITS.md` (SSOT) 참조.