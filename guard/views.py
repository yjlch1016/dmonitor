from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

# Create your views here.
from rest_framework import viewsets

from guard.admin import MicroserviceAdmin, CaseAdmin
from guard.models import Microservice, Case, Step, EnvironmentConfiguration
from guard.serializers import MicroserviceSerializer, CaseSerializer, StepSerializer, \
    EnvironmentConfigurationSerializer


@login_required
def debug_microservice(Files, request):
    """
    调试微服务
    :param Files:
    :param request:
    :return:
    """

    MicroserviceAdmin.debug_microservice(request)
    return redirect('/admin/guard/runningresults/')


@login_required
def debug_case(Files, request):
    """
    调试用例
    :param Files:
    :param request:
    :return:
    """

    CaseAdmin.debug_case(request)
    return redirect('/admin/guard/runningresults/')


class MicroserviceViewSet(viewsets.ModelViewSet):
    """
    微服务列表
    """
    queryset = Microservice.objects.all().order_by('id')
    serializer_class = MicroserviceSerializer


class CaseViewSet(viewsets.ModelViewSet):
    """
    用例列表
    """
    queryset = Case.objects.all().order_by('id')
    serializer_class = CaseSerializer


class StepViewSet(viewsets.ModelViewSet):
    """
    步骤列表
    """
    queryset = Step.objects.all().order_by('id')
    serializer_class = StepSerializer


class EnvironmentConfigurationViewSet(viewsets.ModelViewSet):
    """
    环境配置列表
    """
    queryset = EnvironmentConfiguration.objects.all().order_by('id')
    serializer_class = EnvironmentConfigurationSerializer
