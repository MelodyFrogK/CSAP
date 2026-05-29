# CSAP 명세서 자동 작성 서비스

기업이 제출한 문서(PDF·Word 등)를 입력하면, **KISA 클라우드 보안인증(CSAP) 명세서**
엑셀의 각 **점검항목**에 대해 **운영 현황 / 운영여부 / 관련문서 / 운영 증적 / 보완사항**을
LLM이 자동으로 작성해 주는 웹 서비스입니다.

```
명세서 엑셀(KISA 양식)  +  기업 문서(PDF/Word)
        │
        ▼
 문서 텍스트 추출 → 청크 분할 → 점검항목별 관련 근거 검색
        │
        ▼
 점검항목별 LLM 작성 (운영여부 / 운영 현황 / 관련문서 / 운영 증적 / 보완사항)
        │
        ▼
 원본 양식·서식 그대로 + 결과 열이 채워진 엑셀 다운로드
```

## 지원하는 실제 KISA 명세서 구조

업로드한 실제 KISA 양식(여러 등급) 5종으로 검증했습니다. 두 가지 레이아웃을 모두
자동 인식합니다. 헤더는 보통 **4행**, 데이터는 **5행**부터입니다.

| 레이아웃 | 시트 예시 | 입력 열 | 결과 열(템플릿에 이미 존재) |
|---|---|---|---|
| A (11열) | 1.관리적 / 2.물리적 / 3.기술적 / 4.국가기관 보호조치 | 분야·통제항목·세부통제·세부통제내용·**점검항목**·해설 | 운영여부·운영현황·관련문서·운영증적·담당자 |
| B (8열) | (해당시)전자우편·화상회의·생성형AI 보안 | 분야·**점검항목**·해설 | 운영여부·운영현황·관련문서·운영증적·담당자 |

- **점검항목(질문)** 단위로 작성합니다. 분야/통제항목/세부통제내용은 블록 첫 행에만
  채워져 있으므로 아래 행으로 자동 보정(forward-fill)합니다.
- 결과는 템플릿에 **이미 있는** 운영여부·운영현황·관련문서·운영증적 열에 채웁니다.
- 템플릿에 없는 **「보완사항」 열만 끝에 추가**합니다. **증적확인 담당자** 열은 사람이
  채워야 하므로 비워 둡니다.
- `작성방법` 등 안내 시트는 건너뜁니다.

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

`.env`:

```ini
# Claude
CSAP_LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
CSAP_ANTHROPIC_MODEL=claude-sonnet-4-6

# 또는 OpenAI
CSAP_LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
CSAP_OPENAI_MODEL=gpt-4o
```

`echo` 공급자는 키 없이 형식만 확인하는 **데모 더미**입니다(실제 분석 아님).

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
