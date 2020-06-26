import json
import logging
from itertools import chain

from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from rest_framework.views import APIView

from pyecharts.charts import Bar, Line, EffectScatter
from pyecharts import options as opts

from guard.models import Case, Step, RunningResults

logger = logging.getLogger(__name__)


def response_as_json(data):
    json_str = json.dumps(data)
    response = HttpResponse(
        json_str,
        content_type="application/json",
    )
    response["Access-Control-Allow-Origin"] = "*"
    return response


def json_response(data, code=200):
    data = {
        "code": code,
        "msg": "success",
        "data": data,
    }
    return response_as_json(data)


def json_error(error_string="error", code=500, **kwargs):
    data = {
        "code": code,
        "msg": error_string,
        "data": {}
    }
    data.update(kwargs)
    return response_as_json(data)


JsonResponse = json_response
JsonError = json_error


def get_chart_data():
    # 获取x轴与y轴数据

    logger.info("**********开始手动获取x轴与y轴数据**********\n")

    global run_time_list

    case_name = Case.objects.get(id=next_url, case_on_off="开").case_name
    # 查询用例名称
    step_id_object = Step.objects.values_list("id").filter(step_case_id=next_url).order_by("id")
    # 查询步骤id
    step_id_list = list(step_id_object)
    step_id_list = list(chain.from_iterable(step_id_list))

    y_axis_data = []
    # y轴数据

    for i in step_id_list:
        step_name = Step.objects.get(id=i).step_name
        # 查询步骤名称
        actual_time_object = RunningResults.objects.values_list("actual_time").filter(
            running_results_step_id=i).order_by("-id")[:96]
        # 查询实际的响应时间
        actual_time_list = list(actual_time_object)
        actual_time_list = list(chain.from_iterable(actual_time_list))
        actual_time_list.reverse()

        case_name_step_name_actual_time_dict = {case_name + "→" + step_name: actual_time_list}
        # 把用例名称+步骤名称与实际的响应时间组装成一个字典
        y_axis_data.append(case_name_step_name_actual_time_dict)
        # 往y轴数据列表里面添加元素

        run_time_object = RunningResults.objects.values_list("run_time").filter(
            running_results_step_id=i).order_by("-id")[:96]
        # 查询运行时间，即为x轴
        run_time_list = list(run_time_object)
        run_time_list = list(chain.from_iterable(run_time_list))
        for index in range(len(run_time_list)):
            run_time_list[index] = run_time_list[index].strftime(
                "%Y-%m-%d %H:%M")
            # 把datetime.datetime转为str
        run_time_list.reverse()

    logger.info("x轴数据为：{}".format(run_time_list))
    logger.info("y轴数据为：{}".format(y_axis_data))
    chart_data = [run_time_list, y_axis_data]
    # 把x轴与y轴数据组装成一个列表

    logger.info("**********手动获取x轴与y轴数据结束**********\n")

    return chart_data


def line_chart():
    # 折线图

    line = Line()
    x_y_axis = get_chart_data()
    line.add_xaxis(x_y_axis[0])
    for j in x_y_axis[1]:
        for key, value in j.items():
            line.add_yaxis(key,
                           value,
                           areastyle_opts=opts.AreaStyleOpts(opacity=1),
                           label_opts=opts.LabelOpts(is_show=False))
    line.set_series_opts(
        # linestyle_opts=opts.LineStyleOpts(
        #     width=5,
        #     opacity=1,
        #     type_='solid',
        # )
        markpoint_opts=opts.MarkPointOpts(
            data=[
                opts.MarkPointItem(type_="max", name="最大值"),
                opts.MarkPointItem(type_="min", name="最小值"),
            ]
        ),
    )
    line.set_global_opts(
        title_opts=opts.TitleOpts(
            title="API耗时统计",
            subtitle="生产环境",
            pos_left="30%",
            title_textstyle_opts=opts.TextStyleOpts(color='red'),
            subtitle_textstyle_opts=opts.TextStyleOpts(color='blue')
        ),
        xaxis_opts=opts.AxisOpts(
            name="运行时间",
            type_="category",
            boundary_gap=False,
            # axislabel_opts=opts.LabelOpts(rotate=15)
        ),
        yaxis_opts=opts.AxisOpts(
            name="实际的响应时间（单位：秒）",
            # min_=0,
            # max_=20
        ),
        legend_opts=opts.LegendOpts(
            type_='scroll',
            selected_mode='multiple',
            pos_left='right',
            pos_top='10%',
            orient='vertical'
        ),
        tooltip_opts=opts.TooltipOpts(
            trigger="axis",
            axis_pointer_type="line"
        ),
        toolbox_opts=opts.ToolboxOpts(
            is_show=True,
            pos_left='right'
        ),
        visualmap_opts=opts.VisualMapOpts(
            is_show=True,
            type_="size",
            min_=0,
            max_=20,
            range_text=["最大值", "最小值"]),
        datazoom_opts=[
            opts.DataZoomOpts(range_start=50, range_end=100)],
    )
    line = line.dump_options_with_quotes()
    return line


