from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ImageMessage, ImageSendMessage
import os
from pathlib import Path
import subprocess
import time
import shlex

app = Flask(__name__)

ECHO_BOT_ACCESS_TOKEN = os.environ["ECHO_BOT_ACCESS_TOKEN"]
ECHO_BOT_CHANNEL_SECRET = os.environ["ECHO_BOT_CHANNEL_SECRET"]

FQDN = "https://d4654258.ngrok.io"

line_bot_api = LineBotApi(ECHO_BOT_ACCESS_TOKEN)
handler = WebhookHandler(ECHO_BOT_CHANNEL_SECRET)

SRC_IMAGE_PATH = "static/images/{}.jpg"
MAIN_IMAGE_PATH = "static/images/{}_main.jpg"
PREVIEW_IMAGE_PATH = "static/images/{}_preview.jpg"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    
    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.message.text == "画像認識":
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text="好きな画像を送ってね！（処理に少し時間がかかるから5秒ぐらい待ってね")
    )
    else:
        line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=event.message.text)
    )

@handler.add(MessageEvent, message=ImageMessage)
def handle_image(event):
    message_content = line_bot_api.get_message_content(event.message.id)

    with open("static/images/" + event.message.id + ".jpg", "wb") as f:
        f.write(message_content.content)

    # time.sleep(3)
    command = "python3 TFLite_detection_image.py --modeldir=Sample_TFLite_model --image=static/images/{}.jpg".format(event.message.id)
    # subprocess.run([command], cwd="/home/pi/line-bot")
    detect = subprocess.Popen(
        shlex.split(command),
        cwd='/home/pi/line-bot',
    )
    detect.wait()
    line_bot_api.reply_message(
        event.reply_token,
        ImageSendMessage(
            original_content_url=FQDN + "/static/images/result.jpg",
            preview_image_url=FQDN + "/static/images/result.jpg"
        )
    )

    os.remove("static/images/{}.jpg".format(event.message.id))
    # message_id = event.message.id

    # src_image_path = Path(SRC_IMAGE_PATH.format(message_id)).absolute()
    # main_image_path = MAIN_IMAGE_PATH.format(message_id)

    # save_image(message_id, src_image_path)

    # image_message = ImageSendMessage(
    #     original_content_url=Path(main_image_path).absolute(), 
    #     preview_image_url=Path(main_image_path).absolute()
    # )

    # # app.logger.info()
    # line_bot_api.reply_message(event.reply_token, image_message)

# def save_image(message_id: str, save_path: str):
#     message_content = line_bot_api.get_message_content(message_id)
#     with open(save_path, "wb") as f:
#         for chunk in message_content.iter_content():
#             f.write(chunk)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)