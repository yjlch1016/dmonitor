from django.db import models


# Create your models here.


class Microservice(models.Model):
    # 微服务表

    on_off_choice = (
        ("开", "开"),
        ("关", "关"),
    )
    # 微服务开关枚举

    dingding_on_off_choice = (
        ("开", "开"),
        ("关", "关"),
    )
    # 钉钉开关枚举

    e_mail_on_off_choice = (
        ("开", "开"),
        ("关", "关"),
    )
    # 邮件开关枚举

    microservice_name = models.CharField(
        max_length=50, verbose_name="微服务名称",
        help_text="请输入微服务名称", db_index=True)
    # 微服务名称，并创建索引，必填
    microservice_on_off = models.CharField(
        choices=on_off_choice, max_length=11,
        blank=True, null=True, help_text="请选择开关",
        verbose_name="微服务开关", default="开")
    # 微服务开关
    dingding_on_off = models.CharField(
        choices=dingding_on_off_choice, max_length=11,
        blank=True, null=True, help_text="请选择开关",
        verbose_name="钉钉开关", default="关")
    # 钉钉开关
    e_mail_on_off = models.CharField(
        choices=e_mail_on_off_choice, max_length=11,
        blank=True, null=True, help_text="请选择开关",
        verbose_name="邮件开关", default="关")
    # 邮件开关
    microservice_introduce = models.CharField(
        max_length=255, verbose_name="微服务简介", help_text="请输入微服务简介",
        blank=True, null=True)
    # 微服务简介，选填
    create_time = models.DateTimeField(
        auto_now_add=True, blank=True, null=True, verbose_name="创建时间")
    # 创建时间
    update_time = models.DateTimeField(
        auto_now=True, blank=True, null=True, verbose_name="修改时间")

    # 修改时间

    class Meta:
        db_table = "microservice"
        verbose_name = "微服务列表"
        verbose_name_plural = "微服务列表"

    def __str__(self):
        return self.microservice_name


class Case(models.Model):
    # 用例表

    case_on_off_choice = (
        ("开", "开"),
        ("关", "关"),
    )
    # 用例开关枚举

    dingtalk_on_off_choice = (
        ("开", "开"),
        ("关", "关"),
    )
    # 钉钉开关枚举

    mailbox_on_off_choice = (
        ("开", "开"),
        ("关", "关"),
    )
    # 邮件开关枚举

    case_microservice = models.ForeignKey(
        Microservice, on_delete=models.CASCADE,
        verbose_name="微服务", related_name="microservices",
        help_text="请选择微服务")
    # 外键，关联微服务id
    case_name = models.CharField(
        max_length=50, verbose_name="用例名称",
        help_text="请输入用例名称", db_index=True)
    # 用例名称，并创建索引，必填
    case_on_off = models.CharField(
        choices=case_on_off_choice, max_length=11,
        blank=True, null=True, help_text="请选择开关",
        verbose_name="用例开关", default="开")
    # 用例开关
    dingtalk_on_off = models.CharField(
        choices=dingtalk_on_off_choice, max_length=11,
        blank=True, null=True, help_text="请选择开关",
        verbose_name="钉钉开关", default="关")
    # 钉钉开关
    mailbox_on_off = models.CharField(
        choices=mailbox_on_off_choice, max_length=11,
        blank=True, null=True, help_text="请选择开关",
        verbose_name="邮件开关", default="关")
    # 邮件开关
    create_time = models.DateTimeField(
        auto_now_add=True, blank=True, null=True, verbose_name="创建时间")
    # 创建时间
    update_time = models.DateTimeField(
        auto_now=True, blank=True, null=True, verbose_name="修改时间")

    # 修改时间

    class Meta:
        db_table = "case"
        verbose_name = "用例列表"
        verbose_name_plural = "用例列表"

    def __str__(self):
        return self.case_name


