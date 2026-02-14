# VRAM 계산·세팅 요약 (RTX 4060 8GB)

로컬 LLM(Ollama)용 **VRAM 산식 + 바로 적용 세팅** 한 장.

**안전 러닝 아키텍처(컨테이너·WSL2·쿼터·워치독)**: [vram.md](../vram.md)

---

## 1) 총 GPU 메모리 추정 공식

**총 VRAM ≈ 모델 가중치(양자화 후) + KV 캐시(context × bytes/token) + 런타임 오버헤드(0.5~0.9GB)**

- **모델 가중치**: `.gguf` 크기 또는 `ollama list`의 SIZE.
- **KV 캐시**: `OLLAMA_CONTEXT_LENGTH`에 비례 (모델/양자화마다 토큰당 바이트 상이).
- **오버헤드**: 0.5~0.9GB 여유.
- **실무**: 가용 VRAM의 **10~15%**는 비워두기 (8GB → 약 **7.3GB**로 가정).

---

## 2) 실측 (현재 환경)

| 항목 | 값 |
|------|-----|
| GPU | NVIDIA GeForce RTX 4060 Laptop GPU |
| VRAM | 8188 MiB (유휴 시 사용 ~255 MiB) |
| exaone3.5:7.8b | 4.8 GB, Q4_K_M, 7.8B params |
| qwen2.5:7b-instruct | 4.7 GB |
| llama3.1:8b | 4.9 GB |
| SEOKDONG Q5_K_M | 5.7 GB |

---

## 3) 권장 환경변수 (PowerShell, 바로 적용)

```powershell
setx OLLAMA_NUM_PARALLEL 1
setx OLLAMA_CONTEXT_LENGTH 8192
setx OLLAMA_NUM_THREADS 8
setx OMP_NUM_THREADS 6
```

- **PARALLEL=1** 고정 → KV 중복 방지.
- **CTX=8192** → 8GB에서 실사용 가능 상한; OOM 시 6144→4096으로 하향.

---

## 4) OOM 시 대응 순서

1. `OLLAMA_NUM_PARALLEL=1` 확인
2. `OLLAMA_CONTEXT_LENGTH` 8192 → **6144** → **4096** 단계 하향
3. 더 강한 양자화 (Q5→Q4→Q3) 또는 더 작은 모델
4. 브라우저/WebGL/게임 등 GPU 사용 앱 일시 종료

---

## 5) 실측 체크 3개 (가정 제거용)

```bash
# 모델 크기
ollama show <model>

# 실시간 VRAM
nvidia-smi -l 1

# CTX 8192 / 6144 / 4096 바꿔가며 VRAM 피크 비교
```

---

## 6) 옵션 요약

| 옵션 | 설정 | 위험 | 비고 |
|------|------|------|------|
| **A** | Q4 + CTX=8192 + PARALLEL=1 | 중~높음 | 품질 유지, VRAM 타이트 |
| **B** | CTX=6144(또는 4096) + PARALLEL=1 | 낮음 | 안정 우선 (권장 2순위) |
| **C** | PARALLEL=2 또는 Q5/Q6 | 높음 | 8GB에서 비권장 |

---

*실측일: 환경 점검 시점 기준. VRAM 피크가 7.2GB 근접 시 CTX 하향 적용.*
