# Moa_AI



# 코드 사용법
## 데이터 입력 형식

### 텍스트

```json
[
    {
      "type":"text", 
      "content": "정독도서관 가는 지하철 탐\n잽싸게 앉음"
    }
]
```
### 이미지
```json

[
    {
      "type": "image",
      "path":"image_path"
    }
]
```


### 텍스트 + 이미지
```json
[
    {
      "type": "image_with_text",
      "content": "내려서 걷는데 너무 더움..",
      "path":"image_path"
    }
]
```
### 오디오

```json
[
    {
      "type": "audio",
      "path": "audio_path"
    }
]

```

## 호출 방법

```python
import gemini

json_file=[
    {
      "type": "image",
      "path":"image_path"
    },
    {
      "type": "image",
      "path":"image_path"
    },
    {
      "type": "image_with_text",
      "content": "내려서 걷는데 너무 더움..",
      "path":"image_path"
    },
    {
      "type": "audio",
      "path": "audio_path"
    }
]

get_response(json_file)

```
time_stamp 찍을수 있으면 해주세요

문자열로 리턴합니다

## 예시

```python
import diary
import json

#파일 경로 설정하면 됩니다.
with open("./js_file/example_data.json","r") as f:
    data = json.load(f)


# data=[
#     {"type":"image","path":"./img_file/riding.jpeg"},
#     {"type":"audio","path":audio_path},
#     {"type":"text","content":"수영하러 갔는데 카드를 안들고 와서 빠꾸먹었다 데스크 직원이 융통성 없게 말 질질 끌어서 화가났다"},
#     {"type":"text","content":"학생이 거의 한 수업 못 들을 정도로 늦게 왔다;\n남아서 랜덤테스트로 봐야하는데 그럼 자기 절대 못 한다고 해서 조금 봐줬다. 구두로 물어보면 잘 대답하면서 왜 못 한다는 지 모르겠다"},
#     {"type":"text","content":"퇴근하는데 버스 잘못타서 택시 탔다...\n알바하고 돈벌어서 바로 버리기"},
#     {"type":"image_with_text","path":img_path,"content":"여자친구랑 노래방 왔음"},
#     {"type":"text","content":"너무 졸려서 빨리 씻고 자야겠다"}
# ]
data=[
{"type": "image", "path": "./img_file/riding.jpeg"}, 
{"type": "audio", "path": "./voice_file/test_3.m4a"},
{"type": "text", "content": "\uc218\uc601\ud558\ub7ec \uac14\ub294\ub370 \uce74\ub4dc\ub97c \uc548\ub4e4\uace0 \uc640\uc11c \ube60\uafb8\uba39\uc5c8\ub2e4 \ub370\uc2a4\ud06c \uc9c1\uc6d0\uc774 \uc735\ud1b5\uc131 \uc5c6\uac8c \ub9d0 \uc9c8\uc9c8 \ub04c\uc5b4\uc11c \ud654\uac00\ub0ac\ub2e4"},
{"type": "text", "content": "\ud559\uc0dd\uc774 \uac70\uc758 \ud55c \uc218\uc5c5 \ubabb \ub4e4\uc744 \uc815\ub3c4\ub85c \ub2a6\uac8c \uc654\ub2e4;\n\ub0a8\uc544\uc11c \ub79c\ub364\ud14c\uc2a4\ud2b8\ub85c \ubd10\uc57c\ud558\ub294\ub370 \uadf8\ub7fc \uc790\uae30 \uc808\ub300 \ubabb \ud55c\ub2e4\uace0 \ud574\uc11c \uc870\uae08 \ubd10\uc92c\ub2e4. \uad6c\ub450\ub85c \ubb3c\uc5b4\ubcf4\uba74 \uc798 \ub300\ub2f5\ud558\uba74\uc11c \uc65c \ubabb \ud55c\ub2e4\ub294 \uc9c0 \ubaa8\ub974\uaca0\ub2e4"}, {"type": "text", "content": "\ud1f4\uadfc\ud558\ub294\ub370 \ubc84\uc2a4 \uc798\ubabb\ud0c0\uc11c \ud0dd\uc2dc \ud0d4\ub2e4...\n\uc54c\ubc14\ud558\uace0 \ub3c8\ubc8c\uc5b4\uc11c \ubc14\ub85c \ubc84\ub9ac\uae30"}, 
{"type": "image_with_text", "path": "./img_file/test_img3.jpg", "content": "\uc5ec\uc790\uce5c\uad6c\ub791 \ub178\ub798\ubc29 \uc654\uc74c"}, 
{"type": "text", "content": "\ub108\ubb34 \uc878\ub824\uc11c \ube68\ub9ac \uc53b\uace0 \uc790\uc57c\uaca0\ub2e4"}
]

print(diary.get_response(data))
```

