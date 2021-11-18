#!/usr/bin/env python
"""Module with SNS alert topic."""

from troposphere import Ref, Output, sns

from runway.cfngin.blueprints.base import Blueprint

class SnsTopic(Blueprint):
    """Blueprint for setting up SNS topic."""

    VARIABLES = {}

    def add_resources(self):
        """Add resources to template."""
        template = self.template

        pagerdutyalert = template.add_resource(
            sns.Topic(
                'Topic'
            )
        )

        template.add_output(
            Output(
                "%sARN" % pagerdutyalert.title,
                Description='SNS topic',
                Value=Ref(pagerdutyalert)
            )
        )

    def create_template(self):
        """Create template (main function called by Stacker)."""
        self.template.set_version('2010-09-09')
        self.template.set_description("Sturdy Platform - Core - SNS Topic - 1.0")
        self.add_resources()
