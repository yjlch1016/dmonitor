from django.core.mail import send_mail

from dmonitor import settings


def send_mailbox(e_mail_content):
    send_mail(
        '生产环境钉钉报警',
        e_mail_content,
        settings.DEFAULT_FROM_EMAIL,
        ['eee@www.fff.com'],
        fail_silently=False)
# send_mail的参数分别是
# 邮件标题
# 邮件内容
# 发件箱(settings.py中设置的那个)
# 收件箱列表(可以发送给多个人)
# 失败静默
