# 발전5사 계약규정 개정 버전관리 방안 비교 검토

## 1. 검토 목적

계약규정이 개정될 때 다음을 재현 가능하게 관리하는 방법을 비교한다.

- 어떤 원본(API JSON/HWP)이 언제 확보되었는가
- 어떤 규정 버전이 현행이었는가
- 조문·항·호·목·부칙이 어떻게 바뀌었는가
- 금액·비율·기간·횟수·연산자·예외가 어떻게 바뀌었는가
- 변경 결과가 QA를 통과했는가
- 특정 과거 버전과 현재 버전을 다시 조회·검증할 수 있는가

대상 프로젝트의 현재 snapshot은 4개 API 비교 대상과 중부발전 coverage 상태를 포함한다.

- API 조문: 763개
- 다중 정규화 unit: 4,969개
- 내용 기반 조문 대응 후보: 1,152개
- 부칙 구조화: 108개
- 조문·부칙·API-HWP source QA: 모두 pass

## 2. 현재 확인된 환경

### 로컬 Git 상태

현재 프로젝트는 별도 Git 저장소가 아니라 상위 `<local-home>/eva` Git worktree 안에 있다.

- 상위 저장소 branch: `eva`
- 상위 remote: `han-nakta/Agents_Private`
- 새 프로젝트 파일은 현재 상위 저장소에서 untracked 상태
- 로컬 프로젝트 파일 수: 52개
- 전체 프로젝트 크기: 약 21MB
- 원본 HWP·추출 텍스트·API snapshot·구조화 JSONL·QA를 함께 보존할 수 있는 규모다.

### OpenCrab MCP 상태

실제 MCP status 기준:

- MCP/Supabase: 정상
- tier: Expert
- text/cloud ingest 가능
- query/read_graph 가능
- 현재 전체 계정 기준 표시된 상태: documents 448, chunks 3,791, nodes 5,886, edges 11,108
- `발전5사 계약규정` 검색 기준 기존 OpenCrab project 0개, pack 0개, workflow 0개

확인된 주요 OpenCrab 기능 계약:

- `opencrab_ingest_text`: 텍스트를 ingest하고 기본 private ontology pack 생성
- `opencrab_pack_update`: 기존 pack에 time-series 내용/event를 추가하고 `version`, `event_type`, `occurred_at`, `metadata`, `notes`를 기록
- `opencrab_project_manage`: project 생성 및 pack 연결
- `opencrab_project_run`: 특정 project의 pack만 대상으로 질의하고, Expert는 결과를 새 pack으로 reverse-ingest 가능
- `opencrab_list_nodes`, `opencrab_list_edges`, `opencrab_query`: graph/evidence/query 기능
- `opencrab_pack_qa`: ontology pack 품질 평가 및 graph gap/repair plan 생성
- local folder 자체를 SaaS MCP가 직접 읽는 방식은 아니며, 대형 local corpus는 CrabAgent local builder/upload 흐름이 필요하다.

## 3. 방안 1 — Git + GitHub

### 잘 맞는 부분

- 원본 API JSON/HWP의 byte-level snapshot 보존
- commit/tag/hash 기반의 불변 이력
- 두 버전 간 exact diff 및 구조화 diff 연결
- branch/PR로 개정 검토 승인 흐름 구성
- GitHub Actions로 정기 API probe, parser 실행, QA, 변경 PR 자동화
- 특정 시점의 전체 tree를 checkout해 완전한 재현
- 별도 저장소·private visibility·권한·백업 정책을 명확히 관리

### 권장 Git 구조

```text
raw/api/<institution>/<effective_date>/<serial>.response.json
raw/source/<institution>/<effective_date>/<sha256>.hwp
derived/structured/<institution>/<effective_date>/articles.jsonl
derived/structured/<institution>/<effective_date>/supplementary.jsonl
derived/normalized/<institution>/<effective_date>/units.jsonl
derived/comparison/<from>__<to>/article_diff.jsonl
derived/comparison/<from>__<to>/parameter_diff.jsonl
qa/<institution>/<effective_date>/
reports/<institution>/<effective_date>/
catalog/version_manifest.jsonl
```

### 버전 단위

개정 1건을 하나의 논리적 version으로 정의한다.

