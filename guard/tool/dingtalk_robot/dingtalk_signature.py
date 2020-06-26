import hmac
import hashlib
import base64
import time
import urllib.parse


def get_dingtalk_signature():
    # 获取签名的方法

    timestamp = str(round(time.time() * 1000))
    # 时间戳
    secret = "ABCDEFG"
    # 密钥

    secret_enc = secret.encode('utf-8')
    string_to_sign = '{}\n{}'.format(timestamp, secret)
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))

    return sign