def bar_chart():
    # 柱状图

    bar = Bar()
    x_y_axis = get_chart_data()
    bar.add_xaxis(x_y_axis[0])
    for j in x_y_axis[1]:
        for key, value in j.items():
            bar.add_yaxis(key,
                          value,
                          label_opts=opts.LabelOpts(is_show=False))
    bar.set_series_opts(
        markpoint_opts=opts.MarkPointOpts(
            data=[
                opts.MarkPointItem(type_="max", name="最大值"),
                opts.MarkPointItem(type_="min", name="最小值"),
            ]
        ),
    )
    bar.set_global_opts(
        title_opts=opts.TitleOpts(
            title="API耗时统计",
            subtitle="生产环境",
            pos_left="30%",
            title_textstyle_opts=opts.TextStyleOpts(color='red'),
            subtitle_textstyle_opts=opts.TextStyleOpts(color='blue')
        ),
        xaxis_opts=opts.AxisOpts(
            name="运行时间",
            type_="category",
            boundary_gap=True,
            # axislabel_opts=opts.LabelOpts(rotate=15)
        ),
        yaxis_opts=opts.AxisOpts(
            name="实际的响应时间（单位：秒）",
            # min_=0,
            # max_=20
        ),
        legend_opts=opts.LegendOpts(
            type_='scroll',
            selected_mode='multiple',
            pos_left='right',
            pos_top='10%',
            orient='vertical'
        ),
        tooltip_opts=opts.TooltipOpts(
            trigger="axis",
            axis_pointer_type="line"
        ),
        toolbox_opts=opts.ToolboxOpts(
            is_show=True,
            pos_left='right'
        ),
        visualmap_opts=opts.VisualMapOpts(
            is_show=True,
            type_="size",
            min_=0,
            max_=20,
            range_text=["最大值", "最小值"]),
        datazoom_opts=[
            opts.DataZoomOpts(range_start=50, range_end=100)],
    )
    bar = bar.dump_options_with_quotes()
    return bar


def effect_scatter_chart():
    # 涟漪散点图

    effect_scatter = EffectScatter()
    x_y_axis = get_chart_data()
    effect_scatter.add_xaxis(x_y_axis[0])
    for j in x_y_axis[1]:
        for key, value in j.items():
            effect_scatter.add_yaxis(
                key,
                value,
                label_opts=opts.LabelOpts(is_show=False))
    effect_scatter.set_series_opts(
        markpoint_opts=opts.MarkPointOpts(
            data=[
                opts.MarkPointItem(type_="max", name="最大值"),
                opts.MarkPointItem(type_="min", name="最小值"),
            ]
        ),
    )
    effect_scatter.set_global_opts(
        title_opts=opts.TitleOpts(
            title="API耗时统计",
            subtitle="生产环境",
            pos_left="30%",
            title_textstyle_opts=opts.TextStyleOpts(color='red'),
            subtitle_textstyle_opts=opts.TextStyleOpts(color='blue')
        ),
        xaxis_opts=opts.AxisOpts(
            name="运行时间",
            type_="category",
            boundary_gap=True,
            # axislabel_opts=opts.LabelOpts(rotate=15)
        ),
        yaxis_opts=opts.AxisOpts(
            name="实际的响应时间（单位：秒）",
            # min_=0,
            # max_=20
        ),
        legend_opts=opts.LegendOpts(
            type_='scroll',
            selected_mode='multiple',
            pos_left='right',
            pos_top='10%',
            orient='vertical'
        ),
        tooltip_opts=opts.TooltipOpts(
            trigger="axis",
            axis_pointer_type="line"
        ),
        toolbox_opts=opts.ToolboxOpts(
            is_show=True,
            pos_left='right'
        ),
        visualmap_opts=opts.VisualMapOpts(
            is_show=True,
            type_="size",
            min_=0,
            max_=20,
            range_text=["最大值", "最小值"]),
        datazoom_opts=[
            opts.DataZoomOpts(range_start=50, range_end=100)],
    )
    effect_scatter = effect_scatter.dump_options_with_quotes()
    return effect_scatter


class LineChartView(LoginRequiredMixin, APIView):
    def get(self, request, *args, **kwargs):
        return JsonResponse(json.loads(line_chart()))


class BarChartView(LoginRequiredMixin, APIView):
    def get(self, request, *args, **kwargs):
        return JsonResponse(json.loads(bar_chart()))


class EffectScatterChartView(LoginRequiredMixin, APIView):
    def get(self, request, *args, **kwargs):
        return JsonResponse(json.loads(effect_scatter_chart()))


class IndexView(LoginRequiredMixin, APIView):
    def get(self, request, *args, **kwargs):
        global next_url
        next_url = request.path_info
        if "/admin/guard/case/case_chart/" in next_url:
            next_url = next_url.replace("/admin/guard/case/case_chart/", "")
        # 获取路径中的用例id

        with open("guard/templates/index.html", "r", encoding="utf-8") as f:
            data = f.read()
        return HttpResponse(content=data)