```text
version_id: <institution>-<effective_date>-<api_serial>-<source_hash_prefix>
institution
rule_title
api_serial
administrative_rule_id
effective_at
promulgated_at
fetched_at
api_sha256
source_sha256
parser_version
previous_version_id
change_status
qa_status
git_commit
git_tag
```

Git tag는 예를 들어 다음처럼 둘 수 있다.

```text
nam-bu-2026-01-13
nam-dong-2025-09-30
dong-seo-2024-12-24
seo-bu-2025-03-17
```

### Git의 한계

- Git 자체는 법률 의미를 해석하지 않는다.
- JSONL 전체를 그대로 diff하면 조문 단위 변경이 읽기 어렵다.
- semantic diff, paragraph/item alignment, numeric parameter diff는 별도 비교 스크립트가 필요하다.
- raw snapshot을 무제한 커밋하면 저장소가 커질 수 있다.
- GitHub 공개 저장소에 원문을 올리면 공개 범위·재배포 조건·원문 이용정책을 별도로 확인해야 한다.

### 보완 방법

- 원문 변경 감지는 hash/API identifier/effective date로 한다.
- 사람이 보는 diff는 `article_diff.jsonl`, `parameter_diff.jsonl`, Markdown report로 별도 생성한다.
- GitHub 저장소는 기본 private로 시작한다.
- API key는 GitHub secret 또는 local runner 환경에만 둔다.
- generated output은 deterministic하게 만들고 parser version/lockfile을 함께 커밋한다.
- 현재 규모에서는 Git LFS가 필수는 아니지만, 장기 snapshot이 커질 때 선택한다.

## 4. 방안 2 — OpenCrab MCP ontology

### 잘 맞는 부분

- `Institution -> Regulation -> RegulationVersion -> ArticleSnapshot` 관계 표현
- `AMENDS`, `SUPERSEDES`, `ADDS`, `DELETES`, `REWORDS`, `SPLITS`, `MERGES` 같은 의미 관계 탐색
- 여러 발전자회사와 여러 개정 버전의 공통 개념·차이·예외 질의
- “어느 회사가 특정 threshold를 언제 변경했는가?” 같은 의미 기반 조회
- 부칙의 시행일·적용례·폐지·경과조치를 evidence/query 레이어로 탐색
- pack QA와 graph gap 확인
- project 단위로 비교 대상 pack만 묶어 질의

### 권장 ontology 모델

```text
Institution
  └─ HAS_REGULATION -> Regulation
       └─ HAS_VERSION -> RegulationVersion
            ├─ DERIVED_FROM -> SourceSnapshot
            ├─ CONTAINS -> ArticleSnapshot
            ├─ EFFECTIVE_FROM -> EffectivePeriod
            └─ SUPERSEDES -> RegulationVersion

AmendmentEvent
  ├─ TARGETS -> RegulationVersion / ArticleSnapshot
  ├─ ADDS / DELETES / REWORDS / SPLITS / MERGES
  └─ EVIDENCED_BY -> SourceSnapshot

ArticleSnapshot
  ├─ HAS_PARAGRAPH / HAS_ITEM
  ├─ HAS_PARAMETER -> NumericParameter
  ├─ HAS_TOPIC -> ContractTopic
  └─ TRACEABLE_TO -> GitCommit / SourcePath / SHA256
```

### pack/project 구성 권장안

- OpenCrab project: `발전5사_계약규정_비교`
- 기관별 private pack:
  - `남부 계약규정`
  - `남동 계약규정`
  - `동서 계약규정`
  - `서부 계약규정`
  - 중부는 API/local fallback source가 확보된 뒤 추가
- 개정 발생 시 기관 pack에 `pack_update`로 time-series event를 append
- 모든 update content/metadata에 다음을 필수로 포함:
  - `version_id`
  - `previous_version_id`
  - `effective_at`
  - `source_sha256`
  - `api_serial`
  - `git_commit` 또는 Git tag
  - `qa_status`
  - `occurred_at`

### OpenCrab의 한계

