from rest_framework import serializers

from guard.models import Microservice, Case, Step, EnvironmentConfiguration


class MicroserviceSerializer(serializers.HyperlinkedModelSerializer):
    # 序列化

    class Meta:
        model = Microservice
        fields = "__all__"


class CaseSerializer(serializers.HyperlinkedModelSerializer):
    microservice_name = serializers.ReadOnlyField(source='case_microservice.microservice_name')

    # 外键序列化

    class Meta:
        model = Case
        fields = (
            'id',
            'case_microservice',
            'microservice_name',
            'case_name',
            'case_on_off',
            'dingtalk_on_off',
            'mailbox_on_off',
            'create_time',
            'update_time',
        )


class StepSerializer(serializers.HyperlinkedModelSerializer):
    case_name = serializers.ReadOnlyField(source='step_case.case_name')

    # 外键序列化

    class Meta:
        model = Step
        fields = (
            'id',
            'step_case',
            'case_name',
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
            'create_time',
            'update_time',
        )


class EnvironmentConfigurationSerializer(serializers.HyperlinkedModelSerializer):
    microservice_name = serializers.ReadOnlyField(source='environment_configuration_microservice.microservice_name')

    # 外键序列化

    class Meta:
        model = EnvironmentConfiguration
        fields = (
            'id',
            'environment_configuration_microservice',
            'microservice_name',
            'domain_name',
            'webhook',
            'secret',
            'recipient_email',
            'create_time',
            'update_time',
        )
