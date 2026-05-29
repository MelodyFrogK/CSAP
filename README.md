# CSAP 명세서 자동 작성 서비스

기업이 제출한 문서(PDF·Word 등)를 입력하면, **KISA CSAP 명세서 엑셀**의 각 점검항목에
대해 **현황**과 **보완사항**을 LLM이 자동으로 작성해 주는 웹 서비스입니다.

```
[명세서 엑셀 템플릿]  +  [기업 문서 PDF/Word]
            │
            ▼
  문서 텍스트 추출 → 청크 분할 → 항목별 관련 근거 검색
            │
            ▼
   항목별 LLM 작성 (현황 / 보완사항 / 충족도 / 근거)
            │
            ▼
      원본 양식 그대로 + 결과 열이 채워진 엑셀 다운로드
```

## 특징

- **양식 자동 인식**: 헤더 문구(항목번호·통제분야·점검내용 등)로 열을 자동 매핑하므로
  KISA 양식을 코드 수정 없이 그대로 사용. 결과 열은 원본 끝에 추가합니다.
- **LLM 공급자 추상화**: `anthropic`(Claude) / `openai` / `echo`(키 없이 데모) 전환.
- **근거 기반 작성**: 문서에 실제 근거가 있는 내용만 현황에 작성하도록 프롬프트 설계.
  근거가 없으면 충족도를 `확인불가`로 표기.
- **웹 UI + CLI** 둘 다 제공. 백그라운드 작업 + 진행률 표시.

## 빠른 시작

```bash
pip install -r requirements.txt

# 1) 데모용 샘플 명세서 템플릿 생성 (실제 KISA 엑셀이 있으면 생략 가능)
python scripts/make_sample_template.py

# 2) 설정 (키 없이 먼저 돌려보려면 echo 공급자)
cp .env.example .env
#   .env 에서 CSAP_LLM_PROVIDER=echo 로 두면 키 없이 데모 동작

# 3) 웹 서버 실행
uvicorn app.main:app --reload
#   http://127.0.0.1:8000 접속 → 문서 업로드 → 결과 엑셀 다운로드
```

### CLI

```bash
python -m app.cli --template data/sample_csap_template.xlsx \
    --out 결과.xlsx  docs/정보보호정책.pdf docs/운영매뉴얼.docx
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

## 실제 KISA 명세서 사용하기

1. 웹 UI의 **① 명세서 템플릿**에 실제 `.xlsx`를 업로드하거나,
2. `data/sample_csap_template.xlsx`를 실제 파일로 교체합니다.

열 인식은 `app/parsing/template.py`의 `_HEADER_KEYWORDS`로 동작합니다.
실제 양식의 헤더 문구가 키워드와 다르면 거기에 추가하면 됩니다.

## 프로젝트 구조

```
app/
  config.py              설정(.env)
  models.py              ControlItem / ItemResult / TemplateLayout
  main.py                FastAPI 웹 서비스
  cli.py                 커맨드라인 실행기
  llm/                   공급자 추상화 (anthropic/openai/echo)
  parsing/
    documents.py         PDF·DOCX·txt 텍스트 추출
    template.py          명세서 엑셀 → 항목/열배치 인식
    excel_writer.py      결과를 원본 양식에 기록
  core/
    retrieval.py         청크 분할 + 항목별 관련 근거 검색
    prompts.py           시스템/유저 프롬프트
    pipeline.py          전체 오케스트레이션
  web/templates/index.html   업로드 UI
scripts/make_sample_template.py   샘플 템플릿 생성
tests/                   스모크 테스트 (echo 공급자)
```

## 테스트

```bash
CSAP_LLM_PROVIDER=echo PYTHONPATH=. pytest -q
```

## 로드맵 / 다음 단계

- [ ] HWP(.hwp/.hwpx) 입력 지원
- [ ] 어휘 기반 검색 → 임베딩 기반 검색으로 고도화
- [ ] 작업 상태/결과 영속화(현재 단일 프로세스 메모리)
- [ ] 항목별 근거 셀 코멘트/하이퍼링크로 추적성 강화

## 주의

생성 결과는 **초안**입니다. 인증 제출 전 담당자의 검토·보완이 반드시 필요합니다.
`echo` 공급자 출력은 형식 확인용 더미이며 실제 분석이 아닙니다.
