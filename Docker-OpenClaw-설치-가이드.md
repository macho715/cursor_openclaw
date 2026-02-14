# Docker OpenClaw 설치 방법 (자세히)

처음부터 끝까지 **Docker로 OpenClaw만 설치·실행**하는 순서입니다.  
상세 옵션·트러블슈팅은 [DOCKER-실행-가이드.md](./DOCKER-실행-가이드.md)를 참고하세요.

**이 프로젝트 스택(Ollama+OpenClaw+Prometheus+Grafana) 실행**: [stack/RUNBOOK.md](stack/RUNBOOK.md) Phase 1~3 참조.

---

## 1. 필요한 것

- **Windows 10 21H2 이상** 또는 **Windows 11** (64비트)
- **가상화 켜기**: 작업 관리자 → 성능 → CPU → "가상화: 사용"
- **인터넷** (설치·이미지 받기용)
- **디스크 여유** 수 GB

---

## 2. WSL2 설치 (Bash 쓸 때 필요)

1. **PowerShell을 관리자 권한**으로 실행.
2. 아래 한 줄 입력 후 Enter:
   ```powershell
   wsl --install
   ```
3. **재부팅**.
4. 재부팅 후 **Ubuntu** 앱이 뜨면 열고, **사용자 이름**과 **비밀번호** 한 번 입력해 설정.
5. (선택) WSL2가 기본인지 확인:
   ```powershell
   wsl --set-default-version 2
   ```

