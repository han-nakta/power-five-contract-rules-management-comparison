# 발전5사_계약규정_비교

- 프로젝트 표시명: **발전5사 계약규정 관리 및 비교**
- GitHub repository: https://github.com/han-nakta/power-five-contract-rules-management-comparison
- 공개 상태: `public`

한국전력 발전자회사 5사의 계약규정을 국가법령정보센터 공공기관 규정 API(`target=pi`)와 ALIO 원본 문서 기준으로 비교·검토하는 독립 프로젝트다.

이 프로젝트는 `<alio-project>`의 canonical ALIO 온톨로지와 분리되어 있다. ALIO 원본 프로젝트는 보존하고, 이 디렉터리에는 발전5사 계약규정 비교에 필요한 dated snapshot·원본·runner·QA만 둔다.

## 현재 범위

- API 본문 비교 완료: 한국남부발전, 한국남동발전, 한국동서발전, 한국서부발전
- 한국중부발전: 현재 `target=pi` 계약규정 행을 확인하지 못한 `no_api_record` 상태
  - 이는 계약규정이 없다는 뜻이 아니다.
  - 기관 홈페이지/ALIO/local-file fallback 탐색 대상으로 유지한다.
- 비교 결과는 법률상 동일성 또는 규정의 우열을 자동 판정하지 않고, 내용 기반 대응 후보와 차이 후보를 생성한다.

## 검증 완료 snapshot

- API 조문: 763개
- 다중 정규화 unit: 4,969개
- 내용 기반 조문 대응 후보: 1,152개
- 부칙 구조화: 108개
  - 남부 23, 남동 31, 동서 32, 서부 22
- 조문 추적성 QA: pass
- 부칙 추적성 QA: pass
- API-HWP source QA: pass
- Python runner 문법 검사: pass

## 디렉터리

```text
발전5사_계약규정_비교/
├─ README.md
├─ PROJECT_HANDOFF.md
├─ scripts/
│  └─ compare_four_contract_rules_api_review.py
├─ source/
│  ├─ alio_original/       # 4개 비교 대상 HWP 원본 사본
│  └─ extracted_text/      # source QA용 HWP 추출 텍스트 사본
├─ reviews/
│  └─ contract_rule_comparison_2026-08-11/
│     ├─ raw/api/          # target=pi API snapshot
│     ├─ raw/alio_download/ # 실행 시 재확보한 ALIO 원본
│     ├─ derived/structured/ # 조문·부칙 JSONL
│     ├─ derived/normalized/ # 항·호·목 다중 정규화
│     ├─ derived/comparison/ # 대응 후보·topic matrix
│     ├─ qa/
│     └─ reports/
├─ catalog/
│  └─ power_subsidiaries_coverage.json
├─ docs/
│  ├─ PRD.md
│  ├─ power-subsidiaries-coverage-2026-08-10.md
│  └─ version-management-options-review-2026-08-11.md
```

제품 요구사항과 현재까지의 합의 사항은 [`docs/PRD.md`](docs/PRD.md)에 정리되어 있다.

## 독립 재실행

```bash
cd "."
python3 scripts/compare_four_contract_rules_api_review.py
```

현재 runner는 이전 검증 snapshot과 동일하게 공개 샘플 호출값을 사용한다. 운영용 API 호출에는 `OC=test`를 사용하지 말고, 국가법령정보센터에 등록된 운영 키를 서버 측 설정으로 교체해야 한다.

## 주요 산출물

```text
reviews/contract_rule_comparison_2026-08-11/run_result.json
reviews/contract_rule_comparison_2026-08-11/qa/traceability_report.json
reviews/contract_rule_comparison_2026-08-11/qa/supplementary_traceability_report.json
reviews/contract_rule_comparison_2026-08-11/qa/source_qa_report.json
reviews/contract_rule_comparison_2026-08-11/reports/contract_rule_comparison_review.md
```

## 경계

- ALIO 전체 기관 온톨로지 구축 작업과 섞지 않는다.
- G2B API 데이터·G2B 온톨로지와 섞지 않는다.
- 부칙·본문 비교 결과는 근거 기반 검토 보조용이며 법률 자문이 아니다.
- raw/API/HWP 원문은 로컬 프로젝트 산출물로 보존하고, 채팅 보고에는 count/status/QA 중심으로 요약한다.
