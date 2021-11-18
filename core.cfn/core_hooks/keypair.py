"""Wrapper for keypair hook adding support for values from environment."""
import logging

from stacker.lookups.handlers.default import handler as default_handler
from stacker.lookups.handlers.output import handler as output_handler
import stacker.hooks.keypair as keypair

LOGGER = logging.getLogger(__name__)


def ensure_keypair_exists(provider, context, **kwargs):
    """Wrap ensure_keypair_exists with support for environment values."""
    if kwargs.get('keypair'):
        # keypair has been explicitly set; nothing to do here
        return keypair.ensure_keypair_exists(context=context,
                                             provider=provider,
                                             **kwargs)
    elif kwargs.get('keypair_from_output_handler'):
        keypair_name = output_handler(
            kwargs.get('keypair_from_output_handler'),
            provider=provider,
            context=context
        )
        return keypair.ensure_keypair_exists(context=context,
                                             provider=provider,
                                             keypair=keypair_name)
    elif kwargs.get('keypair_name_from_default_handler'):
        if '::' not in kwargs.get('keypair_name_from_default_handler'):
            LOGGER.error('Invalid value provided for '
                         'keypair_name_from_default_handler - need value in '
                         'the form of "env_var::fallback", received "%s".',
                         kwargs.get('keypair_name_from_default_handler'))
            return False

        keypair_name = default_handler(
            kwargs.get('keypair_name_from_default_handler'),
            provider=provider,
            context=context
        )
        if keypair_name in [None, '', '\'', '\'\'', 'undefined']:
            LOGGER.info(
                'Skipping keypair creation; default handler found no '
                'environment value matching "%s"...',
                kwargs.get('keypair_name_from_default_handler').split('::')[0])
            return True
        return keypair.ensure_keypair_exists(context=context,
                                             provider=provider,
                                             keypair=keypair_name)
    else:
        kwargs_string = ', '.join(
            "%s=%r" % (key, val) for (key, val) in kwargs.iteritems()
        )
        LOGGER.error('No valid argument provided to ensure_keypair_exists ('
                     'looking for one of keypair, keypair_from_output, or '
                     'keypair_from_default - received "%s")',
                     kwargs_string)
        return False
