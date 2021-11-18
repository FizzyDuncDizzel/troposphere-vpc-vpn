#!/usr/bin/env python
"""Module with Elastic IP for VPN server."""

from troposphere import Export, GetAtt, Output, Ref, Sub, ec2

from runway.cfngin.blueprints.base import Blueprint
from runway.cfngin.blueprints.variables.types import CFNString


class VpnEip(Blueprint):
    """Blueprint for setting up the VPN server EIP."""

    VARIABLES = {
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

        # Elastic IPs
        vpnelasticip = template.add_resource(
            ec2.EIP(
                'VPNElasticIP',
                Domain='vpc'
            )
        )
        template.add_output([
            Output(
                'VpnEipPublicIp',
                Description='VPN instance public IP',
                Export=Export(Sub('${AWS::StackName}-VpnEipPublicIp')),
                Value=Ref(vpnelasticip)
            ),
            Output(
                'VpnEipAllocationId',
                Description='AllocationId of the VPN instance public IP',
                Export=Export(Sub('${AWS::StackName}-VpnEipAllocationId')),
                Value=GetAtt(vpnelasticip, 'AllocationId')
            )
        ])

    def create_template(self):
        """Create template (main function called by Stacker)."""
        self.template.set_version('2010-09-09')
        self.template.set_description("Sturdy Platform - Core - VPN Elastic "
                                      "IP - 1.0")
        self.add_resources()
