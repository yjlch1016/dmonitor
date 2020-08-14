# Register your models here.
import json
import logging
import re
from datetime import datetime
from itertools import chain

import demjson
import requests
import xadmin
from django.contrib.auth.models import Group, User
from django.forms import model_to_dict
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django_celery_beat.models import IntervalSchedule, CrontabSchedule, PeriodicTask
from django_celery_results.models import TaskResult
from import_export import resources
from xadmin import views
from xadmin.layout import Main, Fieldset
from xadmin.models import Permission, Log
from xadmin.plugins.actions import BaseActionView
from xadmin.plugins.batch import BatchChangeAction

from guard.models import Microservice, Case, RunningResults, EnvironmentConfiguration, Step
from guard.tool.common_encapsulation.function_assistant import function_dollar, function_rn, function_rl, \
    function_mp, function_rd
from guard.tool.dingtalk_robot.alarm_text import http_request_exception_alarm, response_result_alarm, \
    response_time_alarm, response_code_alarm
from guard.tool.dingtalk_robot.send_alarm_message import send_dingtalk_alarm
from guard.tool.dingtalk_robot.send_e_mail import send_mailbox

logger = logging.getLogger(__name__)


class CopyAction(BaseActionView):
    # 添加复制动作

    action_name = "copy_data"
    description = "复制所选的 %(verbose_name_plural)s"
    model_perm = 'change'
    icon = 'fa fa-facebook'

    def do_action(self, queryset):
        for qs in queryset:
            qs.id = None
            # 先让这条数据的id为空
            qs.save()
        return None


class MicroserviceImport(resources.ModelResource):
    class Meta:
        model = Microservice

        skip_unchanged = True
        # 导入数据时，如果该条数据未修改过，则会忽略
        report_skipped = True
        # 在导入预览页面中显示跳过的记录
        import_id_fields = ('id',)
        # 对象标识的默认字段是id，您可以选择在导入时设置哪些字段用作id
        exclude = (
            'create_time',
            'update_time',
        )
        # 黑名单


class CaseImport(resources.ModelResource):
    class Meta:
        model = Case

        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('id',)
        exclude = (
            'create_time',
            'update_time',
        )


class StepImport(resources.ModelResource):
    class Meta:
        model = Step

        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('id',)
        exclude = (
            'create_time',
            'update_time',
        )


class EnvironmentConfigurationImport(resources.ModelResource):
    class Meta:
        model = EnvironmentConfiguration

        skip_unchanged = True
        report_skipped = True
        import_id_fields = ('id',)
        exclude = (
            'create_time',
            'update_time',
        )


class StepAdmin(object):
    model = Step
    extra = 1
    # 提供1个足够的选项行，也可以提供N个
    style = "accordion"

    # 折叠

    def save_models(self):
        # 重写保存方法
        obj = self.new_obj
        obj.api = re.sub("\s", "", obj.api)
        obj.body = re.sub("\s", "", obj.body)
        obj.headers = re.sub("\s", "", obj.headers)
        obj.query_string = re.sub("\s", "", obj.query_string)
        obj.expected_result = re.sub("\s", "", obj.expected_result)
        obj.regular = re.sub("\s", "", obj.regular)
        # 一次性去除空格、换行符、制表符
        self.new_obj.save()

    def step_case_foreign(self, obj):
        # 给外键添加颜色
        button_html = '<a style="color: red" href="/admin/guard/case/%s/detail/?_format=html">%s</a>' % (
            obj.step_case.id, obj.step_case)
        # %s(,)匹配多个
        return format_html(button_html)

    step_case_foreign.short_description = '<span style="color: red">用例名称</span>'
    step_case_foreign.allow_tags = True

    def running_total(self, obj):
        # 利用外键反向统计步骤总数
        button_html = '<span style="color: brown">%s</span>' % obj.running_key.all().count()
        return format_html(button_html)

    running_total.short_description = '<span style="color: brown">运行总数</span>'
    running_total.allow_tags = True

    def update_button(self, obj):
        # 修改按钮
        button_html = '<a class="icon fa fa-edit" style="color: green" href="/admin/guard/step/%s/update/">修改</a>' % obj.id
        return format_html(button_html)

    update_button.short_description = '<span style="color: green">修改</span>'
    update_button.allow_tags = True

    def delete_button(self, obj):
        # 删除按钮
        button_html = '<a class="icon fa fa-times" style="color: blue" href="/admin/guard/step/%s/delete/">删除</a>' % obj.id
        return format_html(button_html)

    delete_button.short_description = '<span style="color: blue">删除</span>'
    delete_button.allow_tags = True

    form_layout = (
        Main(
            Fieldset('步骤信息部分',
                     'step_case', 'step_name', 'step_on_off',
                     'request_mode', 'api', 'body', 'headers', 'query_string',
                     'expected_time', 'expected_code', 'expected_result',
                     'regular'),
        ),
        # Side(
        #     Fieldset('时间部分',
        #              'create_time', 'update_time'),
        # )
    )
    # 详情页面字段分区，请注意不是fieldsets

    list_display = [
        'id',
        'step_case_foreign',
        'step_name',
        'step_on_off',
        'running_total',
        'request_mode',
        'api',
        'body',
        'headers',
        'query_string',
        'expected_time',
        'expected_code',
        'expected_result',
        'regular',
        'create_time',
        'update_time',
        'update_button',
        'delete_button',
    ]

    ordering = ("id",)
    search_fields = ("step_name", "step_case__case_name")
    list_filter = ["create_time"]
    list_display_links = ('id', 'step_case_foreign', 'step_name')
    show_detail_fields = ['step_name']
    list_editable = ['step_name']
    list_per_page = 20

    batch_fields = (
        'step_name',
        'step_on_off',
        'request_mode',
        'api',
        'body',
        'headers',
        'query_string',
        'expected_time',
        'expected_code',
        'expected_result',
        'regular',
    )
    # 可批量修改的字段
    actions = [CopyAction, BatchChangeAction]
    # 列表页面，添加复制动作与批量修改动作

    import_export_args = {
        'import_resource_class': StepImport,
    }
    # 配置导入按钮


