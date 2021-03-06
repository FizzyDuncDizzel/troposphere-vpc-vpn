#!/usr/bin/env python
"""Module with SNS alert subscription."""

from utils import standalone_output, version  # pylint: disable=relative-import

from troposphere import sns

from stacker.blueprints.base import Blueprint
from stacker.blueprints.variables.types import CFNString


class SnsSubscription(Blueprint):
    """Blueprint for attaching a subscription to a SNS topic."""

    VARIABLES = {
        'Endpoint': {'type': CFNString,
                     'description': 'Endpoint that will receive notifications '
                                    'from the topic.'},
        'Protocol': {'type': CFNString,
                     'description': 'Protocol for "Endpoint".',
                     'default': 'https'},
        'TopicARN': {'type': CFNString,
                     'description': 'SNS topic ARN'}
    }

    def add_resources(self):
        """Add resources to template."""
        template = self.template
        variables = self.get_variables()

        template.add_resource(
            sns.SubscriptionResource(
                'Subscription',
                Protocol=variables['Protocol'].ref,
                Endpoint=variables['Endpoint'].ref,
                TopicArn=variables['TopicARN'].ref
            )
        )

    def create_template(self):
        """Create template (main function called by Stacker)."""
        self.template.add_version('2010-09-09')
        self.template.add_description("Sturdy Platform - Core - SNS "
                                      "Subscription "
                                      "- {0}".format(version.version()))
        self.add_resources()


# Helper section to enable easy blueprint -> template generation
# (just run `python <thisfile>` to output the json)
if __name__ == "__main__":
    from stacker.context import Context

    standalone_output.json(SnsSubscription('test',
                                           Context({"namespace": "test"}),
                                           None))
