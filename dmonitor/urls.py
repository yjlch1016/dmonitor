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
from django.urls import path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import routers, permissions

from guard import views, pyecharts_views

router = routers.DefaultRouter()
router.register('microservice', views.MicroserviceViewSet)
router.register('case', views.CaseViewSet)
router.register('step', views.StepViewSet)
router.register('environment_configuration', views.EnvironmentConfigurationViewSet)

schema_view = get_schema_view(
    openapi.Info(
        title="轻量级生产环境接口监控平台API",
        default_version='V1.0.0',
        description="轻量级生产环境接口监控平台接口文档",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', xadmin.site.urls),

    url(r'^api/', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    # 配置django-rest-framwork路由

    url(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    url(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    url(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    # 配置drf-yasg路由

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

urlpatterns += [url(r'^silk/', include('silk.urls', namespace='silk'))]
# 配置django-silk路由

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [path('__debug__/', include(debug_toolbar.urls)), ] + urlpatterns
# 配置django-debug-toolbar路由