```
#출력 결과(default)

오늘은 아침부터 조금 삐끗하는 일들이 있었네. 수영장에 가려고 설레는 마음으로 나섰는데, 글쎄 카드를 안 들고 온 거야! 결국 아쉽게도 발길을 돌려야 했어. 데스크 직원분이 조금만 더 융통성 있게 설명해 주셨으면 좋았을 텐데, 아쉬움이 컸던 시간이었지.

수업 시간에는 학생이 거의 한 수업을 놓칠 정도로 늦게 왔어. 남아서 랜덤 테스트를 봐야 하는데, 자기는 절대 못 한다고 해서 조금 마음이 쓰이더라. 말로는 질문에 곧잘 대답하는데, 왜 시험만 보면 그렇게 힘들어하는지 모르겠어. 살짝 봐주긴 했지만, 학생의 마음이 조금 복잡해 보였어.

퇴근길에는 또 예상치 못한 일이 생겼지 뭐야? 버스를 잘못 타는 바람에 결국 택시를 타고 말았어. 알바해서 번 돈이 순식간에 사라지는 기분이라 살짝 허탈하기도 했네.

그래도 하루의 마지막은 달콤했어! 사랑하는 여자친구랑 같이 노래방에 가서 신나게 노래도 부르고 즐거운 시간을 보냈거든. 역시 같이 있으면 힘이 나는 것 같아. 덕분에 그동안 쌓였던 피로와 스트레스가 싹 날아가는 기분이었어.

이리저리 부딪히고 다녔더니 몸이 정말 천근만근이네. 얼른 따뜻한 물에 씻고 푹 자야겠어. 내일은 오늘보다 더 행복한 하루가 되기를 바라며! 안녕.
```
```
# 출력 결과(이모티콘 적극 사용)
오늘 정말 정신없는 하루였어! ( T _ T )

아침부터 수영하러 갔는데, 글쎄 카드를 안 가져와서 입장을 못했지 뭐야! (＃`Д´) 데스크 직원분은 왜 그렇게 융통성 없이 굴던지, 진짜 짜증 지대로였어! ┻━┻ ︵ ╰( `□´ )╯ ︵ ┻━┻

다음으로 알바하러 갔는데, 학생 하나가 수업 시작 거의 다 끝나갈 때쯤 늦게 온 거야. 😥 랜덤 테스트로 다시 봐야 한다고 하니까 자기는 절대 못 한다고 떼를 쓰길래, 그냥 봐줬지 뭐야. 구두로 물어보면 잘 대답하면서 왜 못 한다는 건지 아직도 모르겠어. (¬_¬ )

퇴근길에는 버스를 잘못 타서 결국 택시 탔어... ( ; _ ; ) 알바해서 번 돈, 고스란히 택시비로 날려버렸네. 💸💸

그래도 저녁에는 여자친구랑 노래방 가서 신나게 놀았지! (☆▽☆) 스트레스 풀리는 기분이었어~ ٩(ˊᗜˋ*)و

하루 종일 왜 이렇게 정신이 없던 건지, 너무 졸려서 빨리 씻고 자야겠다! (´-ω-`) 내일은 좀 더 평탄한 하루가 되기를 바라야지! (人´∀｀)．☆．。．:*･ﾟ
```
