from google import genai
from google.genai import types
import json
import requests
import os
import shutil
from PIL import Image

# ─────────────────────────────────────────────────────────
# 기본 설정
# ─────────────────────────────────────────────────────────
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise RuntimeError("❌ GOOGLE_API_KEY not found in environment variables")

client = genai.Client(api_key=API_KEY)
model = "gemini-2.5-flash-lite"  # 또는 "gemini-2.5-flash"


# ─────────────────────────────────────────────────────────
# 이미지 다운로드 함수
# ─────────────────────────────────────────────────────────
def _dwn(url: str, file_name: str) -> str:
    """
    주어진 URL에서 이미지를 다운로드해 ./img 폴더에 저장하고 경로를 반환
    """
    os.makedirs("./img", exist_ok=True)
    save_path = f"./img/{file_name}"

    try:
        response = requests.get(url, stream=True, timeout=20)
        if response.status_code == 200:
            with open(save_path, 'wb') as file:
                response.raw.decode_content = True
                shutil.copyfileobj(response.raw, file)
            print(f"✅ 이미지 저장 완료: {save_path}")
            return save_path
        else:
            raise RuntimeError(f"이미지 다운로드 실패 (status: {response.status_code})")
    except Exception as e:
        raise RuntimeError(f"이미지 다운로드 중 오류 발생: {e}")


# ─────────────────────────────────────────────────────────
# JSON 파일에서 이미지 URL 읽고 로컬 이미지로 변환
# ─────────────────────────────────────────────────────────
def _read_url(path: str) -> str:
    """
    response.json 파일을 읽고, 내부의 imageUrl을 실제 파일 경로로 교체.
    새로운 JSON(new_response.json) 경로 반환
    """
    os.makedirs("./img", exist_ok=True)

    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        raise RuntimeError(f"❌ JSON 파일 읽기 실패: {e}")

    # diaries[0].recordList 안쪽 접근
    data = data['diaries'][0]
    record_list = data["recordList"]

    # imageUrl 리스트 수집
    urls = [rec.get("imageUrl") for rec in record_list if rec.get("imageUrl")]

    # 이미지 다운로드
    img_paths = []
    for idx, u in enumerate(urls):
        file_name = f"{idx}.jpg"
        img_paths.append(_dwn(u, file_name))

    # recordList 내부에 실제 파일 경로 매핑
    i = 0
    for rec in record_list:
        if rec.get("imageUrl"):
            rec["imageUrl"] = img_paths[i]
            i += 1
            if i >= len(img_paths):
                break

    # 새로운 JSON 저장
    new_path = "./new_response.json"
    with open(new_path, 'w', encoding='utf-8') as f:
        json.dump(record_list, f, indent=4, ensure_ascii=False)

    return new_path


# ─────────────────────────────────────────────────────────
# 이미지/텍스트를 모델 입력 형식으로 재조합
# ─────────────────────────────────────────────────────────
def _put_content(file_path: str):
    """
    JSON 파일(recordList)을 읽어 Gemini 모델 입력 형식(contents)으로 변환
    """
    

    with open(file_path, "r", encoding="utf-8") as f:
        d = json.load(f)

    l = []
    for rec in d:
        t = rec.get("type")
        ctx = rec.get("context") or ""

        if t in ("image", "text+image") and rec.get("imageUrl"):
            try:
                img = Image.open(rec["imageUrl"])
                l.append([ctx, img])
            except Exception as e:
                print(f"⚠️ 이미지 로드 실패: {rec['imageUrl']} ({e})")
                l.append([ctx, None])
        else:
            l.append([ctx, None])

    # 모델이 이해할 수 있도록 이벤트 블럭으로 구분
    evs = "------이벤트 블럭 시작--------"
    eve = "------이벤트 블럭 종료--------"
    con = []
    for ctx, img in l:
        con.append(evs)
        con.append(ctx)
        if img is not None:
            con.append(img)
        con.append(eve)
    return con


# ─────────────────────────────────────────────────────────
# 메인 함수: Gemini 호출
# ─────────────────────────────────────────────────────────
def get_response(json_file: str, persona: int = 0) -> str:
    """
    response.json 파일 경로를 받아, Google Gemini로 일기 생성 요청
    """
    # 1. 이미지 URL → 로컬 이미지로 교체
    processed_path = _read_url(json_file)

    # 2. 모델 입력 준비
    contents = _put_content(processed_path)

    # 3. 생성 설정
    config = types.GenerateContentConfig(
        system_instruction=_set_persona(persona),
        temperature=0.9,
        max_output_tokens=4096
    )

    # 4. Gemini 호출
    try:
        response = client.models.generate_content(
            model=model,
            config=config,
            contents=contents
        )
        print("✅ Gemini 응답 성공")
        return response.text
    except Exception as e:
        raise RuntimeError(f"❌ Gemini 호출 실패: {e}")


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
# 독립 실행 테스트
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    json_file = "./response.json"
    result = get_response(json_file, persona=0)
    print("\n--- 일기 생성 결과 ---\n")
    print(result)