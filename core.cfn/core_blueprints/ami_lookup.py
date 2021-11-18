#!/usr/bin/env python
"""Stacker module for creating a lambda function for looking up AMIs."""

from os import path

from troposphere import (
    AWSHelperFn, Export, GetAtt, Join, Output, Ref, Sub, awslambda, iam
)

import awacs.awslambda
import awacs.ec2
from awacs.sts import AssumeRole
from awacs.aws import Allow, Condition, Policy, Statement, PolicyDocument, Principal

from runway.cfngin.lookups.handlers.file import parameterized_codec
from runway.cfngin.blueprints.base import Blueprint
from runway.cfngin.blueprints.variables.types import CFNString

AWS_LAMBDA_DIR = path.join(path.dirname(path.realpath(__file__)),
                           'aws_lambda')
IAM_ARN_PREFIX = 'arn:aws:iam::aws:policy/service-role/'


class AmiLookup(Blueprint):
    """Extends Stacker Blueprint class."""

    ami_lookup_src = parameterized_codec(
        open(path.join(AWS_LAMBDA_DIR, 'ami_lookup', 'index.py'), 'r').read(),
        False  # disable base64 encoding
    )

    VARIABLES = {
        'AMILookupLambdaFunction': {'type': AWSHelperFn,
                                    'description': 'Lambda function code',
                                    'default': ami_lookup_src},
        'CustomerName': {'type': CFNString,
                         'description': 'The nickname for the new customer. '
                                        'Must be all lowercase letters, '
                                        'should not contain spaces or special '
                                        'characters, nor should it include '
                                        'any part of EnvironmentName.',
                         'allowed_pattern': '[-_ a-z]*',
                         'default': ''},
        'EnvironmentName': {'type': CFNString,
                            'description': 'Name of Environment',
                            'default': 'common'}
    }

    def add_resources_and_outputs(self):
        """Add resources and outputs to template."""
        template = self.template
        variables = self.get_variables()

        amilookuplambdarole = template.add_resource(
            iam.Role(
                'AMILookupLambdaRole',
                AssumeRolePolicyDocument=PolicyDocument(
                    Statement=[
                        Statement(
                            Effect=Allow,
                            Action=[AssumeRole],
                            Principal=Principal("Service", ["lambda.amazonaws.com"]),
                        )
                    ]
                ),
                ManagedPolicyArns=[
                    IAM_ARN_PREFIX + 'AWSLambdaBasicExecutionRole'
                ],
                Policies=[
                    iam.Policy(
                        PolicyName=Join('-', ['amilookup-lambda-role',
                                              variables['EnvironmentName'].ref,
                                              variables['CustomerName'].ref]),
                        PolicyDocument=Policy(
                            Version='2012-10-17',
                            Statement=[
                                Statement(
                                    Action=[awacs.ec2.DescribeImages],
                                    Effect=Allow,
                                    Resource=['*'],
                                    Sid='AMIAccess'
                                )
                            ]
                        )
                    )
                ]
            )
        )

        # If uploaded to S3 via stacker hook, use that URL; otherwise fall back
        # to the inline code
        if ('lambda' in self.context.hook_data and
                'CoreAMILookup' in self.context.hook_data['lambda']):
            code = self.context.hook_data['lambda']['CoreAMILookup']
        else:
            code = awslambda.Code(
                ZipFile=variables['AMILookupLambdaFunction']
            )

        amilookup = template.add_resource(
            awslambda.Function(
                'AMILookup',
                Description='Find latest AMI for given platform',
                Code=code,
                Handler='index.handler',
                Role=GetAtt(amilookuplambdarole, 'Arn'),
                Runtime='python3.9',
                Timeout=60
            )
        )
        template.add_output(
            Output(
                'FunctionName',
                Description='AMI lookup function name',
                Export=Export(
                    Sub('${AWS::StackName}-FunctionName')
                ),
                Value=Ref(amilookup)
            )
        )
        template.add_output(
            Output(
                'FunctionArn',
                Description='AMI lookup function Arn',
                Export=Export(
                    Sub('${AWS::StackName}-FunctionArn')
                ),
                Value=GetAtt(amilookup, 'Arn')
            )
        )
        template.add_output(
            Output(
                'FunctionRegion',
                Description='AMI lookup function region',
                Value=Ref('AWS::Region')
            )
        )

        # IAM Instance Roles and Profiles
        amilookupaccesspolicy = template.add_resource(
            iam.ManagedPolicy(
                'AmiLookupAccessPolicy',
                Description='Allows invocation of the AMI lookup lambda '
                            'function.',
                Path='/',
                PolicyDocument=Policy(
                    Version='2012-10-17',
                    Statement=[
                        Statement(
                            Action=[awacs.awslambda.InvokeFunction],
                            Effect=Allow,
                            Resource=[GetAtt(amilookup, 'Arn')]
                        )
                    ]
                )
            )
        )
        template.add_output(
            Output(
                'AccessPolicy',
                Description='Policy allowing use of the AMI lookup lambda '
                            'function',
                Export=Export(
                    Sub('${AWS::StackName}-%s' % 'AccessPolicy')
                ),
                Value=Ref(amilookupaccesspolicy)
            )
        )

    def create_template(self):
        """Create template (main function called by Stacker)."""
        self.template.set_version('2010-09-09')
        self.template.set_description("Sturdy Platform - Core - AMI Lookup - 1.0")
        self.add_resources_and_outputs()
