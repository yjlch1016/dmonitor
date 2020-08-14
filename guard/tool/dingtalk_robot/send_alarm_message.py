"""
钉钉自定义机器人开发文档
https://ding-doc.dingtalk.com/doc#/serverapi2/qf2nxq
"""

import json
import time

import requests

from guard.tool.dingtalk_robot.dingtalk_signature import get_dingtalk_signature


def send_dingtalk_alarm(alarm_message, dingtalk_webhook, secret):
    """
    发送钉钉报警的方法
    :param alarm_message: 第一个参数为报警信息
    :param dingtalk_webhook: 第二个参数为钉钉机器人Webhook
    :param secret: 第三个参数为密钥
    :return:
    """

    headers = {
        "Content-Type": "application/json;charset=UTF-8"
    }
    # 请求头

    payload = {
        "msgtype": "text",
        "text": {
            "content": alarm_message
        },
        "at": {
            "atMobiles": [],
            "isAtAll": True
        }
    }
    # 请求体

    timestamp = str(round(time.time() * 1000))
    # 时间戳
    sign = get_dingtalk_signature(secret)
    # 签名

    url = dingtalk_webhook + "&timestamp=" + timestamp + "&sign=" + sign
    # https://oapi.dingtalk.com/robot/send?access_token=XXXXXX&timestamp=XXX&sign=XXX

    return requests.request("POST", url, data=json.dumps(payload), headers=headers).content.decode(
        "utf8")
    # 发起HTTP请求
