"""Claude Code CLI 공급자.

별도의 ANTHROPIC_API_KEY 없이, 이미 인증된 로컬 `claude` CLI(Claude Code)를
서브프로세스로 호출해 LLM 응답을 받는다. 구독/키 등 Claude Code에 설정된 인증을
그대로 재사용하므로, API 키 발급이 어려운 경우의 검증/경량 사용에 적합하다.

주의: 호출마다 CLI 프로세스가 기동되어 직접 API 호출보다 느리고, 대량 배치보다는
표본 검증·경량 사용에 알맞다. 운영 서비스 배포에는 API 키 방식을 권장한다.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from typing import Any

from .base import LLMError, LLMProvider


class ClaudeCliProvider(LLMProvider):
    name = "claude_cli"

    def __init__(self, binary: str = "claude", model: str = "", timeout: int = 180) -> None:
        if not shutil.which(binary):
            raise LLMError(
                f"`{binary}` 실행파일을 찾을 수 없습니다. Claude Code가 설치·인증돼 있어야 합니다."
            )
        self._binary = binary
        self._model = model
        self._timeout = timeout
        # 프로젝트 CLAUDE.md/설정을 끌어오지 않도록 중립 작업디렉토리에서 실행
        self._cwd = tempfile.mkdtemp(prefix="csap_cli_")

    def complete_json(self, system: str, user: str) -> dict[str, Any]:
        # --system-prompt 로 에이전트 기본 프롬프트를 완전히 대체하고,
        # --setting-sources "" 로 프로젝트 설정 로딩을 막아 순수 Q&A로 호출한다.
        cmd = [
            self._binary,
            "-p",
            user,
            "--system-prompt",
            system,
            "--setting-sources",
            "",
            "--output-format",
            "json",
        ]
        if self._model:
            cmd += ["--model", self._model]

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self._timeout,
                cwd=self._cwd,
            )
        except subprocess.TimeoutExpired as exc:
            raise LLMError(f"claude CLI 시간초과({self._timeout}s)") from exc
        except OSError as exc:
            raise LLMError(f"claude CLI 실행 실패: {exc}") from exc

        if proc.returncode != 0:
            raise LLMError(f"claude CLI 오류(rc={proc.returncode}): {proc.stderr.strip()[:300]}")

        try:
            envelope = json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            raise LLMError(f"claude CLI 출력 파싱 실패: {proc.stdout[:300]!r}") from exc

        if envelope.get("is_error"):
            raise LLMError(f"claude CLI 응답 오류: {envelope.get('result', '')[:300]}")

        result_text = envelope.get("result", "")
        if not result_text:
            raise LLMError("claude CLI 응답에 result 가 없습니다.")
        return self._extract_json(result_text)
