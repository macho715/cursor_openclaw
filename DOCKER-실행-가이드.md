# Docker 환경에서 OpenClaw 실행 가이드 (상세)

현재 구조: **Gateway = Windows 호스트**, **에이전트 샌드박스 = Docker**.  
**Gateway까지 Docker**에서 실행하려면 아래를 순서대로 따르면 됩니다.

---

## 목차

0. [컴퓨터 세팅 (처음 한 번)](#0-컴퓨터-세팅-처음-한-번)
1. [준비 사항](#1-준비-사항)
2. [Docker Desktop 설정](#2-docker-desktop-설정)
3. [빠른 실행 (docker-setup.sh)](#3-빠른-실행-docker-setupsh)
4. [온보딩 마법사에서 고를 값](#4-온보딩-마법사에서-고를-값)
5. [실행 후 접속·토큰](#5-실행-후-접속토큰)
6. [Ollama 연결 (Gateway가 Docker 안일 때)](#6-ollama-연결-gateway가-docker-안일-때)
7. [Gateway Docker + 샌드박스 동작 (소켓 마운트)](#7-gateway-docker--샌드박스-동작-소켓-마운트)
8. [수동 실행 (단계별)](#8-수동-실행-단계별)
9. [일상 명령 (시작/중지/로그/헬스)](#9-일상-명령-시작중지로그헬스)
10. [트러블슈팅](#10-트러블슈팅)
11. [요약 표](#11-요약-표)

---

## 0. 컴퓨터 세팅 (처음 한 번)

새 PC에서 OpenClaw를 Docker로 쓰기 전에, 아래를 **한 번만** 순서대로 진행합니다.

### 0.1 Windows 요구사항

- **Windows 10 21H2 이상** 또는 **Windows 11** (64비트).
- **가상화 활성화**: BIOS/UEFI에서 VT-x(Intel) 또는 AMD-V 켜기.  
  - 확인: 작업 관리자 → 성능 → CPU → "가상화: 사용" 인지 확인.

### 0.2 WSL2 설치 (Bash로 docker-setup.sh 실행할 때 사용)

1. **PowerShell(관리자)** 에서:
   ```powershell
   wsl --install
   ```
2. 재부팅 후 WSL이 설치됨. 기본으로 Ubuntu가 설치되는 경우가 많음.
3. Ubuntu 앱을 열어 사용자/비밀번호 한 번 설정.
4. (선택) WSL2를 기본으로 쓰려면:
   ```powershell
   wsl --set-default-version 2
   ```

**대안**: WSL 없이 **Git Bash**만 쓸 수도 있음 → [0.4](#04-git-설치-git-bash-선택-시) 참고.

### 0.3 Docker Desktop 설치

1. [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/) 에서 설치 파일 받아 실행.
2. 설치 시 **"Use WSL 2 based engine"** 옵션 선택 (권장).
3. 설치 후 **Docker Desktop** 실행. 트레이에 고래 아이콘이 보이면 준비 완료.
4. (WSL2 사용 시) **Settings → Resources → WSL integration** 에서 사용할 Linux 배포판(예: Ubuntu) 켜기.

### 0.4 Git 설치 (Git Bash 선택 시)

- WSL2만 쓸 경우 **생략 가능**.
- **Git Bash**로 `docker-setup.sh`를 실행할 거라면: [git-scm.com](https://git-scm.com) 에서 Git for Windows 설치. 설치 시 "Git Bash Here" 등 선택.

### 0.5 Ollama 설치 (로컬 LLM)

1. [ollama.com](https://ollama.com) 에서 Windows용 Ollama 설치.
2. 설치 후 **Ollama** 실행(시작 메뉴 또는 트레이).
3. 터미널에서 모델 받기 (예):
   ```powershell
   ollama pull llama3.1:8b
   ```
4. 포트 **11434** 사용. 브라우저에서 `http://127.0.0.1:11434` 로 접속해 "Ollama is running" 나오면 정상.

### 0.6 OpenClaw 레포 받기

- **방법 A (Git)**  
  WSL2 또는 Git Bash에서 (경로는 Docker Desktop **File sharing**에 포함되는 곳으로, 한글·공백 없이 권장):
  ```bash
  # WSL2 예시
  git clone https://github.com/openclaw/openclaw.git /mnt/c/Users/jichu/Downloads/openclaw
  # Git Bash 예시
  git clone https://github.com/openclaw/openclaw.git /c/Users/jichu/Downloads/openclaw
  ```
- **방법 B (ZIP)**  
  [GitHub openclaw/openclaw](https://github.com/openclaw/openclaw) → Code → Download ZIP → 압축 해제 후 `openclaw` 폴더를 예: `C:\Users\jichu\Downloads\openclaw` 에 두기.

- **참고**: 레포 경로에 **한글이나 공백**이 있으면 스크립트·Docker에서 오류가 날 수 있음. 가능하면 영문·공백 없는 경로 사용.

이후 가이드의 **1. 준비 사항**부터 진행하면 됩니다.

---

## 1. 준비 사항

| 항목 | 설명 |
|------|------|
| **Docker Desktop** | 설치 후 실행 중. WSL2 백엔드 권장. |
| **Ollama** | Windows에 설치·실행 중 (Docker 아님). 포트 11434. |
| **Bash** | `docker-setup.sh` 실행용. **WSL2** 또는 **Git Bash** 필요. |
| **디스크** | 이미지 빌드용 여유 공간 (수 GB). |

- WSL2 없으면: Microsoft Store에서 "Ubuntu" 설치 후 `wsl --set-default-version 2`.
- Git Bash: [git-scm.com](https://git-scm.com) 설치 시 포함.

---

## 2. Docker Desktop 설정

- **Settings → Resources → File sharing** 에서 `C:\`(또는 `C:\Users\jichu`) 공유 허용.
- **Settings → Resources → WSL integration** 에서 사용할 WSL 배포판 켜기 (WSL에서 docker 쓸 경우).
- **Docker Compose v2** 필요 (명령어는 `docker compose` 한 칸. v1 `docker-compose` 하이픈과 구분).
- 터미널에서 확인:
  ```bash
  docker --version
  docker compose version
  ```

---

## 3. 빠른 실행 (docker-setup.sh)

### 3.0 선택 환경 변수 (설정 전에 필요 시만)

| 변수 | 설명 |
|------|------|
| `OPENCLAW_EXTRA_MOUNTS` | 호스트 디렉터리를 컨테이너에 추가 마운트. 쉼표 구분 (예: `경로1:컨테이너경로:ro,경로2:컨테이너경로:rw`). 설정 시 스크립트가 `docker-compose.extra.yml`을 생성함. |
| `OPENCLAW_HOME_VOLUME` | `/home/node` 전체를 named volume으로 유지 (브라우저 캐시 등). 설정 시 `docker-compose.extra.yml` 생성. |
| `OPENCLAW_DOCKER_APT_PACKAGES` | 이미지 빌드 시 설치할 apt 패키지 (공백 구분, 예: `git curl jq`). 변경 시 이미지 재빌드 필요. |

- **주의**: `OPENCLAW_EXTRA_MOUNTS` 또는 `OPENCLAW_HOME_VOLUME`을 쓰면 스크립트가 `docker-compose.extra.yml`을 만듦. 이후 `docker compose` 명령은 **레포 루트**에서 실행하면 이 파일이 자동으로 함께 로드됨. 다른 디렉터리에서 실행할 때는 `docker compose -f docker-compose.yml -f docker-compose.extra.yml <명령>` 형태로 두 파일 모두 지정.

### 3.1 WSL2에서 실행

```bash
# WSL2 터미널
cd /mnt/c/Users/jichu/Downloads/openclaw

# 설정·워크스페이스를 Windows 경로로 (기존 .openclaw 재사용)
export OPENCLAW_CONFIG_DIR="/mnt/c/Users/jichu/.openclaw"
export OPENCLAW_WORKSPACE_DIR="/mnt/c/Users/jichu/.openclaw/workspace"

# 한 번에 실행 (이미지 빌드 → 온보딩 → gateway 기동)
./docker-setup.sh
```

### 3.2 Git Bash에서 실행

```bash
cd /c/Users/jichu/Downloads/openclaw

export OPENCLAW_CONFIG_DIR="/c/Users/jichu/.openclaw"
export OPENCLAW_WORKSPACE_DIR="/c/Users/jichu/.openclaw/workspace"

./docker-setup.sh
```

### 3.3 스크립트가 하는 일

1. `docker build -t openclaw:local -f Dockerfile .` 로 Gateway 이미지 빌드 (몇 분 소요 가능).
2. `docker compose run --rm openclaw-cli onboard --no-install-daemon` 로 **대화형 온보딩** 실행.
3. 온보딩이 `openclaw.json` 등을 `OPENCLAW_CONFIG_DIR`에 씀.
4. `docker compose up -d openclaw-gateway` 로 Gateway 컨테이너 백그라운드 기동.
5. 레포 루트에 `.env` 생성 (토큰, 경로, 포트 등).

---

## 4. 온보딩 마법사에서 고를 값

스크립트가 온보딩을 실행하면 대략 아래처럼 물어봅니다. 권장값만 정리.

| 질문 | 권장/예시 |
|------|-----------|
| Gateway bind | **lan** (같은 네트워크에서 접속 가능) |
| Gateway auth | **token** |
| Gateway token | 스크립트가 출력한 값 그대로 쓰거나, 새로 만들면 `.env`와 `openclaw.json`에 맞춰야 함. 기본은 스크립트가 만든 토큰 사용. |
| Tailscale 노출 | **Off** (로컬만 쓸 경우) |
| Gateway 데몬 설치 | **No** (Docker로 띄우므로) |

마법사가 끝나면 설정은 `OPENCLAW_CONFIG_DIR`(예: `C:\Users\jichu\.openclaw`)에 저장됩니다.

---

## 5. 실행 후 접속·토큰

- **URL**: `http://127.0.0.1:18789/` (브라우저에서 접속).
- **토큰**:
  - 터미널에 스크립트가 마지막에 출력한 `Token: ...` 값을 복사.
  - 또는 레포 루트 `.env` 파일에서 `OPENCLAW_GATEWAY_TOKEN=...` 확인.
  - Control UI → 설정 → Gateway token에 붙여넣기.
- **대시보드 링크 다시 보기** (토큰 포함 URL):
  ```bash
  cd /mnt/c/Users/jichu/Downloads/openclaw
  docker compose run --rm openclaw-cli dashboard --no-open
  ```

### 5.1 "unauthorized" / "pairing required" (1008) 나올 때

- 대시보드에서 새 기기 연결 시 **한 번 승인**이 필요할 수 있음.
  ```bash
  docker compose run --rm openclaw-cli devices list
  docker compose run --rm openclaw-cli devices approve <requestId>
  ```
- `requestId`는 `devices list` 출력에서 확인.

---

## 6. Ollama 연결 (Gateway가 Docker 안일 때)

Gateway가 **컨테이너 안**에서 돌면, Ollama는 **호스트(Windows)**에 있으므로 컨테이너 기준으로는 `localhost`가 아닌 **호스트**를 가리켜야 합니다.

- Windows Docker Desktop: **`host.docker.internal`**
- Ollama URL: `http://host.docker.internal:11434/v1`

### 6.1 수정할 파일·위치

- **파일**: `C:\Users\jichu\.openclaw\openclaw.json`
- **백업** (선택): `openclaw.json.bak.docker` 등으로 복사본 저장.

### 6.2 수정할 키

`models.providers.ollama.baseUrl` 값을 다음처럼 변경:

```json
"models": {
  "providers": {
    "ollama": {
      "baseUrl": "http://host.docker.internal:11434/v1",
      "apiKey": "ollama-local",
      "api": "openai-completions",
      "models": [ ... ]
    }
  }
}
```

- 기존에 `http://127.0.0.1:11434/v1` 이었다면 위 한 줄만 바꾸면 됨.
- 수정 후 Gateway 컨테이너 재시작:
  ```bash
  cd /mnt/c/Users/jichu/Downloads/openclaw   # 또는 레포 루트
  docker compose restart openclaw-gateway
  ```

### 6.3 연결 확인

- 브라우저에서 OpenClaw로 간단한 질문 보내서 모델 응답이 오는지 확인.
- 또는 호스트에서: `curl http://127.0.0.1:11434/api/tags` 로 Ollama는 정상인지 확인.

---

## 7. Gateway Docker + 샌드박스 동작 (소켓 마운트)

Gateway를 Docker에서 돌리면서 **에이전트 샌드박스**(exec 등)도 쓰려면, Gateway 컨테이너가 **호스트의 Docker**를 쓸 수 있어야 합니다. 이를 위해 **Docker 소켓**을 컨테이너에 마운트합니다.

### 7.1 오버라이드 파일로 추가 (권장)

레포 루트에 `docker-compose.override.yml`을 만들고, gateway 서비스에 volume만 추가:

```yaml
# docker-compose.override.yml (openclaw 레포 루트에 생성)
services:
  openclaw-gateway:
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
```

- WSL2에서 `docker compose` 실행 시: 위 경로 그대로 사용.
- **Windows PowerShell**에서 Docker Desktop 사용 시: Docker Desktop이 `/var/run/docker.sock`를 처리해 주는 경우가 많음. 안 되면 Docker Desktop 문서의 “Mount Docker socket” 예시 경로 확인.

이후:

```bash
docker compose down
docker compose up -d openclaw-gateway
```

### 7.2 샌드박스 이미지 준비 (필수)

Gateway가 샌드박스 컨테이너를 띄우려면 **샌드박스 이미지**가 호스트에 있어야 함. 한 번만 빌드:

```bash
cd /mnt/c/Users/jichu/Downloads/openclaw   # WSL2. Git Bash는 /c/Users/...
./scripts/sandbox-setup.sh
```

- `openclaw-sandbox:bookworm-slim` 이미지가 생성됨. 실패 시 [10.5](#105-이미지-빌드-실패-pnpm--bun--network) 참고.

### 7.3 동작 확인

- WebChat 등에서 에이전트에게 `ls` 또는 간단한 명령 실행 요청.
- 호스트에서:
  ```bash
  docker ps --filter "name=openclaw-sbx"
  ```
  샌드박스 컨테이너가 생성되면 정상.

### 7.4 보안 참고

- Docker 소켓 마운트는 호스트 Docker와 동일한 권한을 컨테이너에 줌. 신뢰할 수 있는 환경에서만 사용.

---

## 8. 수동 실행 (단계별)

스크립트 없이 직접 할 때:

```bash
cd /mnt/c/Users/jichu/Downloads/openclaw

export OPENCLAW_CONFIG_DIR="/mnt/c/Users/jichu/.openclaw"
export OPENCLAW_WORKSPACE_DIR="/mnt/c/Users/jichu/.openclaw/workspace"
export OPENCLAW_GATEWAY_PORT=18789
export OPENCLAW_BRIDGE_PORT=18790
export OPENCLAW_GATEWAY_BIND=lan

# 토큰 생성 (나중에 .env에 넣거나 기억)
export OPENCLAW_GATEWAY_TOKEN="$(openssl rand -hex 32)"

# 1) 이미지 빌드
docker build -t openclaw:local -f Dockerfile .

# 2) 온보딩 (대화형)
docker compose run --rm openclaw-cli onboard --no-install-daemon

# 3) Gateway 기동
docker compose up -d openclaw-gateway
```

- `.env`가 없으면 compose가 환경 변수 미설정 경고를 낼 수 있음. 레포 루트에 `.env`를 만들어 두면 편함. 최소 예시 (경로는 WSL 기준):
  ```
  OPENCLAW_CONFIG_DIR=/mnt/c/Users/jichu/.openclaw
  OPENCLAW_WORKSPACE_DIR=/mnt/c/Users/jichu/.openclaw/workspace
  OPENCLAW_GATEWAY_PORT=18789
  OPENCLAW_BRIDGE_PORT=18790
  OPENCLAW_GATEWAY_BIND=lan
  OPENCLAW_GATEWAY_TOKEN=<위에서 생성한 토큰>
  OPENCLAW_IMAGE=openclaw:local
  ```

---

## 9. 일상 명령 (시작/중지/로그/헬스)

레포 루트에서 `docker compose` 실행. `OPENCLAW_*`는 `.env`에 있거나 export 해 두기.

- **참고**: `OPENCLAW_EXTRA_MOUNTS` 또는 `OPENCLAW_HOME_VOLUME`을 써서 `docker-compose.extra.yml`이 생성된 경우, 아래 명령을 `docker compose -f docker-compose.yml -f docker-compose.extra.yml ...` 형태로 실행해야 함.

| 목적 | 명령 |
|------|------|
| Gateway 시작 | `docker compose up -d openclaw-gateway` |
| Gateway 중지 | `docker compose stop openclaw-gateway` |
| Gateway 중지·컨테이너 제거 | `docker compose down` |
| 로그 보기 (실시간) | `docker compose logs -f openclaw-gateway` |
| 헬스 체크 | `docker compose exec openclaw-gateway node dist/index.js health --token "$OPENCLAW_GATEWAY_TOKEN"` |
| 대시보드 URL(토큰 포함) | `docker compose run --rm openclaw-cli dashboard --no-open` |

- **채널 설정** (Telegram 등): 설정 후 필요 시 gateway 재시작.
  ```bash
  docker compose run --rm openclaw-cli channels add --channel telegram --token "<봇 토큰>"
  docker compose restart openclaw-gateway
  ```

---

## 10. 트러블슈팅

### 10.1 "permission denied" / EACCES (설정·워크스페이스)

- 이미지는 **node** 사용자(uid 1000)로 실행됨.
- 바인드 마운트 경로(`OPENCLAW_CONFIG_DIR`, `OPENCLAW_WORKSPACE_DIR`)가 컨테이너 안에서 쓰기 가능해야 함.
- **WSL2**: Windows 쪽 경로(`/mnt/c/Users/...`)는 보통 755/775라서 동작하는 경우가 많음. 문제 나오면 `chmod -R 775 ...` 또는 소유자를 1000:1000으로 맞추기(리눅스 쪽 경로일 때).
- **Git Bash**: `C:\Users\jichu\.openclaw`가 Docker에서 공유된 드라이브인지 확인 (Docker Desktop File sharing).

### 10.2 "port 18789 already in use"

- 이미 호스트에서 OpenClaw Gateway가 떠 있으면 포트 충돌.
- 선택 1: 호스트 Gateway 종료 후 다시 `docker compose up -d openclaw-gateway`.
- 선택 2: 다른 포트 쓰기. 예: `export OPENCLAW_GATEWAY_PORT=18799` 후 `docker compose up -d openclaw-gateway`. 접속은 `http://127.0.0.1:18799/`.

### 10.3 Ollama 연결 안 됨 (Gateway in Docker)

- `openclaw.json`의 `models.providers.ollama.baseUrl`이 `http://host.docker.internal:11434/v1` 인지 확인.
- Windows 방화벽에서 Ollama(11434) 허용 여부 확인.
- 호스트에서 `curl http://127.0.0.1:11434/api/tags` 로 Ollama 정상 여부 확인.

### 10.4 샌드박스가 안 생김 (Gateway in Docker)

- Gateway 서비스에 Docker 소켓 마운트가 있어야 함. [7. Gateway Docker + 샌드박스 동작](#7-gateway-docker--샌드박스-동작-소켓-마운트) 참고.
- `docker compose logs openclaw-gateway` 에서 sandbox/docker 관련 에러 확인.

### 10.5 이미지 빌드 실패 (pnpm / Bun / network)

- 네트워크·프록시 환경이면 `HTTP_PROXY`/`HTTPS_PROXY` 등 설정 후 재시도.
- Dockerfile에서 `pnpm build` 실패 시: 레포가 최신인지, `pnpm install`이 호스트에서 성공하는지 먼저 확인.

### 10.6 인증 실패 / "pairing required" (1008)

- [5.1](#51-unauthorized--pairing-required-1008-나올-때) 참고: `devices list` → `devices approve <requestId>`.
- 토큰이 바뀌었으면 Control UI 설정에서 토큰 다시 붙여넣기.

### 10.7 OpenAI Codex OAuth (Docker/헤드리스)

- 마법사에서 Codex OAuth 선택 시 브라우저 콜백이 `http://127.0.0.1:1455/auth/callback`로 오는데, Docker/헤드리스에서는 실패할 수 있음. 브라우저에 뜬 **리다이렉트 URL 전체**를 복사해 마법사에 붙여넣어 인증 완료.

### 10.8 docker-setup.sh 실행 안 됨 (WSL2 / Git Bash)

- **실행 권한**: `chmod +x docker-setup.sh` 후 다시 `./docker-setup.sh`.
- **"bad interpreter"** (Git Bash): 줄바꿈이 CRLF면 발생. `bash docker-setup.sh` 로 직접 실행하거나, `git config core.autocrlf input` 설정 후 레포 다시 clone.
- **경로**: 반드시 **레포 루트**에서 실행 (`cd .../openclaw` 후 실행).

---

## 11. 요약 표

| 목표 | 방법 |
|------|------|
| **지금처럼 쓰기** | Gateway = 호스트(Windows), 샌드박스만 Docker → 추가 작업 없음. |
| **Gateway도 Docker에서** | WSL2/Git Bash에서 `OPENCLAW_CONFIG_DIR`/`OPENCLAW_WORKSPACE_DIR` 설정 후 `./docker-setup.sh` → Ollama baseUrl을 `http://host.docker.internal:11434/v1` 로 변경. |
| **Gateway Docker + 샌드박스** | `docker-compose.override.yml`에 gateway 서비스 volumes로 `/var/run/docker.sock:/var/run/docker.sock` 추가 후 `docker compose up -d openclaw-gateway`. |

---

**문서 버전**: 상세 가이드 (Docker 실행·Ollama·샌드박스·트러블슈팅 포함).
