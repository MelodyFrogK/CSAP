# CSAP 명세서 자동 작성 서비스

기업이 제출한 문서(PDF·Word·zip 등)를 입력하면, **KISA 클라우드 보안인증(CSAP) 명세서**
엑셀의 각 **점검항목**에 대해 **운영여부(Y/N) / 운영현황 / 관련문서 / 운영증적**을 기존 양식에
그대로 채우고, 오른쪽에 **보조 열**(자동 판정·판단 근거·보완사항·준비 권장 증적·검토 필요)을
LLM이 자동으로 작성해 주는 웹 서비스입니다.

```
명세서 엑셀(KISA 양식)  +  기업 문서(PDF/Word/zip)
        │
        ▼
 문서 텍스트 추출 → 청크 분할 → 점검항목별 관련 근거 검색
        │
        ▼
 점검항목별 LLM 작성 (운영여부 / 운영현황 / 관련문서 / 운영증적 + 보조 열)
        │
        ▼
 원본 양식·서식 그대로 + 결과 열이 채워진 엑셀 다운로드
```

## 지원하는 실제 KISA 명세서 구조

실제 CSAP 심사에 사용된 명세서(SaaS 표준·간편 등)로 검증했습니다. 여러 레이아웃을
자동 인식하며, 헤더는 보통 **4행**, 데이터는 **5행**부터입니다. `작성방법` 시트의 공식
기준(운영여부 Y/N, 운영현황 육하원칙, 관련문서+증적 색인)을 반영합니다.

| 레이아웃 | 시트 예시 | 입력 열 | 결과 열(템플릿에 이미 존재) |
|---|---|---|---|
| 표준(최대 17열) | 1.관리적 / 3.기술적 / 4.국가기관 보호조치 | 분야·통제항목·세부통제·세부통제내용·**관련법규**·**점검항목**·해설(2024.6/2024.7) | **운영여부(Y/N)**·운영현황·관련문서·운영증적·담당자 *(점검결과·심사위원 등 평가자 열은 보존)* |
| 간편/갱신 | 1.관리적 / 3.기술적 / 4.국가기관 | 분야·통제항목·세부통제·**점검항목**·해설 | (평가기관현황·최초심사현황·)운영현황·관련문서·운영증적·담당자 |

- **점검항목(질문)** 단위로 작성합니다. 분야/통제항목/세부통제내용/관련법규는 블록 첫 행에만
  채워져 있으므로 아래 행으로 자동 보정(forward-fill)합니다.
- 점검항목 해설이 여러 버전이면 **가장 최신본**을 사용합니다.
- 결과는 템플릿에 **이미 있는** 운영여부(Y/N)·운영현황·관련문서·운영증적 열에 채웁니다.
- 템플릿에 없는 **보조 열만 맨 오른쪽(평가자 열 뒤)에 추가**합니다:
  **① 자동 판정(상세)** 운영/부분운영/미운영/해당없음/확인불가 · **② 판단 근거**(해설 요건 대조) ·
  **③ 보완사항** · **④ 준비 권장 증적·문서**(색인 예: `1.1.1.1-1`) · **⑤ 검토 필요**(Y/공백).
- **증적확인 담당자**, **점검결과·점검결과 근거·심사위원** 등 평가자/사람이 채울 열은 건드리지 않습니다.
- `작성방법` 등 안내 시트는 건너뜁니다.
- 일부 파일은 빈 셀이 100만 행까지 서식 지정돼 있어, 표 끝 이후의 유령 행을 정리해
  저장 속도와 결과 파일 크기를 줄입니다.

## 빠른 시작

```bash
pip install -r requirements.txt

# 1) 데모용 샘플 템플릿 생성 (실제 KISA 엑셀이 있으면 생략하고 UI에서 업로드)
python scripts/make_sample_template.py

# 2) 설정 (키 없이 먼저 돌려보려면 echo 공급자)
cp .env.example .env

# 3) 웹 서버 실행
uvicorn app.main:app --reload
#   http://127.0.0.1:8000 → 명세서 엑셀 + 기업 문서 업로드 → 결과 다운로드
```

### CLI

```bash
python -m app.cli --template "클라우드보안운영명세서.xlsx" \
    --out 결과.xlsx  정보보호정책서.pdf 접근통제지침.docx
```

## 실제 LLM 연결

`.env` 에서 공급자를 선택합니다. 4가지를 지원합니다.

