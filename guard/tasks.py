# Create your tasks here

from __future__ import absolute_import, unicode_literals

import json
import logging
import re
from itertools import chain

import demjson
import requests
from django.utils.datetime_safe import datetime

from guard.models import Microservice, Case, RunningResults, Step
from guard.tool.common_encapsulation.function_assistant import function_dollar, function_rn, function_rl, function_mp
from guard.tool.dingtalk_robot.alarm_text import http_request_exception_alarm, response_time_alarm, \
    response_result_alarm, response_code_alarm
from guard.tool.dingtalk_robot.send_alarm_message import send_dingtalk_alarm
from dmonitor.celery import app
from guard.tool.dingtalk_robot.send_e_mail import send_mailbox

logger = logging.getLogger(__name__)


@app.task
def run_all():
    logger.info("**********本轮调度程序准备好了**********\n")

    global pass_status, fail_reason, actual_result_text_re
    variable_result_dict = {}
    # 定义一个变量名与提取的结果字典

    microservice_id_object = Microservice.objects.values_list("id").filter(
        microservice_on_off="开").order_by("id")
    # 查询微服务开关=开的微服务id
    microservice_id_list = list(microservice_id_object)
    microservice_id_list = list(chain.from_iterable(microservice_id_list))

    data_object = Case.objects.values_list("id").filter(
        case_on_off="开", case_microservice__in=microservice_id_list).order_by("id")
    # 反向查询微服务包含的用例信息
    data_tuple = tuple(data_object)
    # 把QuerySet对象转换成元祖
    data_tuple = tuple(chain.from_iterable(data_tuple))
    # 把多维元祖转换成一维元祖

    for case_i in data_tuple:
        case_object = Case.objects.get(id=case_i, case_on_off="开").step_key.values().order_by("id")
        # 反向查询用例包含的步骤信息
        case_name = Case.objects.get(id=case_i).case_name
        logger.info("用例名称为：{}".format(case_name))
        case_list = list(case_object)
        # 把QuerySet对象转换成列表
        for step_i in case_list:
            step_id = step_i["id"]
            step_name = step_i["step_name"]
            request_mode = step_i["request_mode"]
            api = step_i["api"]
            body = step_i["body"]
            headers = step_i["headers"]
            query_string = step_i["query_string"]
            expected_time = step_i["expected_time"]
            expected_code = step_i["expected_code"]
            expected_result = step_i["expected_result"]
            regular = step_i["regular"]

            if variable_result_dict:
                if api:
                    api = function_dollar(api, variable_result_dict.items())
                if body:
                    body = function_dollar(body, variable_result_dict.items())
                if headers:
                    headers = function_dollar(headers, variable_result_dict.items())
                if query_string:
                    query_string = function_dollar(query_string, variable_result_dict.items())
                if expected_result:
                    expected_result = function_dollar(expected_result, variable_result_dict.items())

            if api:
                api = function_rn(api)
                api = function_rl(api)
            if body:
                body = function_rn(body)
                body = function_rl(body)
                body = function_mp(body)
                body = json.loads(body)
            if headers:
                headers = function_rn(headers)
                headers = function_rl(headers)
                headers = function_mp(headers)
                headers = json.loads(headers)
            if query_string:
                query_string = function_rn(query_string)
                query_string = function_rl(query_string)
                query_string = function_mp(query_string)
                query_string = json.loads(query_string)

            logger.info("步骤名称为：{}".format(step_name))
            service_domain = Step.objects.get(
                id=step_id).step_case.case_microservice.microservice_environment.domain_name
            url = service_domain + api
            logger.info("请求地址为：{}".format(url))
            dingtalk_switch = Step.objects.get(id=step_id).step_case.dingtalk_on_off
            logger.info("钉钉开关为：{}".format(dingtalk_switch))
            e_mail_switch = Step.objects.get(id=step_id).step_case.mailbox_on_off
            logger.info("邮件开关为：{}".format(e_mail_switch))

            try:
                response = requests.request(
                    request_mode, url, data=json.dumps(body),
                    headers=headers, params=query_string, timeout=(15, 20)
                )
                logger.info("HTTP请求成功")
            except Exception as e:
                logger.error("HTTP请求发生错误：{}".format(e))
                if dingtalk_switch == "开":
                    alarm_message = http_request_exception_alarm(
                        case_name, step_name, url, request_mode,
                        json.dumps(body, ensure_ascii=False),
                        json.dumps(headers, ensure_ascii=False),
                        json.dumps(query_string, ensure_ascii=False),
                        str(e))
                    send_dingtalk_alarm(alarm_message)
                    logger.info("钉钉报警发送成功")
                if e_mail_switch == "开":
                    alarm_message = http_request_exception_alarm(
                        case_name, step_name, url, request_mode,
                        json.dumps(body, ensure_ascii=False),
                        json.dumps(headers, ensure_ascii=False),
                        json.dumps(query_string, ensure_ascii=False),
                        str(e))
                    send_mailbox(alarm_message)
                    logger.info("邮件发送成功")
                raise e

            try:
                actual_time = response.elapsed.total_seconds()
                logger.info("实际的响应时间为：{}".format(actual_time))
            except Exception as e:
                logger.error("获取实际的响应时间发生错误：{}".format(e))
                raise e
            try:
                actual_code = response.status_code
                logger.info("实际的响应代码为：{}".format(actual_code))
            except Exception as e:
                logger.error("获取实际的响应代码发生错误：{}".format(e))
                raise e
            try:
                actual_result_text = response.text
                logger.info("实际的响应结果为：{}".format(actual_result_text[0:300]))
            except Exception as e:
                logger.error("获取实际的响应结果发生错误：{}".format(e))
                raise e

            if regular:
                regular = demjson.decode(regular)
                extract_list = []
                for i in regular["expression"]:
                    regular_result = re.findall(i, actual_result_text)[0]
                    extract_list.append(regular_result)
                variable_result_dict_temporary = dict(zip(regular["variable"], extract_list))
                for key, value in variable_result_dict_temporary.items():
                    variable_result_dict[key] = value

            if variable_result_dict:
                for key in list(variable_result_dict.keys()):
                    if not variable_result_dict[key]:
                        del variable_result_dict[key]

            expected_result = re.sub("{|}|\'|\"|\\[|\\]| ", "", expected_result)
            if actual_result_text:
                actual_result_text_re = re.sub("{|}|\'|\"|\\[|\\]| ", "", actual_result_text)
            expected_result_list = re.split(":|,", expected_result)
            actual_result_list_sp = re.split(":|,", actual_result_text_re)

            if expected_code == actual_code:
                fail_reason = ""
                if set(expected_result_list) <= set(actual_result_list_sp):
                    pass_status = "是"
                    if expected_time:
                        if actual_time <= expected_time:
                            pass_status = "是"
                        else:
                            pass_status = "否"
                            fail_reason = "实际的响应时间大于预期的响应时间"
                            logger.error("实际的响应时间大于预期的响应时间")
                            if dingtalk_switch == "开":
                                alarm_message = response_time_alarm(
                                    case_name, step_name, url, request_mode,
                                    json.dumps(body, ensure_ascii=False),
                                    json.dumps(headers, ensure_ascii=False),
                                    json.dumps(query_string, ensure_ascii=False),
                                    actual_time, expected_time)
                                send_dingtalk_alarm(alarm_message)
                                logger.info("钉钉报警发送成功")
                            if e_mail_switch == "开":
                                alarm_message = response_time_alarm(
                                    case_name, step_name, url, request_mode,
                                    json.dumps(body, ensure_ascii=False),
                                    json.dumps(headers, ensure_ascii=False),
                                    json.dumps(query_string, ensure_ascii=False),
                                    actual_time, expected_time)
                                send_mailbox(alarm_message)
                                logger.info("邮件发送成功")
                else:
                    pass_status = "否"
                    fail_reason = "预期的响应结果与实际的响应结果断言失败"
                    logger.error("预期的响应结果与实际的响应结果断言失败")
                    if dingtalk_switch == "开":
                        alarm_message = response_result_alarm(
                            case_name, step_name, url, request_mode,
                            json.dumps(body, ensure_ascii=False),
                            json.dumps(headers, ensure_ascii=False),
                            json.dumps(query_string, ensure_ascii=False),
                        )
                        send_dingtalk_alarm(alarm_message)
                        logger.info("钉钉报警发送成功")
                    if e_mail_switch == "开":
                        alarm_message = response_result_alarm(
                            case_name, step_name, url, request_mode,
                            json.dumps(body, ensure_ascii=False),
                            json.dumps(headers, ensure_ascii=False),
                            json.dumps(query_string, ensure_ascii=False),
                        )
                        send_dingtalk_alarm(alarm_message)
                        logger.info("邮件发送成功")
            else:
                pass_status = "否"
                fail_reason = "预期的响应代码与实际的响应代码不相等"
                logger.error("预期的响应代码与实际的响应代码不相等")
                if dingtalk_switch == "开":
                    alarm_message = response_code_alarm(
                        case_name, step_name, url, request_mode,
                        json.dumps(body, ensure_ascii=False),
                        json.dumps(headers, ensure_ascii=False),
                        json.dumps(query_string, ensure_ascii=False),
                        expected_code, actual_code)
                    send_dingtalk_alarm(alarm_message)
                    logger.info("钉钉报警发送成功")
                if e_mail_switch == "开":
                    alarm_message = response_code_alarm(
                        case_name, step_name, url, request_mode,
                        json.dumps(body, ensure_ascii=False),
                        json.dumps(headers, ensure_ascii=False),
                        json.dumps(query_string, ensure_ascii=False),
                        expected_code, actual_code)
                    send_dingtalk_alarm(alarm_message)
                    logger.info("邮件发送成功")

            RunningResults.objects.create(
                running_results_step_id=step_id,
                pass_status=pass_status,
                fail_reason=fail_reason,
                run_time=datetime.now(),
                actual_time=actual_time,
                actual_code=actual_code,
                actual_result=actual_result_text,
            )

    logger.info("**********本轮调度程序已经完成，请等待下一轮**********\n")
