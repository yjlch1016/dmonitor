from dmonitor.settings import MONITOR_PLATFORM


def response_result_alarm(case_name,
                          step_name,
                          url,
                          request_mode,
                          body,
                          headers,
                          query_string):
    # 响应结果报警文本

    text = "钉钉报警：\n用例名称：{}\n步骤名称：{}\n请求地址：{}\n请求方式：{}\n请求体：{}\n请求头：{}\n请求参数：{}\n预期的响应结果与实际的响应结果断言失败！！！\n请访问：{}\n" \
        .format(case_name,
                step_name,
                url,
                request_mode,
                body,
                headers,
                query_string,
                MONITOR_PLATFORM)
    return text


def response_time_alarm(case_name,
                        step_name,
                        url,
                        request_mode,
                        body,
                        headers,
                        query_string,
                        actual_time,
                        expected_time):
    # 响应时间报警文本

    text = "钉钉报警：\n用例名称：{}\n步骤名称：{}\n请求地址：{}\n请求方式：{}\n请求体：{}\n请求头：{}\n请求参数：{}\n实际的响应时间大于预期的响应时间：{}秒>{}秒\n请访问：{}\n" \
        .format(case_name,
                step_name,
                url,
                request_mode,
                body,
                headers,
                query_string,
                actual_time,
                expected_time,
                MONITOR_PLATFORM)
    return text


def response_code_alarm(case_name,
                        step_name,
                        url,
                        request_mode,
                        body,
                        headers,
                        query_string,
                        expected_code,
                        actual_code):
    # 响应代码报警文本

    text = "钉钉报警：\n用例名称：{}\n步骤名称：{}\n请求地址：{}\n请求方式：{}\n请求体：{}\n请求头：{}\n请求参数：{}\n预期的响应代码与实际的响应代码不相等：{}!={}\n请访问：{}\n" \
        .format(case_name,
                step_name,
                url,
                request_mode,
                body,
                headers,
                query_string,
                expected_code,
                actual_code,
                MONITOR_PLATFORM)
    return text


def http_request_exception_alarm(case_name,
                                 step_name,
                                 url,
                                 request_mode,
                                 body,
                                 headers,
                                 query_string,
                                 e):
    # http请求异常报警文本

    text = "钉钉报警：\n用例名称：{}\n步骤名称：{}\n请求地址：{}\n请求方式：{}\n请求体：{}\n请求头：{}\n请求参数：{}\n异常信息：{}\n请访问：{}\n" \
        .format(case_name,
                step_name,
                url,
                request_mode,
                body,
                headers,
                query_string,
                e,
                MONITOR_PLATFORM)
    return text
