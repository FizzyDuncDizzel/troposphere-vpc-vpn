#!/usr/bin/env python
"""Stacker module for SSM-based chef-client run document."""

from troposphere import Ref, Output, ssm

from runway.cfngin.blueprints.base import Blueprint
from runway.cfngin.blueprints.variables.types import CFNString


class SSMChefRunDocuments(Blueprint):
    """Blueprint class for the SSM-based chef-client run document."""

    VARIABLES = {
        'SyncCommand': {'type': CFNString,
                        'description': 'Command to sync in Chef policy data.',
                        'default': '/etc/chef/sync_cookbooks.sh'},
        'ChefClientRunCommand': {'type': CFNString,
                                 'description': 'Command to perform '
                                                'chef-client run.',
                                 'default': '/etc/chef/perform_chef_run.sh'},
        'ExecutionTimeout': {'type': CFNString,
                             'description': 'The maximum time that the '
                                            'chef-client is allowed to run. '
                                            'Default is 3600 (1 hour). '
                                            'Maximum is 28800 (8 hours).',
                             'default': '3600'}
    }

    def add_resources(self):
        """Add resources to template."""
        template = self.template
        variables = self.get_variables()

        linuxdocument = template.add_resource(ssm.Document(
            'Linux',
            Content={
                'schemaVersion': '2.0',
                'description': 'Performs chef-client run',
                'parameters': {
                    'executionTimeout': {
                        'type': 'String',
                        'default': variables['ExecutionTimeout'].ref,
                        'description': 'The time in seconds for a command to '
                                       'complete before it is considered to '
                                       'have failed. Default is 3600 (1 hour)'
                                       '. Maximum is 28800 (8 hours).',
                        'allowedPattern': '([1-9][0-9]{0,3})|'
                                          '(1[0-9]{1,4})|'
                                          '(2[0-7][0-9]{1,3})|'
                                          '(28[0-7][0-9]{1,2})|'
                                          '(28800)'
                    }
                },
                'mainSteps': [
                    {'action': 'aws:runShellScript',
                     'name': 'runShellScript',
                     'inputs': {
                         'runCommand': [
                             variables['SyncCommand'].ref,
                             variables['ChefClientRunCommand'].ref
                         ],
                         'timeoutSeconds':'{{ executionTimeout }}',
                     }}
                ]
            },
            DocumentType='Command'
        ))
        template.add_output(Output(
            'LinuxDocumentName',
            Description='Chef-client run SSM document for Linux',
            Value=Ref(linuxdocument),
        ))

    def create_template(self):
        """Entrypoint for Stacker."""
        self.add_resources()
        self.template.set_description("Sturdy Platform - Core - SSM "
                                      "chef-client Run Documents - 1.0")
