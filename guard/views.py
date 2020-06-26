from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

# Create your views here.


from guard.admin import MicroserviceAdmin, CaseAdmin


@login_required
def debug_microservice(Files, request):
    # 调试微服务

    MicroserviceAdmin.debug_microservice(request)
    return redirect('../')


@login_required
def debug_case(Files, request):
    # 调试用例

    CaseAdmin.debug_case(request)
    return redirect('../')
