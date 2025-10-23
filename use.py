import diary
import json
#json 파일 경로
json_path=""

with open(f"{json_path}","r") as f:
    data = json.load(f)
'''
persona <- 0~2
0 : 반말? 채팅? 말투
1 : 카오모지 말투
2 : 로봇말투인데 잘 안나와요;;; <- 바꿀 예정
3 : 은 아직 설정 안했,,,
'''
persona=1
print(diary.get_response(data,persona=1))

