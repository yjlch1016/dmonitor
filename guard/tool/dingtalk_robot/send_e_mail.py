from django.core.mail import send_mail

from dmonitor import settings


def send_mailbox(e_mail_content, recipient_email):
    """
    发送邮件报警的方法
    :param e_mail_content: 第一个参数为报警信息
    :param recipient_email: 第二个参数为收件人邮箱
    :return:
    """

    send_mail(
        '钉钉报警',
        e_mail_content,
        settings.DEFAULT_FROM_EMAIL,
        [recipient_email],
        fail_silently=False)
    # send_mail的参数分别是
    # 邮件标题
    # 邮件内容
    # 发件箱(settings.py中设置的那个)
    # 收件箱列表(可以发送给多个人)
    # 失败静默
