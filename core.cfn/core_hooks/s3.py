"""Wrapper for keypair hook adding support for values from environment."""
import logging

from runway.cfngin.lookups.handlers.output import OutputLookup as output_handler
from runway.cfngin.session_cache import get_session

LOGGER = logging.getLogger(__name__)


def empty_bucket(provider, context, **kwargs):
    """Delete objects in S3 bucket."""
    if kwargs.get('bucket_from_output'):
        bucket_name = output_handler(
            kwargs.get('bucket_from_output'),
            provider=provider,
            context=context
        )
    elif kwargs.get('bucket_name'):
        bucket_name = kwargs.get('bucket_name')
    else:
        LOGGER.error('bucket_from_output or bucket_name must be specified.')
        return False

    session = get_session(provider.region)
    s3_resource = session.resource('s3')
    bucket = s3_resource.Bucket(bucket_name)
    bucket.object_versions.delete()
    return True