class Step(models.Model):
    # 步骤表

    mode_choice = (
        ("GET", "GET"),
        ("POST", "POST"),
        ("PUT", "PUT"),
        ("DELETE", "DELETE"),
        ("PATCH", "PATCH"),
    )
    # 请求方式枚举
    # 第一个元素是存储在数据库里面的值
    # 第二个元素是页面显示的值

    step_case = models.ForeignKey(
        Case, on_delete=models.CASCADE,
        verbose_name="用例名称", related_name="step_key",
        help_text="请选择用例")
    # 外键，关联用例id
    step_name = models.CharField(
        max_length=50, verbose_name="步骤名称",
        help_text="请输入步骤名称", db_index=True)
    # 步骤名称，并创建索引，必填
    request_mode = models.CharField(
        choices=mode_choice, max_length=11,
        verbose_name="请求方式", default="GET",
        help_text="请选择请求方式")
    # 请求方式，必填
    api = models.CharField(
        max_length=255, verbose_name="接口路径", help_text="请输入接口路径")
    # 接口路径，必填
    body = models.TextField(
        verbose_name="请求体", blank=True, null=True,
        help_text="请输入json格式的请求体", default="")
    # 请求体，选填
    headers = models.TextField(
        verbose_name="请求头", blank=True, null=True,
        help_text="请输入json格式的请求头", default='{"Content-Type":"application/json;charset=UTF-8"}')
    # 请求头，选填
    query_string = models.TextField(
        verbose_name="请求参数", blank=True, null=True,
        help_text="请输入json格式的请求参数", default="")
    # 请求参数，选填
    expected_time = models.FloatField(
        max_length=8, verbose_name="预期的响应时间",
        blank=True, null=True,
        default=3.0, help_text="请输入预期的响应时间，单位：秒")
    # 预期的响应时间，选填
    expected_code = models.IntegerField(
        verbose_name="预期的响应代码", help_text="请输入预期的响应代码",
        default=200)
    # 预期的响应代码，必填
    expected_result = models.TextField(
        verbose_name="预期的响应结果", help_text="请输入json格式的预期的响应结果",
        default="")
    # 预期的响应结果，必填
    regular = models.TextField(
        verbose_name="正则", blank=True, null=True,
        help_text="请输入正则（变量名与表达式）", default="")
    # 正则，选填
    create_time = models.DateTimeField(
        auto_now_add=True, blank=True, null=True, verbose_name="创建时间")
    # 创建时间
    update_time = models.DateTimeField(
        auto_now=True, blank=True, null=True, verbose_name="修改时间")

    # 修改时间

    class Meta:
        db_table = "step"
        verbose_name = "步骤列表"
        verbose_name_plural = "步骤列表"

    def __str__(self):
        return self.step_name


class RunningResults(models.Model):
    # 运行结果表

    pass_status_choice = (
        ("是", "是"),
        ("否", "否"),
    )

    running_results_step = models.ForeignKey(
        Step, on_delete=models.CASCADE,
        verbose_name="步骤名称", related_name="running_key",
        help_text="请选择步骤")
    # 外键，关联步骤id
    pass_status = models.CharField(
        choices=pass_status_choice, max_length=11,
        blank=True, null=True, default="",
        verbose_name="是否通过", db_index=True)
    # 是否通过，并创建索引
    fail_reason = models.TextField(
        verbose_name="失败原因", default="",
        blank=True, null=True)
    # 失败原因
    run_time = models.DateTimeField(
        auto_now_add=True, verbose_name="运行时间",
        blank=True, null=True, db_index=True)
    # 运行时间
    actual_time = models.FloatField(
        max_length=8, verbose_name="实际的响应时间（秒）",
        blank=True, null=True, db_index=True)
    # 实际的响应时间
    actual_code = models.IntegerField(
        verbose_name="实际的响应代码",
        blank=True, null=True)
    # 实际的响应代码
    actual_result = models.TextField(
        verbose_name="实际的响应结果",
        blank=True, null=True, default="")

    # 实际的响应结果

    class Meta:
        db_table = "running_results"
        verbose_name = "运行结果列表"
        verbose_name_plural = "运行结果列表"

    def __str__(self):
        return self.pass_status

    def actual_result_ellipsis(self):
        if len(str(self.actual_result)) > 50:
            return "{}......".format(str(self.actual_result[0:50]))
        else:
            return self.actual_result

    actual_result_ellipsis.short_description = "实际的响应结果"
    actual_result_ellipsis.allow_tags = True


class EnvironmentConfiguration(models.Model):
    # 环境配置表

    environment_configuration_microservice = models.OneToOneField(
        Microservice, on_delete=models.CASCADE,
        verbose_name="微服务", related_name="microservice_environment",
        help_text="请选择微服务")
    # 外键，关联微服务id
    domain_name = models.CharField(
        max_length=255, verbose_name="域名",
        help_text="请输入域名", db_index=True)
    # 域名，并创建索引，必填
    create_time = models.DateTimeField(
        auto_now_add=True, blank=True, null=True, verbose_name="创建时间")
    # 创建时间
    update_time = models.DateTimeField(
        auto_now=True, blank=True, null=True, verbose_name="修改时间")

    # 修改时间

    class Meta:
        db_table = "environment_configuration"
        verbose_name = "环境配置列表"
        verbose_name_plural = "环境配置列表"

    def __str__(self):
        return self.domain_name