class CaseAdmin(object):
    model = Case
    extra = 1
    # 提供1个足够的选项行，也可以提供N个
    style = "accordion"
    # 折叠

    inlines = [StepAdmin]

    # 使用内嵌显示

    def microservice_name(self, obj):
        # 给外键添加颜色
        button_html = '<a style="color: red" href="/admin/guard/microservice/%s/detail/?_format=html">%s</a>' % (
            obj.case_microservice.id, obj.case_microservice)
        # %s(,)匹配多个
        return format_html(button_html)

    microservice_name.short_description = '<span style="color: red">微服务名称</span>'
    microservice_name.allow_tags = True

    def step_total(self, obj):
        # 利用外键反向统计步骤总数
        button_html = '<span style="color: brown">%s</span>' % obj.step_key.all().count()
        return format_html(button_html)

    step_total.short_description = '<span style="color: brown">步骤总数</span>'
    step_total.allow_tags = True

    def debug_button(self, obj):
        # 调试按钮

        button = '<a class="icon fa fa-bug" style="color: purple" href="debug_case/%s">调试</a>' % obj.id
        return mark_safe(button)

    debug_button.short_description = '<span style="color: purple">调试</span>'
    debug_button.allow_tags = True

    def debug_case(self):
        # 调试用例

        logger.info("**********手动调试用例开始**********\n")

        global pass_status, fail_reason, actual_result_text_re
        variable_result_dict = {}
        # 定义一个变量名与提取的结果字典

        data_object = Case.objects.get(id=self, case_on_off="开"). \
            step_key.values().filter(step_on_off="开").order_by("id")
        # 反向查询用例包含的步骤信息
        data_list = list(data_object)
        # 把QuerySet对象转换成列表

        case_name = Case.objects.get(id=self, case_on_off="开").case_name
        logger.info("用例名称为：{}".format(case_name))

        service_domain = Case.objects.get(id=self, case_on_off="开"). \
            case_microservice.microservice_environment.domain_name
        switch_dict = model_to_dict(
            Case.objects.get(id=self, case_on_off="开"), fields=["dingtalk_on_off", "mailbox_on_off"])
        dingtalk_switch = switch_dict["dingtalk_on_off"]
        logger.info("钉钉开关为：{}".format(dingtalk_switch))
        e_mail_switch = switch_dict["mailbox_on_off"]
        logger.info("邮件开关为：{}".format(e_mail_switch))

        dingtalk_webhook = Case.objects.get(id=self, case_on_off="开"). \
            case_microservice.microservice_environment.webhook
        secret = Case.objects.get(id=self, case_on_off="开"). \
            case_microservice.microservice_environment.secret
        recipient_email = Case.objects.get(id=self, case_on_off="开"). \
            case_microservice.microservice_environment.recipient_email

        for item in data_list:
            step_id = item["id"]
            step_name = item["step_name"]
            step_on_off = item["step_on_off"]
            request_mode = item["request_mode"]
            api = item["api"]
            body = item["body"]
            headers = item["headers"]
            query_string = item["query_string"]
            expected_time = item["expected_time"]
            expected_code = item["expected_code"]
            expected_result = item["expected_result"]
            regular = item["regular"]

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
                body = function_rd(body)
                body = json.loads(body)
            if headers:
                headers = function_rn(headers)
                headers = function_rl(headers)
                headers = function_mp(headers)
                headers = function_rd(headers)
                headers = json.loads(headers)
            if query_string:
                query_string = function_rn(query_string)
                query_string = function_rl(query_string)
                query_string = function_mp(query_string)
                query_string = function_rd(query_string)
                query_string = json.loads(query_string)

            logger.info("步骤名称为：{}".format(step_name))
            logger.info("请求方式为：{}".format(request_mode))
            logger.info("步骤开关为：{}".format(step_on_off))
            url = service_domain + api
            logger.info("请求地址为：{}".format(url))
            logger.info("请求头为：{}".format(json.dumps(headers, ensure_ascii=False)))
            logger.info("请求参数为：{}".format(json.dumps(query_string, ensure_ascii=False)))
            logger.info("请求体为：{}".format(json.dumps(body, ensure_ascii=False)))

            try:
                response = requests.request(
                    request_mode, url, data=json.dumps(body),
                    headers=headers, params=query_string, timeout=(25, 30)
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
                    send_dingtalk_alarm(alarm_message, dingtalk_webhook, secret)
                    logger.info("钉钉报警发送成功")
                if e_mail_switch == "开":
                    alarm_message = http_request_exception_alarm(
                        case_name, step_name, url, request_mode,
                        json.dumps(body, ensure_ascii=False),
                        json.dumps(headers, ensure_ascii=False),
                        json.dumps(query_string, ensure_ascii=False),
                        str(e))
                    send_mailbox(alarm_message, recipient_email)
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
                actual_headers = response.headers
                logger.info("实际的响应头为：{}".format(actual_headers))
            except Exception as e:
                logger.error("获取实际的响应头发生错误：{}".format(e))
                raise e
            try:
                actual_result_text = response.text
                logger.info("实际的响应结果为：{}".format(actual_result_text[0:400]))
            except Exception as e:
                logger.error("获取实际的响应结果发生错误：{}".format(e))
                raise e

            try:
                if regular:
                    regular = demjson.decode(regular)
                    extract_list = []
                    for i in regular["expression"]:
                        re_list = re.findall(i, actual_result_text)
                        if len(re_list) >= 1:
                            regular_result = re_list[0]
                            extract_list.append(regular_result)
                    variable_result_dict_temporary = dict(zip(regular["variable"], extract_list))
                    for key, value in variable_result_dict_temporary.items():
                        variable_result_dict[key] = value
            except Exception as e:
                logger.error("正则匹配发生错误：{}".format(e))
                raise e

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
                                send_dingtalk_alarm(alarm_message, dingtalk_webhook, secret)
                                logger.info("钉钉报警发送成功")
                            if e_mail_switch == "开":
                                alarm_message = response_time_alarm(
                                    case_name, step_name, url, request_mode,
                                    json.dumps(body, ensure_ascii=False),
                                    json.dumps(headers, ensure_ascii=False),
                                    json.dumps(query_string, ensure_ascii=False),
                                    actual_time, expected_time)
                                send_mailbox(alarm_message, recipient_email)
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
                        send_dingtalk_alarm(alarm_message, dingtalk_webhook, secret)
                        logger.info("钉钉报警发送成功")
                    if e_mail_switch == "开":
                        alarm_message = response_result_alarm(
                            case_name, step_name, url, request_mode,
                            json.dumps(body, ensure_ascii=False),
                            json.dumps(headers, ensure_ascii=False),
                            json.dumps(query_string, ensure_ascii=False),
                        )
                        send_mailbox(alarm_message, recipient_email)
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
                    send_dingtalk_alarm(alarm_message, dingtalk_webhook, secret)
                    logger.info("钉钉报警发送成功")
                if e_mail_switch == "开":
                    alarm_message = response_code_alarm(
                        case_name, step_name, url, request_mode,
                        json.dumps(body, ensure_ascii=False),
                        json.dumps(headers, ensure_ascii=False),
                        json.dumps(query_string, ensure_ascii=False),
                        expected_code, actual_code)
                    send_mailbox(alarm_message, recipient_email)
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

        logger.info("**********手动调试用例结束**********\n")

    def chart_button(self, obj):
        # 图表按钮

        button = '<a class="icon fa fa-film" style="color: violet" href="case_chart/%s">图表</a>' % obj.id
        return mark_safe(button)

    chart_button.short_description = '<span style="color: violet">图表</span>'
    chart_button.allow_tags = True

    def update_button(self, obj):
        # 修改按钮
        button_html = '<a class="icon fa fa-edit" style="color: green" href="/admin/guard/case/%s/update/">修改</a>' % obj.id
        return format_html(button_html)

    update_button.short_description = '<span style="color: green">修改</span>'
    update_button.allow_tags = True

    def delete_button(self, obj):
        # 删除按钮
        button_html = '<a class="icon fa fa-times" style="color: blue" href="/admin/guard/case/%s/delete/">删除</a>' % obj.id
        return format_html(button_html)

    delete_button.short_description = '<span style="color: blue">删除</span>'
    delete_button.allow_tags = True

    form_layout = (
        Main(
            Fieldset('用例信息部分',
                     'case_microservice', 'case_name',
                     'case_on_off', 'dingtalk_on_off', 'mailbox_on_off'),
        ),
        # Side(
        #     Fieldset('时间部分',
        #              'create_time', 'update_time'),
        # )
    )
    # 详情页面字段分区，请注意不是fieldsets

    list_display = [
        'id',
        'microservice_name',
        'case_name',
        'case_on_off',
        'dingtalk_on_off',
        'mailbox_on_off',
        'step_total',
        'chart_button',
        'create_time',
        'update_time',
        'debug_button',
        'update_button',
        'delete_button',
    ]

    ordering = ("id",)
    search_fields = ("case_name", "case_microservice__microservice_name")
    list_filter = ["create_time"]
    list_display_links = ('id', 'microservice_name', 'case_name')
    show_detail_fields = ['case_name']
    list_editable = ['case_name']
    list_per_page = 20

    batch_fields = (
        'case_name',
        'case_on_off',
        'dingtalk_on_off',
        'mailbox_on_off',
    )
    # 可批量修改的字段
    actions = [CopyAction, BatchChangeAction]
    # 列表页面，添加复制动作与批量修改动作

    import_export_args = {
        'import_resource_class': CaseImport,
    }
    # 配置导入按钮


class MicroserviceAdmin(object):
    inlines = [CaseAdmin]

    # 使用内嵌显示

    def swagger(self, obj):
        # swagger地址
        button_html = '<a style="color: green" href="%s" target="_blank">%s</a>' % (
            obj.swagger_address, obj.swagger_address)
        return format_html(button_html)

    swagger.short_description = '<span style="color: green">swagger地址</span>'
    swagger.allow_tags = True

    def case_total(self, obj):
        # 利用外键反向统计用例总数
        button_html = '<span style="color: brown">%s</span>' % obj.microservices.all().count()
        return format_html(button_html)

    case_total.short_description = '<span style="color: brown">用例总数</span>'
    case_total.allow_tags = True

    def debug_button(self, obj):
        # 调试按钮

        button = '<a class="icon fa fa-bug" style="color: purple" href="debug_microservice/%s">调试</a>' % obj.id
        return mark_safe(button)

    debug_button.short_description = '<span style="color: purple">调试</span>'
    debug_button.allow_tags = True

    def debug_microservice(self):
        # 调试微服务

        logger.info("**********手动调试微服务开始**********\n")

        global pass_status, fail_reason, actual_result_text_re
        variable_result_dict = {}
        # 定义一个变量名与提取的结果字典

        data_object = Microservice.objects.filter(microservice_on_off="开").get(
            id=self).microservices.values_list("id").filter(case_on_off="开").order_by("id")
        # 反向查询微服务包含的用例信息
        data_tuple = tuple(data_object)
        # 把QuerySet对象转换成元祖
        data_tuple = tuple(chain.from_iterable(data_tuple))
        # 把多维元祖转换成一维元祖

        service_domain = Microservice.objects.get(id=self, microservice_on_off="开") \
            .microservice_environment.domain_name
        dingtalk_webhook = Microservice.objects.get(id=self, case_on_off="开") \
            .microservice_environment.webhook
        secret = Microservice.objects.get(id=self, case_on_off="开") \
            .microservice_environment.secret
        recipient_email = Microservice.objects.get(id=self, case_on_off="开") \
            .microservice_environment.recipient_email

        for case_i in data_tuple:
            case_object = Case.objects.get(id=case_i, case_on_off="开").step_key.values().filter(
                step_on_off="开").order_by("id")
            # 反向查询用例包含的步骤信息
            case_name = Case.objects.get(id=case_i, case_on_off="开").case_name
            logger.info("用例名称为：{}".format(case_name))
            case_list = list(case_object)
            # 把QuerySet对象转换成列表

            switch_dict = model_to_dict(
                Case.objects.get(id=case_i, case_on_off="开"), fields=["dingtalk_on_off", "mailbox_on_off"])
            dingtalk_switch = switch_dict["dingtalk_on_off"]
            logger.info("钉钉开关为：{}".format(dingtalk_switch))
            e_mail_switch = switch_dict["mailbox_on_off"]
            logger.info("邮件开关为：{}".format(e_mail_switch))

            for step_i in case_list:
                step_id = step_i["id"]
                step_name = step_i["step_name"]
                step_on_off = step_i["step_on_off"]
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
                    body = function_rd(body)
                    body = json.loads(body)
                if headers:
                    headers = function_rn(headers)
                    headers = function_rl(headers)
                    headers = function_mp(headers)
                    headers = function_rd(headers)
                    headers = json.loads(headers)
                if query_string:
                    query_string = function_rn(query_string)
                    query_string = function_rl(query_string)
                    query_string = function_mp(query_string)
                    query_string = function_rd(query_string)
                    query_string = json.loads(query_string)

                logger.info("步骤名称为：{}".format(step_name))
                logger.info("请求方式为：{}".format(request_mode))
                logger.info("步骤开关为：{}".format(step_on_off))
                url = service_domain + api
                logger.info("请求地址为：{}".format(url))
                logger.info("请求头为：{}".format(json.dumps(headers, ensure_ascii=False)))
                logger.info("请求参数为：{}".format(json.dumps(query_string, ensure_ascii=False)))
                logger.info("请求体为：{}".format(json.dumps(body, ensure_ascii=False)))

                try:
                    response = requests.request(
                        request_mode, url, data=json.dumps(body),
                        headers=headers, params=query_string, timeout=(25, 30)
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
                        send_dingtalk_alarm(alarm_message, dingtalk_webhook, secret)
                        logger.info("钉钉报警发送成功")
                    if e_mail_switch == "开":
                        alarm_message = http_request_exception_alarm(
                            case_name, step_name, url, request_mode,
                            json.dumps(body, ensure_ascii=False),
                            json.dumps(headers, ensure_ascii=False),
                            json.dumps(query_string, ensure_ascii=False),
                            str(e))
                        send_mailbox(alarm_message, recipient_email)
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
                    actual_headers = response.headers
                    logger.info("实际的响应头为：{}".format(actual_headers))
                except Exception as e:
                    logger.error("获取实际的响应头发生错误：{}".format(e))
                    raise e
                try:
                    actual_result_text = response.text
                    logger.info("实际的响应结果为：{}".format(actual_result_text[0:400]))
                except Exception as e:
                    logger.error("获取实际的响应结果发生错误：{}".format(e))
                    raise e

                try:
                    if regular:
                        regular = demjson.decode(regular)
                        extract_list = []
                        for i in regular["expression"]:
                            re_list = re.findall(i, actual_result_text)
                            if len(re_list) >= 1:
                                regular_result = re_list[0]
                                extract_list.append(regular_result)
                        variable_result_dict_temporary = dict(zip(regular["variable"], extract_list))
                        for key, value in variable_result_dict_temporary.items():
                            variable_result_dict[key] = value
                except Exception as e:
                    logger.error("正则匹配发生错误：{}".format(e))
                    raise e

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
                                fail_reason = "实际的响应时间大于预期的响应时间\n"
                                logger.error("实际的响应时间大于预期的响应时间")
                                if dingtalk_switch == "开":
                                    alarm_message = response_time_alarm(
                                        case_name, step_name, url, request_mode,
                                        json.dumps(body, ensure_ascii=False),
                                        json.dumps(headers, ensure_ascii=False),
                                        json.dumps(query_string, ensure_ascii=False),
                                        actual_time, expected_time)
                                    send_dingtalk_alarm(alarm_message, dingtalk_webhook, secret)
                                    logger.info("钉钉报警发送成功")
                                if e_mail_switch == "开":
                                    alarm_message = response_time_alarm(
                                        case_name, step_name, url, request_mode,
                                        json.dumps(body, ensure_ascii=False),
                                        json.dumps(headers, ensure_ascii=False),
                                        json.dumps(query_string, ensure_ascii=False),
                                        actual_time, expected_time)
                                    send_mailbox(alarm_message, recipient_email)
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
                            send_dingtalk_alarm(alarm_message, dingtalk_webhook, secret)
                            logger.info("钉钉报警发送成功")
                        if e_mail_switch == "开":
                            alarm_message = response_result_alarm(
                                case_name, step_name, url, request_mode,
                                json.dumps(body, ensure_ascii=False),
                                json.dumps(headers, ensure_ascii=False),
                                json.dumps(query_string, ensure_ascii=False),
                            )
                            send_mailbox(alarm_message, recipient_email)
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
                        send_dingtalk_alarm(alarm_message, dingtalk_webhook, secret)
                        logger.info("钉钉报警发送成功")
                    if e_mail_switch == "开":
                        alarm_message = response_code_alarm(
                            case_name, step_name, url, request_mode,
                            json.dumps(body, ensure_ascii=False),
                            json.dumps(headers, ensure_ascii=False),
                            json.dumps(query_string, ensure_ascii=False),
                            expected_code, actual_code)
                        send_mailbox(alarm_message, recipient_email)
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

        logger.info("**********手动调试微服务结束**********\n")

    def update_button(self, obj):
        # 修改按钮
        button_html = '<a class="icon fa fa-edit" style="color: green" href="/admin/guard/microservice/%s/update/">修改</a>' % obj.id
        return format_html(button_html)

    update_button.short_description = '<span style="color: green">修改</span>'
    update_button.allow_tags = True

    def delete_button(self, obj):
        # 删除按钮
        button_html = '<a class="icon fa fa-times" style="color: blue" href="/admin/guard/microservice/%s/delete/">删除</a>' % obj.id
        return format_html(button_html)

    delete_button.short_description = '<span style="color: blue">删除</span>'
    delete_button.allow_tags = True

    form_layout = (
        Main(
            Fieldset('微服务信息部分',
                     'microservice_name', 'swagger_address', 'microservice_on_off', 'dingding_on_off', 'e_mail_on_off',
                     'microservice_introduce'),
        ),
        # Side(
        #     Fieldset('时间部分',
        #              'create_time', 'update_time'),
        # )
    )

    list_display = [
        'id',
        'microservice_name',
        'swagger',
        'microservice_on_off',
        'dingding_on_off',
        'e_mail_on_off',
        'case_total',
        'microservice_introduce',
        'create_time',
        'update_time',
        'debug_button',
        'update_button',
        'delete_button',
    ]
    ordering = ("id",)
    search_fields = ("microservice_name",)
    list_filter = ["create_time"]
    show_detail_fields = ['microservice_name']
    list_display_links = ('id', 'microservice_name')
    list_editable = ['microservice_name']
    list_per_page = 20

    batch_fields = (
        'microservice_name',
        'swagger_address',
        'microservice_on_off',
        'dingding_on_off',
        'e_mail_on_off',
        'microservice_introduce',
    )
    # 可批量修改的字段
    actions = [CopyAction, BatchChangeAction]
    # 列表页面，添加复制动作与批量修改动作

    import_export_args = {
        'import_resource_class': MicroserviceImport,
    }
    # 配置导入按钮


class RunningResultsAdmin(object):

    def has_add_permission(self):
        # 禁用增加按钮
        return False

    def case_foreign(self, obj):
        # 给外键添加颜色
        button_html = '<a style="color: orange" href="/admin/guard/case/%s/detail/?_format=html">%s</a>' % (
            obj.running_results_step.step_case.id, obj.running_results_step.step_case)
        # %s(,)匹配多个
        return format_html(button_html)

    case_foreign.short_description = '<span style="color: orange">用例名称</span>'
    case_foreign.allow_tags = True

    def running_step_foreign(self, obj):
        # 给外键添加颜色
        button_html = '<a style="color: red" href="/admin/guard/step/%s/detail/?_format=html">%s</a>' % (
            obj.running_results_step.id, obj.running_results_step)
        # %s(,)匹配多个
        return format_html(button_html)

    running_step_foreign.short_description = '<span style="color: red">步骤名称</span>'
    running_step_foreign.allow_tags = True

    def delete_button(self, obj):
        # 删除按钮
        button_html = '<a class="icon fa fa-times" style="color: blue" href="/admin/guard/runningresults/%s/delete/">删除</a>' % obj.id
        return format_html(button_html)

    delete_button.short_description = '<span style="color: blue">删除</span>'
    delete_button.allow_tags = True

    form_layout = (
        Main(
            Fieldset('运行结果部分',
                     'case_foreign', 'running_results_step', 'pass_status', 'fail_reason',
                     'run_time', 'actual_time', 'actual_code', 'actual_result',
                     ),
        ),
        # Side(
        #     Fieldset('时间部分',
        #              'create_time', 'update_time'),
        # )
    )

    list_display = [
        'id',
        'case_foreign',
        'running_step_foreign',
        'pass_status',
        'fail_reason',
        'run_time',
        'actual_time',
        'actual_code',
        'actual_result_ellipsis',
        'delete_button',
    ]
    ordering = ("-id",)
    search_fields = ['pass_status', 'running_results_step__step_name', 'running_results_step__step_case__case_name']
    list_filter = ["run_time"]
    list_display_links = None
    # 禁用编辑链接
    show_detail_fields = ['pass_status']
    readonly_fields = [
        'id', 'running_results_step', 'pass_status', 'fail_reason',
        'run_time', 'actual_time', 'actual_code', 'actual_result'
    ]
    # 设置只读字段
    list_per_page = 20


class EnvironmentConfigurationAdmin(object):

    def microservice_name_env(self, obj):
        # 给外键添加颜色
        button_html = '<a style="color: red" href="/admin/guard/microservice/%s/update/">%s</a>' % (
            obj.environment_configuration_microservice.id, obj.environment_configuration_microservice)
        # %s(,)匹配多个
        return format_html(button_html)

    microservice_name_env.short_description = '<span style="color: red">微服务名称</span>'
    microservice_name_env.allow_tags = True

    def update_button(self, obj):
        # 修改按钮
        button_html = '<a class="icon fa fa-edit" style="color: green" href="/admin/guard/environmentconfiguration/%s/update/">修改</a>' % obj.id
        return format_html(button_html)

    update_button.short_description = '<span style="color: green">修改</span>'
    update_button.allow_tags = True

    def delete_button(self, obj):
        # 删除按钮
        button_html = '<a class="icon fa fa-times" style="color: blue" href="/admin/guard/environmentconfiguration/%s/delete/">删除</a>' % obj.id
        return format_html(button_html)

    delete_button.short_description = '<span style="color: blue">删除</span>'
    delete_button.allow_tags = True

    form_layout = (
        Main(
            Fieldset('环境配置信息部分',
                     'environment_configuration_microservice', 'domain_name',
                     'webhook', 'secret', 'recipient_email'),
        ),
        # Side(
        #     Fieldset('时间部分',
        #              'create_time', 'update_time'),
        # )
    )

    list_display = [
        'id',
        'microservice_name_env',
        'domain_name',
        'webhook',
        'secret',
        'recipient_email',
        'create_time',
        'update_time',
        'update_button',
        'delete_button',
    ]
    ordering = ("id",)
    search_fields = ("domain_name", "environment_configuration_microservice__microservice_name")
    list_filter = ["create_time"]
    show_detail_fields = ['domain_name']
    list_display_links = ('id', 'microservice_name_env', 'domain_name')
    list_editable = ['domain_name']
    list_per_page = 20

    batch_fields = (
        'domain_name', 'webhook', 'secret', 'recipient_email',
    )
    # 可批量修改的字段
    actions = [CopyAction, BatchChangeAction]
    # 列表页面，添加复制动作与批量修改动作

    import_export_args = {
        'import_resource_class': EnvironmentConfigurationImport,
    }
    # 配置导入按钮


class IntervalScheduleAdmin(object):
    list_display = [
        'id', 'every', 'period',
    ]
    ordering = ['id']
    search_fields = ['every']
    list_per_page = 10


class CrontabScheduleAdmin(object):
    list_display = [
        'id', 'minute', 'hour',
        'day_of_week', 'day_of_month', 'month_of_year', 'timezone'
    ]
    ordering = ['id']
    search_fields = ['minute']
    list_per_page = 10


class PeriodicTaskAdmin(object):
    list_display = [
        'id', 'name', 'task', 'interval', 'crontab',
        'enabled', 'description', 'last_run_at', 'total_run_count',
        'date_changed', 'solar', 'clocked',
        'args', 'kwargs', 'queue', 'exchange', 'routing_key', 'headers',
        'priority', 'expires', 'one_off', 'start_time',
    ]
    ordering = ['id']
    search_fields = ['name']
    show_detail_fields = ['name']
    list_per_page = 10


class TaskResultAdmin(object):

    def has_add_permission(self):
        # 禁用增加按钮
        return False

    list_display = [
        'id', 'task_id', 'task_name',
        'status', 'date_done',
        'task_args', 'task_kwargs',
        'content_type', 'content_encoding', 'traceback',
        'result', 'hidden', 'meta',
    ]
    ordering = ['-id']
    search_fields = ['task_id']
    list_display_links = None
    # 禁用编辑链接
    show_detail_fields = ['task_id']
    readonly_fields = [
        'id', 'task_id', 'task_name',
        'status', 'date_done',
        'task_args', 'task_kwargs',
        'content_type', 'content_encoding', 'traceback',
        'result', 'hidden', 'meta'
    ]
    # 设置只读字段
    list_per_page = 10


class BaseSetting(object):
    enable_themes = True
    use_bootswatch = True
    # 开启主题自由切换


class GlobalSetting(object):
    global_search_models = [
        Microservice,
        Case,
        Step,
        RunningResults,
        EnvironmentConfiguration
    ]
    # 配置全局搜索选项
    # 默认搜索组、用户、日志记录

    site_title = "生产环境接口监控平台"
    # 标题
    site_footer = "测试部门"
    # 页脚
    menu_style = "accordion"

    # 左侧菜单收缩功能

    def get_site_menu(self):
        return (
            {
                'title': '监控管理',
                'icon': 'fa fa-bar-chart-o',
                'perm': self.get_model_perm(Microservice, 'change'),
                # 权限
                'menus': (
                    {
                        'title': 'supervisor',
                        'icon': 'fa fa-trophy',
                        'url': "http://www.monitor.com/supervisor/"
                    },
                    {
                        'title': 'silk',
                        'icon': 'fa fa-twitter',
                        'url': "http://www.monitor.com/silk/"
                    },
                )
            },
            {
                'title': '用例列表',
                'icon': 'fa fa-github-alt',
                'perm': self.get_model_perm(Microservice, 'change'),
                # 权限
                'menus': (
                    {
                        'title': '微服务列表',
                        'icon': 'fa fa-html5',
                        'url': self.get_model_url(Microservice, 'changelist')
                    },
                    {
                        'title': '用例列表',
                        'icon': 'fa fa-css3',
                        'url': self.get_model_url(Case, 'changelist')
                    },
                    {
                        'title': '步骤列表',
                        'icon': 'fa fa-anchor',
                        'url': self.get_model_url(Step, 'changelist')
                    },
                    {
                        'title': '运行结果列表',
                        'icon': 'fa fa-youtube',
                        'url': self.get_model_url(RunningResults, 'changelist')
                    },
                    {
                        'title': '环境配置列表',
                        'icon': 'fa fa-coffee',
                        'url': self.get_model_url(EnvironmentConfiguration, 'changelist')
                    },
                )
            },
            {
                'title': '任务队列',
                'icon': 'fa fa-cloud',
                'perm': self.get_model_perm(PeriodicTask, 'change'),
                'menus': (
                    {
                        'title': '间隔时间列表',
                        'icon': 'fa fa-backward',
                        'url': self.get_model_url(IntervalSchedule, 'changelist')
                    },
                    {
                        'title': '定时时间列表',
                        'icon': 'fa fa-forward',
                        'url': self.get_model_url(CrontabSchedule, 'changelist')
                    },
                    {
                        'title': '任务设置列表',
                        'icon': 'fa fa-play-circle',
                        'url': self.get_model_url(PeriodicTask, 'changelist')
                    },
                    {
                        'title': '任务结果列表',
                        'icon': 'fa fa-arrows-alt',
                        'url': self.get_model_url(TaskResult, 'changelist')
                    },
                )
            },
            {
                'title': '后台管理',
                'icon': 'fa fa-user',
                'perm': self.get_model_perm(Group, 'change'),
                'menus': (
                    {
                        'title': '组',
                        'icon': 'fa fa-sun-o',
                        'url': self.get_model_url(Group, 'changelist')
                    },
                    {
                        'title': '用户',
                        'icon': 'fa fa-moon-o',
                        'url': self.get_model_url(User, 'changelist')
                    },
                    {
                        'title': '权限',
                        'icon': 'fa fa-weibo',
                        'url': self.get_model_url(Permission, 'changelist')
                    },
                    {
                        'title': '日志记录',
                        'icon': 'fa fa-renren',
                        'url': self.get_model_url(Log, 'changelist')
                    },
                )
            },
        )
    # 自定义应用的顺序


xadmin.site.register(Microservice, MicroserviceAdmin)
xadmin.site.register(Case, CaseAdmin)
xadmin.site.register(Step, StepAdmin)
xadmin.site.register(RunningResults, RunningResultsAdmin)
xadmin.site.register(EnvironmentConfiguration, EnvironmentConfigurationAdmin)

xadmin.site.register(views.BaseAdminView, BaseSetting)
xadmin.site.register(views.CommAdminView, GlobalSetting)

xadmin.site.register(IntervalSchedule, IntervalScheduleAdmin)
# 间隔时间表
xadmin.site.register(CrontabSchedule, CrontabScheduleAdmin)
# 定时时间表
xadmin.site.register(PeriodicTask, PeriodicTaskAdmin)
# 配置任务
xadmin.site.register(TaskResult, TaskResultAdmin)
# 任务结果