### A) 별도 API 키 없이 — Claude Code 재사용 (권장: 키 발급이 부담될 때)

이미 설치·인증된 `claude` CLI(Claude Code)를 그대로 사용합니다. **추가 API 키가 필요 없습니다.**

```ini
CSAP_LLM_PROVIDER=claude_cli
CSAP_CLAUDE_CLI_MODEL=        # 빈 값=기본 모델. claude-haiku-4-5(저렴)/claude-sonnet-4-6 등
```

> 호출마다 CLI 프로세스가 떠서 직접 API보다 느립니다(항목당 수 초). 표본 검증·경량 사용에
> 적합하며, 대량/운영 배포에는 아래 API 키 방식을 권장합니다. Claude Code에 설정된 인증
> (구독 또는 키)을 따릅니다.

### B) Anthropic API 키

```ini
CSAP_LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
CSAP_ANTHROPIC_MODEL=claude-sonnet-4-6
```

### C) OpenAI API 키

```ini
CSAP_LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
CSAP_OPENAI_MODEL=gpt-4o
```

### D) echo (데모 더미)

키 없이 형식만 확인하는 더미입니다(실제 분석 아님).

### 실 LLM 출력 품질 검증 (표본)

전체를 다 돌리기 전에, 대표 점검항목 표본만 호출해 출력 품질을 확인합니다.

```bash
# 별도 키 없이 Claude Code 재사용
export CSAP_LLM_PROVIDER=claude_cli
python scripts/verify_llm.py --template "명세서.xlsx" --limit 10 회사문서.pdf

# 또는 API 키 사용
export CSAP_LLM_PROVIDER=anthropic ANTHROPIC_API_KEY=sk-ant-...
python scripts/verify_llm.py --template "명세서.xlsx" --limit 10 회사문서.pdf
```

- 시트 전반에 고르게 표본을 뽑아(근거 있음/없음이 섞이도록) LLM을 호출합니다.
- 결과를 `verify_report.md`(사람이 보기 좋은 표) + `verify_report.json`(원시)로 저장합니다.
- 확인 포인트: 문서에 없는 주제가 `확인불가`로 나오는지(환각 여부), 근거 있는 항목의
  현황이 사실과 맞는지, 보완사항이 구체적인지. (상세: `docs/prompt_quality_notes.md`)

## 프로젝트 구조

```
app/
  config.py              설정(.env)
  models.py              ControlItem / ItemResult / SheetLayout
  main.py                FastAPI 웹 서비스
  cli.py                 커맨드라인 실행기
  llm/                   공급자 추상화 (anthropic/openai/echo)
  parsing/
    documents.py         PDF·DOCX·txt 텍스트 추출
    template.py          KISA 명세서 → 시트별 점검항목/열배치 인식 + forward-fill
    excel_writer.py      결과를 원본 양식에 기록(+보완사항 열 추가)
  core/
    retrieval.py         청크 분할 + 점검항목별 근거 검색
    prompts.py           시스템/유저 프롬프트(KISA 필드)
    pipeline.py          전체 오케스트레이션(다중 시트)
  web/templates/index.html   업로드 UI
scripts/make_sample_template.py   샘플 템플릿(실제 레이아웃 모사)
tests/                   스모크 테스트 (echo 공급자)
docs/roadmap.md          향후 서비스(증적자료 제출목록·신청양식) 계획
docs/prompt_quality_notes.md  프롬프트 품질 점검·보강 노트
```

## 테스트

```bash
CSAP_LLM_PROVIDER=echo PYTHONPATH=. pytest -q
```

## 로드맵 — 향후 추가 서비스

본 1단계는 **명세서 점검항목 작성**입니다. 동일 입력 문서를 재사용해 다음 산출물을
추가할 계획입니다(상세: [`docs/roadmap.md`](docs/roadmap.md)).

- [ ] **사후 서면평가 증적자료 제출목록** 자동 매핑/생성
- [ ] **신청양식** 자동 초안 작성
- [ ] HWP(.hwp/.hwpx) 입력 지원
- [ ] 어휘 기반 검색 → 임베딩 기반 검색 고도화
- [ ] 작업 상태/결과 영속화(현재 단일 프로세스 메모리)

## 주의

생성 결과는 **초안**입니다. 인증 제출 전 담당자의 검토·보완이 반드시 필요합니다.