**WSL 안 쓸 때**: [Git for Windows](https://git-scm.com) 설치 후 **Git Bash**로 4단계부터 진행하면 됩니다.

---

## 3. Docker Desktop 설치

1. 브라우저에서 **[Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/)** 설치 페이지 열기.
2. **Download Docker Desktop** 등으로 설치 파일 받기.
3. 설치 파일 실행 후:
   - **Use WSL 2 instead of Hyper-V** (또는 "Use WSL 2 based engine") **체크**.
   - 설치 완료까지 진행.
4. **Docker Desktop** 실행. 오른쪽 아래 트레이에 **고래 아이콘**이 보이면 준비 완료.
5. **Settings**(톱니바퀴) → **Resources** → **WSL integration** 에서 **Ubuntu** (또는 쓰는 Linux 배포판) **켜기**.
6. **Settings** → **Resources** → **File sharing** 에서 **C:\** 또는 **C:\Users\jichu** 가 공유 목록에 있는지 확인. 없으면 **+** 로 추가.

**확인** (WSL2 터미널 또는 Git Bash에서):

```bash
docker --version
docker compose version
```

둘 다 버전이 나오면 OK.

---

## 4. Ollama 설치 (로컬 LLM)

1. **[ollama.com](https://ollama.com)** 접속 → **Download** → **Windows** 받기.
2. 설치 후 **Ollama** 실행 (시작 메뉴 또는 트레이).
3. **PowerShell** 또는 **명령 프롬프트**에서:
   ```powershell
   ollama pull llama3.1:8b
   ```
   (다른 모델 쓰려면 해당 모델 이름으로 `ollama pull <이름>` 실행.)
4. 브라우저에서 **http://127.0.0.1:11434** 열어서 "Ollama is running" 나오면 정상.

---

## 5. OpenClaw 레포 받기

**경로는 한글·공백 없이** 두는 것이 좋습니다. 예: `C:\Users\jichu\Downloads\openclaw`.

### 방법 A: Git (WSL2 또는 Git Bash)

**WSL2** 터미널에서:

```bash
git clone https://github.com/openclaw/openclaw.git /mnt/c/Users/jichu/Downloads/openclaw
```

**Git Bash**에서:

```bash
git clone https://github.com/openclaw/openclaw.git /c/Users/jichu/Downloads/openclaw
```

### 방법 B: ZIP

1. **[github.com/openclaw/openclaw](https://github.com/openclaw/openclaw)** 접속.
2. **Code** → **Download ZIP** 클릭.
3. ZIP 압축 해제 후 폴더 이름을 `openclaw` 로 두고, `C:\Users\jichu\Downloads\openclaw` 에 넣기.

---

## 6. OpenClaw Docker 설치·실행 (한 번에)

아래는 **설정 파일·워크스페이스를 Windows 경로에 두고**, **한 번에 이미지 빌드 + 온보딩 + Gateway 기동**까지 하는 방법입니다.

### 6.1 WSL2에서 실행할 때

1. **Ubuntu**(또는 사용 중인 WSL 배포판) 터미널 열기.
2. 아래를 **순서대로** 붙여 넣어 실행 (경로는 본인에 맞게 수정).

```bash
cd /mnt/c/Users/jichu/Downloads/openclaw

export OPENCLAW_CONFIG_DIR="/mnt/c/Users/jichu/.openclaw"
export OPENCLAW_WORKSPACE_DIR="/mnt/c/Users/jichu/.openclaw/workspace"

./docker-setup.sh
```

3. **이미지 빌드**가 끝나면 **온보딩 마법사**가 시작됨. 질문에 아래처럼 답하면 됨:
   - **Gateway bind** → `lan` 입력 후 Enter.
   - **Gateway auth** → `token` 선택.
   - **Gateway token** → 화면에 나온 토큰 **그대로** 입력 (또는 Enter로 기본값 사용).
   - **Tailscale** → `Off` 또는 No.
   - **Install Gateway daemon** → **No** (Docker로 띄우므로).
4. 마법사가 끝나면 **Gateway 컨테이너**가 자동으로 백그라운드에서 실행됨.
5. 마지막에 터미널에 **Token: ...** 이 출력됨. 이 값을 **복사**해 두기.

### 6.2 Git Bash에서 실행할 때

1. **Git Bash** 실행.
2. **레포 폴더**로 이동 (경로는 본인에 맞게 수정):

```bash
cd /c/Users/jichu/Downloads/openclaw

export OPENCLAW_CONFIG_DIR="/c/Users/jichu/.openclaw"
export OPENCLAW_WORKSPACE_DIR="/c/Users/jichu/.openclaw/workspace"

./docker-setup.sh
```

3. 이후는 **6.1의 3~5**와 동일 (온보딩 답변, 토큰 복사).

### 6.3 스크립트 실행이 안 될 때

- **"permission denied"** 나오면:
  ```bash
  chmod +x docker-setup.sh
  ./docker-setup.sh
  ```
- **"bad interpreter"** 나오면 (줄바꿈 문제):
  ```bash
  bash docker-setup.sh
  ```

---

## 7. 브라우저에서 접속

1. 브라우저 주소창에 **http://127.0.0.1:18789/** 입력 후 접속.
2. **설정**(톱니바퀴) 또는 **Settings** → **Gateway token** 칸에 **6단계에서 복사한 토큰** 붙여 넣기.
3. 저장 후 채팅 화면이 보이면 **설치·접속 완료**.

토큰을 잊었으면 **OpenClaw 레포 폴더** 안의 **.env** 파일을 열어 `OPENCLAW_GATEWAY_TOKEN=...` 값을 확인하면 됩니다.

---

## 8. Ollama 연결 (Gateway가 Docker 안에 있을 때)

Gateway를 **Docker**에서 띄웠다면, LLM은 **Windows에 설치한 Ollama**에 연결해야 합니다.

1. **메모장** 등으로 **C:\Users\jichu\.openclaw\openclaw.json** 열기.
2. **Ctrl+F**로 `baseUrl` 검색.
3. `"baseUrl": "http://127.0.0.1:11434/v1"` 를 아래처럼 바꿈:
   ```json
   "baseUrl": "http://host.docker.internal:11434/v1"
   ```
4. 저장 후, OpenClaw Gateway 컨테이너만 다시 시작:
   ```bash
   cd /mnt/c/Users/jichu/Downloads/openclaw
   docker compose restart openclaw-gateway
   ```
   (Git Bash에서는 `cd /c/Users/jichu/Downloads/openclaw` 로 경로만 바꿔서 실행.)

이후 WebChat에서 메시지를 보내 보면, Ollama 모델로 응답이 오는지 확인할 수 있습니다.

---

## 9. 설치 확인 체크리스트

| 확인 항목 | 방법 |
|-----------|------|
| Docker 실행 중 | 트레이에 고래 아이콘 |
| OpenClaw Gateway 실행 중 | `docker ps` 에 `openclaw-gateway` 보임 |
| Ollama 실행 중 | 브라우저에서 http://127.0.0.1:11434 접속 시 "Ollama is running" |
| WebChat 접속 | http://127.0.0.1:18789/ 접속 후 토큰 입력 |
| LLM 응답 | WebChat에서 질문 보내서 답이 오는지 확인 |

---

## 10. 자주 쓰는 명령 (설치 후)

- **Gateway 로그 보기**  
  ```bash
  cd /mnt/c/Users/jichu/Downloads/openclaw
  docker compose logs -f openclaw-gateway
  ```
- **Gateway 중지**  
  ```bash
  docker compose stop openclaw-gateway
  ```
- **Gateway 다시 시작**  
  ```bash
  docker compose up -d openclaw-gateway
  ```
- **토큰·대시보드 URL 다시 보기**  
  ```bash
  docker compose run --rm openclaw-cli dashboard --no-open
  ```

---

**요약**: 1~5단계로 환경 준비 → 6단계에서 `docker-setup.sh` 한 번 실행 → 7단계에서 브라우저 접속·토큰 입력 → 8단계에서 Ollama baseUrl만 `host.docker.internal` 로 바꾸면 Docker OpenClaw 설치·연동이 끝납니다.  
더 자세한 옵션·에러 해결은 [DOCKER-실행-가이드.md](./DOCKER-실행-가이드.md)를 보면 됩니다.

**설치 완료 후** 이 프로젝트 스택(Ollama+OpenClaw+Prometheus+Grafana)을 실행하려면 → [stack/RUNBOOK.md](stack/RUNBOOK.md) Phase 1~3 참조.
