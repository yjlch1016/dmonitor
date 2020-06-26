"""dmonitor URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import xadmin
from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from django.urls import path

from guard import views, pyecharts_views

urlpatterns = [
    path('admin/', xadmin.site.urls),

    url(r'^admin/guard/microservice/debug_microservice/(\d+)$', views.debug_microservice, name='debug_microservice'),
    # 运行微服务路由

    url(r'^admin/guard/case/debug_case/(\d+)$', views.debug_case, name='debug_case'),
    # 运行用例路由

    url(r'^admin/guard/case/case_chart/(\d+)$', pyecharts_views.IndexView.as_view(), name='create_chart'),
    path('pyecharts/line/', pyecharts_views.LineChartView.as_view(), name='pyecharts'),
    path('pyecharts/bar/', pyecharts_views.BarChartView.as_view(), name='pyecharts'),
    path('pyecharts/effect_scatter/', pyecharts_views.EffectScatterChartView.as_view(), name='pyecharts'),
    # 用例图表路由
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
# 配置媒体文件url转发
