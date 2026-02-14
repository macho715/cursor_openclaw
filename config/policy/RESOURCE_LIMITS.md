# RESOURCE_LIMITS.md (SSOT)

> **판정:** AMBER — Docker/WSL 리소스 제한은 공식 옵션으로 가능하나, OpenClaw가 "컨테이너 생성 시 플래그 주입"을 어디서 받는지 미확정.
> **가정:** Docker Desktop(WSL2) + OpenClaw sandbox 컨테이너 생성 가능.

---

## A안(고정) — Ollama(Host) + Sandbox(Docker) 자원 분리

| No | Item                 | Value (고정)             | Risk                     | Evidence                                          |
| -: | -------------------- | ---------------------- | ------------------------ | ------------------------------------------------- |
|  1 | Host CPU 총량(참고)      | 20 threads             | 잘못 가정 시 배분 부정확           | Intel i5-13500HX spec                             |
|  2 | WSL2 VM 상한(CPU)      | `processors=10.00`     | 너무 낮으면 Docker/툴 느려짐      | `.wslconfig` 가능                                  |
|  3 | WSL2 VM 상한(RAM)      | `memory=14.00GB`       | 너무 낮으면 WSL OOM           | `.wslconfig` 가능                                  |
|  4 | WSL2 VM 상한(SWAP)     | `swap=4.00GB`          | 너무 크면 디스크 스왑으로 지연        | `.wslconfig` 가능                                  |
|  5 | Sandbox 컨테이너 CPU 상한  | `--cpus=6.00`          | 너무 높으면 Host/Ollama 체감 저하 | Docker 리소스 제한                                  |
|  6 | Sandbox 컨테이너 RAM 상한  | `--memory=10.00g`      | OOM 시 작업 실패(안전상 의도)      | Docker 리소스 제한                                  |
|  7 | Sandbox 컨테이너 SWAP 상한 | `--memory-swap=10.00g` | 스왑 금지→OOM 빨리 발생(대신 안정)   | Docker 리소스 제한                                  |
|  8 | Sandbox PID 상한       | `--pids-limit=512.00`  | 너무 낮으면 프로세스 많은 작업 실패     | Docker 리소스 제한                                  |
|  9 | 동시 Sandbox 세션        | `1.00`                 | 병렬 작업 느려짐(대신 추론 안정)      | 운영정책 고정값                                     |
| 10 | Host 여유 RAM 목표       | `≥18.00GB`             | 여유 부족 시 UI/응답 지연         | 32GB 기준 산술                                     |

**해석:** WSL(10C/14GB) → 그 안에서 Sandbox(6C/10GB)로 2단 상한을 걸어 Ollama(Host)와 충돌을 물리적으로 차단.

---

## 적용 순서

### 1. WSL2 전역 상한

Windows 사용자 홈에 `.wslconfig` 생성:

```ini
[wsl2]
memory=14GB
processors=10
swap=4GB
```

적용 후 `wsl --shutdown` 권장.

### 2. Sandbox 컨테이너 상한

OpenClaw가 컨테이너 생성 시 주입해야 하는 플래그:

```bash
docker run --cpus=6 --memory=10g --memory-swap=10g --pids-limit=512 ...
```

### 3. 검증

- `docker stats`에서 Sandbox가 CPU 6.00 / MEM 10.00g 이상 못 쓰는지 확인
- Ollama 토큰 속도(체감) 흔들리면 Option B로 즉시 다운

---

## Options (A/B/C)

| Option | 설정      | Pros                             | Cons                   | Risk     |
| ------ | ------- | -------------------------------- | ---------------------- | -------- |
| A      | 위 표 그대로 | 안정/분리 균형 최적                      | 일부 heavy scan 느려질 수 있음 | Low      |
| B      | 더 보수적   | `--cpus=4`, `--memory=8g`         | Ollama 최우선, 끊김 최소      | Low      |
| C      | 더 공격적   | `--cpus=8`, `--memory=12g`        | Sandbox 처리량 ↑          | Med      |

---

## References

- [Docker Resource constraints](https://docs.docker.com/engine/containers/resource_constraints/)
- [WSL Advanced settings (.wslconfig)](https://learn.microsoft.com/en-us/windows/wsl/wsl-config)
- [Intel Core i5-13500HX](https://www.intel.com/content/www/us/en/products/sku/232156/intel-core-i513500hx-processor-24m-cache-up-to-4-70-ghz/specifications.html)
