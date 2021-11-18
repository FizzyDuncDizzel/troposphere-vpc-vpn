"""Generic Cloudwatch Alarm."""

from troposphere import cloudwatch
from troposphere import Join, Not, If, Ref, Equals

from runway.cfngin.blueprints.base import Blueprint
from runway.cfngin.blueprints.variables.types import CFNString, CFNCommaDelimitedList


class BlueprintClass(Blueprint):
    """CloudWatch alarms blueprint."""

    VARIABLES = {
        'SnsAlarmArns': {
            'type': CFNCommaDelimitedList,
            'default': '',
            'description': 'List of Arn of the SNS alert topic to send alarms to',
        },
        'CustomerName': {
            'type': CFNString,
            'default': '',
            'description': 'The customers name',
        },
        'EnvironmentName': {
            'type': CFNString,
            'default': 'test',
            'description': 'Name of Environment',
        },
        'AlarmDescription': {
            'type': CFNString,
            'default': '',
            'description': 'Alarm description',
        },
        'AlarmThreshold': {
            'type': CFNString,
            'default': '0',
            'description': 'Expression for the rule to be scheduled',
        },
        'MetricNamespace': {
            'type': CFNString,
            'default': '',
            'description': 'Metric namespace',
        },
        'AlarmPeriod': {
            'type': CFNString,
            'default': '5',
            'description': 'How many minutes in the sample period',
        },
        'ComparisonOperator': {
            'type': CFNString,
            'description': 'Comparison operator',
            'allowed_values': [
                'GreaterThanOrEqualToThreshold',
                'GreaterThanThreshold',
                'LessThanThreshold',
                'LessThanOrEqualToThreshold'
            ]
        },
        'DimensionSets': {'type': dict,
            'description': 'Dimension key, value pairs',
            'default': {}
        },
        'MetricName': {
            'type': CFNString,
            'default': '',
            'description': 'The metric to alert on',
        },
        'EvaluationTime': {
            'type': CFNString,
            'default': '60',
            'description': 'Amount of time statistics applied. Specify time in seconds, in multiples of 60.',
        },
        'StatisticType': {
            'type': CFNString,
            'default': 'Average',
            'description': 'Statistics type',
            'allowed_values': [
                'Average',
                'Minimum',
                'Maximum',
                'Sum',
                'Sample Count'
            ]
        },
        'TreatMissingData': {
            'type': CFNString,
            'default': 'missing',
            'description': 'How alarms treats missing data',
            'allowed_values': [
                'breaching',
                'notBreaching',
                'ignore',
                'missing'
            ]
        }
    }

    def add_resources(self):
        """Add resources to template."""
        template = self.template
        variables = self.get_variables()

        d_set = []
        for key, value in variables['DimensionSets'].items():
            d_set += [cloudwatch.MetricDimension(Name=key, Value=value)]

        template.add_resource(
            cloudwatch.Alarm(
                'CloudWatchAlarm',
                AlarmDescription=variables['AlarmDescription'].ref,
                Namespace=variables['MetricNamespace'].ref,
                Statistic=variables['StatisticType'].ref,
                Period=variables['EvaluationTime'].ref,
                EvaluationPeriods=variables['AlarmPeriod'].ref,
                Threshold=variables['AlarmThreshold'].ref,
                AlarmActions=variables['SnsAlarmArns'].ref,
                ComparisonOperator=variables['ComparisonOperator'].ref,
                Dimensions=d_set,
                MetricName=variables['MetricName'].ref,
                TreatMissingData=variables['TreatMissingData'].ref
            )
        )

    def create_template(self):
        """Create CFN template."""
        self.template.set_version('2010-09-09')
        self.template.set_description("Generic Cloudwatch Alarm - 1.0.0")
        self.add_resources()