- 노출된 tool 계약에는 Git과 같은 branch/commit/merge/tag/checkout/diff primitive가 없다.
- `pack_update`의 version/event는 time-series 기록 수단이지, 원본 파일의 byte-level rollback 체계로 간주하면 안 된다.
- 전체 raw API/HWP를 cloud ingest하면 private pack이라도 로컬 밖으로 데이터가 이동한다.
- local folder를 SaaS MCP가 직접 읽지 않으므로 대형 corpus는 local builder/upload와 cloud pack 관리가 추가된다.
- embedding/chunking/index 갱신에 따라 동일 질의 결과가 변할 수 있으므로, 질의 결과만으로 역사적 사실을 재현하면 안 된다.
- pack update의 재시도·중복·부분 실패·이전 버전 필터를 프로젝트 규칙으로 별도 설계해야 한다.
- OpenCrab에만 원문을 넣으면 공급자 종속과 export/rollback 부담이 커진다.

### OpenCrab 사용 시 최소 안전 조건

- 기본은 private pack이며 marketplace/public share를 사용하지 않는다.
- 원문 전체보다 metadata + normalized semantic evidence를 우선 ingest한다.
- 모든 node/edge/evidence에 `version_id`, `source_path`, `source_sha256`, `git_commit`, `effective_at`을 연결한다.
- 질의에는 `as_of`, `version_id`, `effective_at` 조건을 강제한다.
- Git source snapshot이 존재하지 않는 OpenCrab event는 canonical amendment record로 인정하지 않는다.
- pack QA 결과와 ingest run ID를 version manifest에 되돌려 기록한다.

## 5. 직접 비교

### Git/GitHub가 우위인 항목

- 원본 보존
- exact diff
- byte/hash 기반 재현성
- 승인·review·rollback
- 변경 이력 감사
- offline/local 운영
- vendor lock-in 최소화

### OpenCrab이 우위인 항목

- 의미 기반 질의
- 기관 간 개념·관계 탐색
- 조문과 개정 이벤트의 graph navigation
- evidence retrieval
- graph QA와 downstream assistant 활용

### 둘 다 단독으로 부족한 항목

- 조문 번호가 달라진 split/merge 비교
- threshold/operator/exception의 법적 의미 비교
- 시행일과 적용례의 충돌 검토
- source label과 body effective date 불일치 처리

이 항목들은 별도 deterministic comparison pipeline과 사람 검토가 필요하다.

## 6. 결론

### 권장 결론

**Git/GitHub를 canonical version store로 사용하고, OpenCrab은 검증된 Git 산출물에서 파생하는 ontology/query layer로 사용한다.**

역할을 바꾸지 않는 것이 핵심이다.

```text
API/HWP source
    -> local parser + deterministic QA
    -> Git commit/tag/PR  [정본·버전·감사·rollback]
    -> OpenCrab private pack update  [의미 그래프·질의·탐색]
```

### 하나만 선택해야 한다면

**Git/GitHub를 선택한다.**

규정 개정 버전 관리의 1차 요구사항은 “과거 원본과 변경을 정확히 재현하는 것”이고, 이 부분은 Git이 더 직접적이고 검증 가능하다. OpenCrab은 그 위에 얹을 때 가치가 커진다.

## 7. 추천 도입 순서

1. 별도 GitHub private repository를 만든다. 현재 상위 `Agents_Private`에 무작정 섞기보다 프로젝트 전용 repo가 적합하다.
2. 현재 snapshot을 initial commit/tag로 고정한다.
3. `version_manifest`, source hash, parser version, structured diff, parameter diff 스키마를 먼저 고정한다.
4. 정기 API probe가 변경을 감지하면 새 version 디렉터리·diff·QA를 만들고 PR을 생성한다.
5. QA 통과 후 merge/tag한다.
6. merge된 version만 OpenCrab private project/pack에 update한다.
7. OpenCrab query 결과에는 반드시 version/effective date/source commit을 함께 표시한다.
8. 첫 OpenCrab pilot은 한 기관의 current snapshot과 다음 실제 개정본을 사용해 time-series/rollback/query 필터를 검증한 뒤 4개사로 확장한다.

## 8. 현재 판단

- Git/GitHub: **정본 버전관리로 즉시 적합**
- OpenCrab: **파생 ontology/query layer로 적합**
- OpenCrab 단독 정본화: **현재는 비추천**
- 다음 사용자 판단이 필요한 지점: 별도 GitHub private repository 생성 여부와 OpenCrab private pilot의 원문 포함 범위
