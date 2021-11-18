#!/usr/bin/env python
"""Module with IAM roles."""

from troposphere import Export, Join, Output, Ref, Sub, iam

import awacs.cloudwatch
import awacs.ds
import awacs.ec2
import awacs.logs
import awacs.s3
import awacs.ssm
from awacs.sts import AssumeRole
from awacs.aws import Allow, Condition, Policy, Statement, PolicyDocument, Principal
# Linter is incorrectly flagging the automatically generated functions in awacs
from awacs.aws import StringLike  # pylint: disable=no-name-in-module

from runway.cfngin.blueprints.base import Blueprint
from runway.cfngin.blueprints.variables.types import CFNString


class Roles(Blueprint):
    """Stacker blueprint for common instance role(s)."""

    VARIABLES = {
        'ChefBucketArn': {'type': CFNString,
                          'description': 'Arn of bucket storing core Chef '
                                         'configuration',
                          'default': 'common'},
        'ChefDataBucketArn': {'type': CFNString,
                              'description': 'Arn of bucket storing extra '
                                             'Chef data',
                              'default': 'citadel'},
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

    def add_resources(self):
        """Add resources to template."""
        template = self.template
        variables = self.get_variables()

        # IAM Instance Roles and Profiles
        commonpolicy = template.add_resource(
            iam.ManagedPolicy(
                'CommonPolicy',
                Description='Common instance policy; allows SSM management '
                            'and CloudWatch publishing.',
                Path='/',
                PolicyDocument=Policy(
                    Version='2012-10-17',
                    Statement=[
                        Statement(
                            Action=[awacs.ec2.DescribeInstances,
                                    awacs.ec2.DescribeTags,
                                    awacs.ec2.CreateTags],
                            Effect=Allow,
                            Resource=['*']
                        ),
                        Statement(
                            Action=[
                                awacs.logs.CreateLogGroup,
                                awacs.logs.CreateLogStream,
                                awacs.logs.PutLogEvents,
                                awacs.logs.DescribeLogStreams,
                                awacs.logs.DescribeLogGroups
                            ],
                            Effect=Allow,
                            Resource=[
                                'arn:aws:logs:*:*:*'
                            ]
                        ),
                        Statement(
                            Action=[awacs.cloudwatch.PutMetricData],
                            Effect=Allow,
                            Resource=['*']
                        ),
                        Statement(
                            Action=[awacs.aws.Action('s3', 'List*'),
                                    awacs.s3.GetBucketVersioning],
                            Effect=Allow,
                            Resource=[
                                variables['ChefBucketArn'].ref
                            ]
                        ),
                        Statement(
                            Action=[awacs.aws.Action('s3', 'Get*'),
                                    awacs.aws.Action('s3', 'List*')],
                            Effect=Allow,
                            Resource=[
                                Join('', [variables['ChefBucketArn'].ref,
                                          '/*'])
                            ]
                        ),
                        Statement(
                            Action=[awacs.aws.Action('s3', 'Get*'),
                                    awacs.aws.Action('s3', 'List*')],
                            Effect=Allow,
                            Resource=[
                                Join('', [variables['ChefDataBucketArn'].ref,
                                          '/all/*'])
                            ]
                        ),
                        Statement(  # Required for Jenkins invoked CodeBuild
                            Action=[awacs.s3.GetBucketVersioning],
                            Effect=Allow,
                            Resource=[variables['ChefDataBucketArn'].ref]
                        ),
                        Statement(
                            Action=[awacs.s3.ListBucket],
                            Effect=Allow,
                            Resource=[
                                Join('', [variables['ChefDataBucketArn'].ref])
                            ],
                            Condition=Condition(
                                StringLike('s3:prefix', ['', 'all/*'])
                            )
                        ),
                        Statement(  # For wildcard matching of parameters
                            Action=[awacs.ssm.DescribeParameters],
                            Effect=Allow,
                            Resource=['*']
                        ),
                        Statement(
                            Action=[awacs.ssm.GetParameters],
                            Effect=Allow,
                            Resource=[
                                Join(':', ['arn:aws:ssm',
                                           Ref('AWS::Region'),
                                           Ref('AWS::AccountId'),
                                           'parameter/all.*']),
                                Join(':', ['arn:aws:ssm',
                                           Ref('AWS::Region'),
                                           Ref('AWS::AccountId'),
                                           'parameter/all/*'])
                            ]
                        ),
                        # Platform downloading
                        Statement(
                            Action=[awacs.s3.ListBucket,
                                    awacs.s3.GetObject],
                            Effect=Allow,
                            Resource=[
                                'arn:aws:s3:::sturdy-platform*',
                                'arn:aws:s3:::onica-platform*',
                            ]
                        ),
                        # SSM
                        # Adapted from EC2RoleforSSM with the following changes
                        #   * Dropping the Put/Get S3 * access
                        #   * Dropping the GetParameters * access
                        Statement(
                            Action=[awacs.ssm.DescribeAssociation,
                                    awacs.aws.Action(
                                        'ssm',
                                        'GetDeployablePatchSnapshotForInstance'
                                    ),
                                    awacs.ssm.GetDocument,
                                    awacs.ssm.ListAssociations,
                                    awacs.ssm.ListInstanceAssociations,
                                    awacs.ssm.PutInventory,
                                    awacs.ssm.UpdateAssociationStatus,
                                    awacs.ssm.UpdateInstanceAssociationStatus,
                                    awacs.aws.Action(
                                        'ssm',
                                        'UpdateInstanceInformation')],
                            Effect=Allow,
                            Resource=['*']
                        ),
                        Statement(
                            Action=[awacs.aws.Action('ec2messages',
                                                     'AcknowledgeMessage'),
                                    awacs.aws.Action('ec2messages',
                                                     'DeleteMessage'),
                                    awacs.aws.Action('ec2messages',
                                                     'FailMessage'),
                                    awacs.aws.Action('ec2messages',
                                                     'GetEndpoint'),
                                    awacs.aws.Action('ec2messages',
                                                     'GetMessages'),
                                    awacs.aws.Action('ec2messages',
                                                     'SendReply')],
                            Effect=Allow,
                            Resource=['*']
                        ),
                        Statement(
                            Action=[awacs.ec2.DescribeInstanceStatus],
                            Effect=Allow,
                            Resource=['*']
                        ),
                        Statement(
                            Action=[awacs.ds.CreateComputer,
                                    awacs.ds.DescribeDirectories],
                            Effect=Allow,
                            Resource=['*']
                        ),
                        Statement(
                            Action=[awacs.s3.ListBucket],
                            Effect=Allow,
                            Resource=[
                                'arn:aws:s3:::amazon-ssm-packages-*'
                            ]
                        )
                    ]
                )
            )
        )
        commonrole = template.add_resource(
            iam.Role(
                'CommonRole',
                AssumeRolePolicyDocument=PolicyDocument(
                    Statement=[
                        Statement(
                            Effect=Allow,
                            Action=[AssumeRole],
                            Principal=Principal("Service", ["ec2.amazonaws.com"]),
                        )
                    ]
                ),
                ManagedPolicyArns=[Ref(commonpolicy)],
                Path='/'
            )
        )
        commoninstanceprofile = template.add_resource(
            iam.InstanceProfile(
                'CommonInstanceProfile',
                Path='/',
                Roles=[Ref(commonrole)]
            )
        )
        template.add_output(
            Output(
                commonpolicy.title,
                Description='Common instance policy',
                Export=Export(
                    Sub('${AWS::StackName}-%s' % commonpolicy.title)
                ),
                Value=Ref(commonpolicy)
            )
        )
        template.add_output(
            Output(
                commonrole.title,
                Description='Common instance role',
                Export=Export(Sub('${AWS::StackName}-%s' % commonrole.title)),
                Value=Ref(commonrole)
            )
        )
        template.add_output(
            Output(
                commoninstanceprofile.title,
                Description='Common instance profile',
                Export=Export(
                    Sub('${AWS::StackName}-%s' % commoninstanceprofile.title)
                ),
                Value=Ref(commoninstanceprofile)
            )
        )

    def create_template(self):
        """Create template (main function called by Stacker)."""
        self.template.set_version('2010-09-09')
        self.template.set_description("Sturdy Platform - Core - Roles - 1.0")
        self.add_resources()
