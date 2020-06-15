#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import audioop
from ctypes import *
import RPi.GPIO as GPIO
import ktkws # KWS
import MicrophoneStream as MS
import time

import grpc
import gigagenieRPC_pb2
import gigagenieRPC_pb2_grpc
import user_auth as UA
import os

KWSID = ['기가지니', '지니야', '친구야', '자기야']
RATE = 16000
CHUNK = 512

HOST = 'gate.gigagenie.ai'
PORT = 4080

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(29, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(31, GPIO.OUT)
btn_status = False

def callback(channel):  
	print("falling edge detected from pin {}".format(channel))
	global btn_status
	btn_status = True
	print(btn_status)

GPIO.add_event_detect(29, GPIO.FALLING, callback=callback, bouncetime=10)

ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)
def py_error_handler(filename, line, function, err, fmt):
  dummy_var = 0
c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
asound = cdll.LoadLibrary('libasound.so')
asound.snd_lib_error_set_handler(c_error_handler)



def detect():
    with MS.MicrophoneStream(RATE, CHUNK) as stream:            
        audio_generator = stream.generator()
        for content in audio_generator:
            rc = ktkws.detect(content)
            rms = audioop.rms(content,2)
            #print('audio rms = %d' % (rms))

            if (rc == 1):
                MS.play_file("../data/sample_sound.wav")
                return 200

def btn_detect():
    
    global btn_status
    with MS.MicrophoneStream(RATE, CHUNK) as stream:
            audio_generator = stream.generator()

            for content in audio_generator:
                GPIO.output(31, GPIO.HIGH)
                rc = ktkws.detect(content)
                rms = audioop.rms(content,2)
                #print('audio rms = %d' % (rms))
                GPIO.output(31, GPIO.LOW)
                if (btn_status == True):
                    rc = 1
                    btn_status = False			
                if (rc == 1):
                    GPIO.output(31, GPIO.HIGH)
                    MS.play_file("../data/sample_sound.wav")
                    return 200

def calltest(key_word = '기가지니'):
    rc = ktkws.init("../data/kwsmodel.pack")
    print ('init rc = %d' % (rc))
    rc = ktkws.start()
    print ('start rc = %d' % (rc))
    print ('호출어를 불러보세요~\n')
    ktkws.set_keyword(KWSID.index(key_word))
    rc = detect()
    print ('detect rc = %d' % (rc))
    print ('호출어가 정상적으로 인식되었습니다.\n')
    ktkws.stop()
    return rc

def btn_test(key_word = '기가지니'):
    global btn_status
    rc = ktkws.init("../data/kwsmodel.pack")
    print ('init rc = %d' % (rc))
    rc = ktkws.start()
    print ('start rc = %d' % (rc))
    print ('\n버튼을 눌러보세요~\n')
    ktkws.set_keyword(KWSID.index(key_word))
    rc = btn_detect()
    print ('detect rc = %d' % (rc))
    print ('호출어가 정상적으로 인식되었습니다.\n')
    ktkws.stop()
    return rc


def generate_request():
    with MS.MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
    
        for content in audio_generator:
            message = gigagenieRPC_pb2.reqVoice()
            message.audioContent = content
            yield message


def get_grpc_stub():
    channel = grpc.secure_channel('{}:{}'.format(HOST, PORT), UA.getCredentials())
    stub = gigagenieRPC_pb2_grpc.GigagenieStub(channel)
    return stub


def getVoice2Text():	
    print ("\n음성인식을 시작합니다.")
    #print("종료하시려면 Ctrl+\ 키를 누루세요.\n")
    stub = get_grpc_stub()
    request = generate_request()
    resultText = ''
    for response in stub.getVoice2Text(request):
        if response.resultCd == 200: # partial
            print('resultCd=%d | recognizedText= %s' 
                  % (response.resultCd, response.recognizedText))
            resultText = response.recognizedText
        elif response.resultCd == 201: # final
            print('resultCd=%d | recognizedText= %s' 
                  % (response.resultCd, response.recognizedText))
            resultText = response.recognizedText
            break
        else:
            print('resultCd=%d | recognizedText= %s' 
                  % (response.resultCd, response.recognizedText))
            break

    print ("\n인식결과: %s " % (resultText))
    return resultText


def getText2VoiceStream(inText,inFileName = 'tts.wav'):
    
    stub = get_grpc_stub()  
    message = gigagenieRPC_pb2.reqText()
    message.lang=0
    message.mode=0
    message.text=inText
    
    writeFile=open(inFileName,'wb')
    for response in stub.getText2VoiceStream(message):
       if response.HasField("resOptions"):
           #print ("\nResVoiceResult: %d" %(response.resOptions.resultCd))
           pass 
       if response.HasField("audioContent"):
           #print ("Audio Stream\n")
           writeFile.write(response.audioContent)
           
            
    writeFile.close()
    return True

def speech(text):
    result_code = getText2VoiceStream(text + "  ,,//")
    if result_code == True:
        MS.play_file('tts.wav')
        #print('음성이 출력되었습니다.\n\n')
    else:
        print('에러가 발생하였습니다.\n\n')

def queryByText(text):

    stub = get_grpc_stub()

    message = gigagenieRPC_pb2.reqQueryText()
    message.queryText = text
    message.userSession = "1234"
    message.deviceId = "yourdevice"
            
    response = stub.queryByText(message)

    #print ("resultCd: %d" % (response.resultCd))
    
    if response.resultCd == 200:
        print ("\n질의한 내용: %s" % (response.uword))
        #dssAction = response.action
        for a in response.action:
                response = a.mesg
        parsing_resp = response.replace('<![CDATA[', '')
        parsing_resp = parsing_resp.replace(']]>', '')
        print("질의에 대한 답변: " + parsing_resp + '\n')
        return parsing_resp
    
    else:
        print ("Fail: %d" % (response.resultCd))
        return None

def main():
    
    while 1:
        recog = calltest(KWSID[0])
        if recog == 200:
            recognized_text = getVoice2Text()
            result = queryByText(recognized_text)
            print(result)
            speech(result)
                    

if __name__ == '__main__':   
    main()
        