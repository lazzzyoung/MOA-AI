import os
import json
import tempfile
from typing import List, Literal, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables (.env)
load_dotenv()

# AI 엔진
import diary


# ─────────────────────────────────────────────────────────
# 입력 데이터 스키마 정의
# ─────────────────────────────────────────────────────────

AllowedTypesIn = Literal[
    "text",
    "image",
    "text+image",
    "image_with_text",
    "voice",
    "audio"
]


class DiaryItem(BaseModel):
    type: AllowedTypesIn
    content: Optional[str] = Field(default=None, description="텍스트 내용 (선택)")
    path: Optional[str] = Field(default=None, description="이미지 또는 오디오 경로/URL")


class GenerateRequest(BaseModel):
    items: List[DiaryItem]
    persona: int = Field(default=0, ge=0, le=3, description="0~3 사이의 페르소나 선택")


class GenerateResponse(BaseModel):
    diary: str


# ─────────────────────────────────────────────────────────
# FastAPI 초기화
# ─────────────────────────────────────────────────────────
app = FastAPI(title="MOA AI Diary Service", version="1.0.0")

# CORS 설정 (운영 환경에서는 Origin 제한 권장)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────
# 타입 매핑 함수
# ─────────────────────────────────────────────────────────
def map_type(t: str) -> str:
    """프론트에서 오는 타입명(text+image 등)을 내부 표준으로 매핑"""
    if t == "text+image":
        return "image_with_text"
    if t == "voice":
        return "audio"
    return t  # text, image, image_with_text, audio


# ─────────────────────────────────────────────────────────
# 헬스체크
# ─────────────────────────────────────────────────────────
@app.get("/health")
def health():
    """서버 정상 상태 확인"""
    return {"ok": True}


# ─────────────────────────────────────────────────────────
# 내부 변환 함수: items → 엔지니어 스키마(JSON 저장용)
# ─────────────────────────────────────────────────────────
def _to_engineer_schema(items: List[DiaryItem]):
    """
    FastAPI에서 받은 DiaryItem 리스트를
    AI 엔진이 사용하는 {"diaries": [{"recordList": [...]}]} 구조로 변환
    """
    record_list = []

    for it in items:
        t = map_type(it.type)

        # 텍스트 전용
        if t == "text":
            record_list.append({
                "type": "text",
                "context": it.content or "",
                "imageUrl": None
            })

        # 이미지 단독 or 텍스트+이미지
        elif t in ("image", "image_with_text", "text+image"):
            record_list.append({
                "type": "text+image" if t in ("image_with_text", "text+image") else "image",
                "context": it.content or "",
                "imageUrl": it.path or None
            })

        # 오디오 (STT된 텍스트가 content로 들어왔다고 가정)
        elif t == "audio":
            record_list.append({
                "type": "text",
                "context": it.content or "",
                "imageUrl": None
            })

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported type: {it.type}")

    return {"diaries": [{"recordList": record_list}]}


# ─────────────────────────────────────────────────────────
# 일기 생성 엔드포인트
# ─────────────────────────────────────────────────────────
@app.post("/diary/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest):
    """
    클라이언트에서 전송된 record 데이터를 기반으로
    AI 엔진(Google Gemini)을 호출하여 일기를 생성
    """
    # 키 체크
    if not os.getenv("GOOGLE_API_KEY"):
        raise HTTPException(status_code=500, detail="GOOGLE_API_KEY not set in .env")

    # 데이터 변환
    payload = _to_engineer_schema(req.items)

    # 임시 JSON 파일로 저장 (use.py, diary.py와 동일한 포맷)
    tmpdir = tempfile.mkdtemp(prefix="moa_ai_")
    json_path = os.path.join(tmpdir, "response.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    # Gemini 호출
    try:
        diary_text = diary.get_response(json_path, persona=req.persona)
        return GenerateResponse(diary=diary_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI generation failed: {e!s}")


# ─────────────────────────────────────────────────────────
# 로컬 실행 진입점
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=True
    )