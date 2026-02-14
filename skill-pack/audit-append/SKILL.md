---
name: audit-append
description: append-only 감사로그 기록(이벤트 체인). audit/append-only/trace 키워드면 사용.
---

# audit-append

## Role
각 단계 결과를 append-only 로그로 남긴다(수정/삭제 금지).

## Steps
1) WRITE 승인 확보
2) append_only_path에 JSONL로 1줄 append
3) event_id/prev_event_id 체인 유지

## Outputs
- audit-append branch
