#-*- coding: utf-8 -*-

import quiz_list
import random
import voice
import time

def get_random_quiz():
    quiz_lists = quiz_list.quiz_lists
    random_quiz_number = random.randint(0, len(quiz_lists)-1)
    quiz = quiz_lists[random_quiz_number]

    quiz_answer = quiz["answer"]
    quiz_hints = quiz["question"]

    return quiz_answer, quiz_hints

def solve_quiz(quiz_answer, quiz_hints):
    score = 10

    for hint in quiz_hints:
        time.sleep(0.5)
        print("\n현재 점수는 %d점 입니다." % score)
        score_speech = "현재 점수는 %d점 입니다." % score
        voice.speech(score_speech)
        print("%d번 힌트 입니다." % (quiz_hints.index(hint) + 1))
        voice.speech("%d번 힌트 입니다." % (quiz_hints.index(hint) + 1))
        time.sleep(0.5)
        voice.speech(hint)
        time.sleep(0.5)
        voice.speech("정답은 무엇일까요?")
        input_text = voice.getVoice2Text()
        time.sleep(2)
        if input_text.find(quiz_answer) != -1:
            voice.speech("정답입니다.")
            return score
        elif input_text == "" or input_text.find("다음") != -1:
            voice.speech("다음 힌트를 잘 들어보세요")
            score -= 1
            time.sleep(1)
            continue
        else:
            voice.speech("땡 오답입니다.")
            score -= 2
            time.sleep(1)
            continue
        

    time.sleep(1)
    answer_text = "정답은 %s였습니다." % quiz_answer
    print(answer_text)
    return score

def main():
    voice.speech("지금부터 퀴즈를 시작하겠습니다. 힌트를 듣고 정답을 말해주세요...")
    time.sleep(1)
    quiz_answer, quiz_hint = get_random_quiz()
    result_score = solve_quiz(quiz_answer, quiz_hint)
    voice.speech("점수는 %d점 입니다." % result_score)

if __name__ == "__main__":
    main()