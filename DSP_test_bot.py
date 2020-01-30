import telepot
from telepot.loop import MessageLoop
import cv2 as cv
import tempfile
import urllib3
import os
import subprocess
from requests import get
from random import randint
from time import sleep
from json import loads
from os import path, mkdir

# Proxy for free PythonAnywhere platform account. If you are running it on PythonAnywhere then uncomment this  part.
# proxy_url = "http://proxy.server:3128"
# telepot.api._pools = {
#     'default': urllib3.ProxyManager(proxy_url=proxy_url, num_pools=3, maxsize=10, retries=False, timeout=30),
# }
# telepot.api._onetime_pool_spec = (urllib3.ProxyManager, dict(proxy_url=proxy_url, num_pools=1, maxsize=1, retries=False, timeout=30))
# end of the stuff that's only needed for free PythonAnywhere account

def user_folder_checker(user_id):
    #Create dir named by user id which will hold users files
    if not path.exists(str(user_id)):
        os.mkdir(str(user_id))

def get_file_path(token, file_id):
    get_path = get('https://api.telegram.org/bot{}/getFile?file_id={}'.format(token, file_id))
    json_doc = loads(get_path.text)
    try:
        file_path = json_doc['result']['file_path']
    except Exception as e:
        print('Cannot download a file because the size is more than 20MB')
        return None

    return 'https://api.telegram.org/file/bot{}/{}'.format(token, file_path)

def get_audio_fie(msg_list, content_type, user_id):

    audio_file_index = 0

    if len(msg_list) > 1:
        msg_count = len(msg_list)
        print('Total files: {}'.format(msg_count))


    user_folder_checker(user_id)

    last_saved_audio_index = str(user_id) + '/last_saved_audio_index.txt'

    if path.exists(last_saved_audio_index):
        temp = open(last_saved_audio_index).readline()
        audio_file_index = int(temp) + 1


    for msg in msg_list:
        file_id = msg['message'][content_type]['file_id']


        download_url = get_file_path(bot_token, file_id)
        file = get(download_url)

        filename = str(user_id) +'/audio_message_' + str(audio_file_index) + '_temp.wav'

        with open(filename, 'wb') as f:
            f.write(file.content)


        # saving last audio file index
        temp = open(last_saved_audio_index,'w')
        file_id = str(audio_file_index)
        temp.write(file_id)
        temp.close()

        return filename


def handle(msg):
    content_type, chat_type, user_id = telepot.glance(msg)
    usermsg = bot.getUpdates(allowed_updates='message')

    if content_type == 'voice':

        filename = get_audio_fie(usermsg, content_type ,user_id)

        # Changing sampling rate of the audio to 16KHz
        new_filename = ''.join(filename.split("_temp"))
        process = subprocess.run(['ffmpeg', '-i', filename,'-ar','16000', new_filename])
        if process.returncode != 0:
            bot.sendMessage(user_id, 'Something went wrong in the process of saving audio file.')
            raise Exception("Something went wrong")
        else:
            os.remove(filename)
            bot.sendMessage(user_id, 'Your audio was succesfully saved and converted to .wav file with sampling rate 16kHz.')

    elif content_type == 'photo':

        #Creating temporary file for opencv
        f = tempfile.NamedTemporaryFile(delete=True).name+".png"
        photo = msg['photo'][-1]["file_id"]
        bot.download_file(photo, f)
        bot.sendMessage(user_id, 'Your photo is being processed. Wait a few seconds please.')

        #Face detection part

        p = cv.imread(f)
        g = cv.cvtColor(p, cv.COLOR_BGR2GRAY)

        # Here you need to put your OWN path to 'haarcascade_frontalface_default.xml' file
        face_cascade = cv.CascadeClassifier('haarcascade_frontalface_default.xml')
        faces_rects = face_cascade.detectMultiScale(g, 1.1, 4)

        # number of faces found
        print('Faces found: ', len(faces_rects))
        if len(faces_rects) > 0:

            #Create dir named by user id which will hold users files if there is no any
            user_folder_checker(user_id)

            #There is at least 1 face detected
            last_saved_photo_index = str(user_id) + '/last_saved_photo_index.txt'
            photo_file_index = 0

            # Check if there is txt file for saving last index of saved photo
            if path.exists(last_saved_photo_index):
                temp = open(last_saved_photo_index).readline()
                photo_file_index = int(temp) + 1

            #Saving photo
            filename = str(user_id) +'/photo_message_' + str(photo_file_index) + '.png'
            cv.imwrite(filename, p)

            #Saving last file index
            temp = open(last_saved_photo_index,'w')
            file_id = str(photo_file_index)
            temp.write(str(photo_file_index))
            temp.close()

            bot.sendMessage(user_id, 'Picture with human face detected. File saved')
        else:
            bot.sendMessage(user_id, 'Picture is with NO human face.')
    else:
        bot.sendMessage(user_id, 'Sorry, we only accept audio and photo.')


bot_token = "YOUR TOKEN"
bot = telepot.Bot(bot_token)
bot.message_loop(handle)

