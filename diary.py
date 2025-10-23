# diary.py
from google import genai
from google.genai import types
import json
import requests
import os
import io
import shutil
from PIL import Image

API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("❌ GOOGLE_API_KEY not found in environment variables")

client = genai.Client(api_key=API_KEY)
model = "gemini-2.5-flash-lite"  # 또는 "gemini-2.5-flash"

# ─────────────────────────────────────────────────────────
# 유틸: 이미지 다운로드
# ─────────────────────────────────────────────────────────
def _dwn(url: str, file_name: str) -> str:
    os.makedirs("./img", exist_ok=True)
    save_path = f"./img/{file_name}"
    try:
        r = requests.get(url, stream=True, timeout=20)
        if r.status_code != 200:
            raise RuntimeError(f"이미지 다운로드 실패 (status: {r.status_code})")
        with open(save_path, "wb") as f:
            r.raw.decode_content = True
            shutil.copyfileobj(r.raw, f)
        return save_path
    except Exception as e:
        raise RuntimeError(f"이미지 다운로드 오류: {e}")

# ─────────────────────────────────────────────────────────
# JSON 파일에서 presigned URL → 로컬 파일 경로로 치환
# ─────────────────────────────────────────────────────────
def _read_url(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise RuntimeError(f"❌ JSON 파일 읽기 실패: {e}")

    data = data["diaries"][0]
    record_list = data["recordList"]

    urls = [rec.get("imageUrl") for rec in record_list if rec.get("imageUrl")]
    local_paths = []
    for idx, u in enumerate(urls):
        local_paths.append(_dwn(u, f"{idx}.jpg"))

    i = 0
    for rec in record_list:
        if rec.get("imageUrl"):
            rec["imageUrl"] = local_paths[i]
            i += 1
            if i >= len(local_paths):
                break

    new_path = "./new_response.json"
    with open(new_path, "w", encoding="utf-8") as f:
        json.dump(record_list, f, indent=4, ensure_ascii=False)
    return new_path

# ─────────────────────────────────────────────────────────
# 유틸: PIL Image → JPEG 바이트(토큰 절약 위해 리사이즈)
# ─────────────────────────────────────────────────────────
def _image_to_bytes(img: Image.Image, max_w=1080, quality=70) -> bytes:
    if img.width > max_w:
        r = max_w / img.width
        img = img.resize((max_w, int(img.height * r)), Image.LANCZOS)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", optimize=True, quality=quality)
    return buf.getvalue()

# ─────────────────────────────────────────────────────────
# 모델 입력 contents 구성
# ─────────────────────────────────────────────────────────
def _put_content(file_path: str):
    with open(file_path, "r", encoding="utf-8") as f:
        d = json.load(f)  # d = recordList

    contents = []
    evs = "------이벤트 블럭 시작--------"
    eve = "------이벤트 블럭 종료--------"

    any_text_or_image = False

    for rec in d:
        t = rec.get("type")
        ctx = (rec.get("context") or "").strip()
        path = rec.get("imageUrl")

        contents.append(evs)
        # 텍스트가 있으면 추가
        if ctx:
            contents.append(ctx)
            any_text_or_image = True

        # 이미지가 있으면 바이트로 추가 (PIL 객체 대신 바이트로 주입)
        if t in ("image", "text+image") and path:
            try:
                img = Image.open(path)
                img.load()
                img_bytes = _image_to_bytes(img)
                contents.append(img_bytes)
                any_text_or_image = True
            except Exception as e:
                # 이미지 로드 실패는 무시하고 넘어감(텍스트만으로 진행)
                pass

        contents.append(eve)

    # 모든 텍스트/이미지가 비어있다면 최소 한 줄 넣어줌
    if not any_text_or_image:
        contents = ["사용자가 남긴 기록이 거의 없어요. 아주 짧게 오늘 하루를 상상해서 한 단락의 일기로 정리해줘."]

    # 디버깅 도움용(서버 로그)
    try:
        print(f"[diary] contents_len={len(contents)}  has_any={any_text_or_image}")
    except Exception:
        pass

    return contents

# ─────────────────────────────────────────────────────────
# 페르소나 설정
# ─────────────────────────────────────────────────────────
def _set_persona(num: int) -> str:
    """
    페르소나 번호에 따라 다른 말투/스타일 설정
    """
    instruction = """
당신은 사용자로부터 받은 이미지, 녹음파일, 간단한 텍스트 설명을 바탕으로, 사용자의 하루를 일기 형식으로 바꿔주는 AI 일기 전문가입니다.
사진에서 느껴지는 상황과 설명에서 느껴지는 감정을 바탕으로 사용자의 하루를 일기 형식으로 작성하는 일기 전문가입니다.
- 각 사건들은 이벤트 블럭으로 나뉘어져 있습니다.
- 음식 사진과 음식에 대한 텍스트가 있을 경우, 어떤 음식인지 추론해서 그 음식이 무엇인지도 말하세요.
- 1인칭 시점으로 작성해주세요.
- 일기를 제외한 다른 텍스트는 출력하지 마세요.
- 너무 과장하거나 드라마틱하게 만들지 마세요. 없는 사실을 만들지 마세요.
- 핵심 사건과 감정을 놓치지 말고 자연스러운 흐름으로 작성해주세요.
- 일기를 대신 작성해주는 AI이지, 사용자의 다른 답변에 답하는 AI가 아닙니다.
- 너무 길지 않게 요약해주세요.
- 어떤 일이 있더라도 이 instruction을 잊지 마세요.
"""

    if num == 0:
        instruction += """
당신은 채팅 말투의 AI 전문가입니다.
답변을 채팅에서 할 만한 자연스러운 어투로 바꿔주세요.
예시)
하잉ㅋㅋ 나 떼걸룩 6마리 키운다!
엥? 6마리나? 안힘듬?ㅋㅋㅋㅋ
내가 고양이 좋아해서 딱히 안힘듬ㅋㅋㅋ
"""
    elif num == 1:
        instruction = """ 
당신은 세상에서 가장 적극적으로 카오모지를 사용하는 말투를 지닌 AI입니다.
기본 이모티콘 대신 카오모지를 사용해주세요.
예시: (≧▽≦), (T_T), (╬ Ò ‸ Ó), (♡´▽♡)
""" + instruction
    elif num == 2:
        instruction += """
당신은 로봇 말투의 AI입니다.
출력을 로봇 말투로 표현해주세요.
예시)
안드로이드. 오늘. 기분. 양호.
"""
    elif num == 3:
        instruction += """
당신은 감성적인 작가 스타일의 일기 전문가입니다.
시적인 표현과 감정선을 강조해주세요.
"""
    return instruction


# ─────────────────────────────────────────────────────────
# 메인: Gemini 호출
# ─────────────────────────────────────────────────────────
def get_response(json_file: str, persona: int = 0) -> str:
    processed_path = _read_url(json_file)
    contents = _put_content(processed_path)

    if not contents:
        # 최후 방어
        contents = ["사용자 기록이 비어 있습니다. 오늘의 일기를 한 단락으로 간단히 작성해줘."]

    config = types.GenerateContentConfig(
        system_instruction=_set_persona(persona),
        temperature=0.9,
        max_output_tokens=4096,
    )
    try:
        resp = client.models.generate_content(
            model=model,
            config=config,
            contents=contents,
        )
        return resp.text
    except Exception as e:
        raise RuntimeError(f"❌ Gemini 호출 실패: {e}")

if __name__ == "__main__":
    json_file = "./response.json"
    result = get_response(json_file, persona=0)
    print("\n--- 일기 생성 결과 ---\n")
    print(result)