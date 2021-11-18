"""Caches remote artifacts on S3."""

from os import path
from shutil import rmtree
from tempfile import mkdtemp
from urllib import urlretrieve
import logging
import re

from runway.cfngin.lookups.handlers.default import DefaultLookup as default_handler
from runway.cfngin.lookups.handlers.output import OutputLookup as output_handler
from runway.cfngin.session_cache import get_session

LOGGER = logging.getLogger(__name__)
COOKBOOK_PKG_PATTERN = re.compile(r'^cookbooks-[0-9]*\.(tar\.gz|tgz)')


def upload(provider, context, **kwargs):  # pylint: disable=W0613
    """Ensure artifact is present on S3.

    Args:
        provider (:class:`stacker.providers.base.BaseProvider`): provider
            instance
        context (:class:`stacker.context.Context`): context instance

    Returns: boolean for whether or not the hook succeeded.

    """
    always_upload_new_artifact = kwargs.get('always_upload_new_artifact',
                                            False)
    environment = kwargs.get('environment', 'all')
    if kwargs.get('artifact_bucket_output'):
        artifact_bucket = output_handler(
            kwargs.get('artifact_bucket_output'),
            provider=provider,
            context=context
        )
    elif kwargs.get('artifact_bucket_xref'):
        artifact_bucket = output_handler(
            kwargs.get('artifact_bucket_xref'),
            provider=provider,
            context=context,
            fqn=True
        )
    else:
        artifact_bucket = kwargs.get('artifact_bucket')
    if kwargs.get('s3_bucket_prefix_default'):
        bucket_prefix = default_handler(
            kwargs.get('s3_bucket_prefix_default'),
            provider=provider,
            context=context
        )
    else:
        bucket_prefix = 's3_bucket_prefix'

    if kwargs.get('source_url_default'):
        source_url = default_handler(
            kwargs.get('source_url_default'),
            provider=provider,
            context=context
        )
    else:
        source_url = kwargs.get('source_url')

    if kwargs.get('filename'):
        filename = kwargs.get('filename')
    else:
        filename = source_url.split('/')[-1]

    bucket_key = '%s/%s/%s' % (environment, bucket_prefix, filename)

    session = get_session(provider.region)
    client = session.client('s3')

    if always_upload_new_artifact is False:
        list_results = client.list_objects(
            Bucket=artifact_bucket,
            Prefix=bucket_key
        )
        if 'Contents' in list_results:
            LOGGER.info('Skipping artifact upload; s3://%s/%s already '
                        'present.',
                        artifact_bucket,
                        bucket_key)
            return True

    LOGGER.info('Downloading %s...', source_url)
    tmp_dir = mkdtemp()
    file_cache_location = path.join(tmp_dir, filename)
    urlretrieve(source_url, file_cache_location)

    LOGGER.info('Uploading artifact %s to s3://%s/%s',
                filename,
                artifact_bucket,
                bucket_key)
    client.upload_file(file_cache_location,
                       artifact_bucket,
                       bucket_key,
                       ExtraArgs={'ServerSideEncryption': 'AES256'})

    # Clean up cached download
    rmtree(tmp_dir)
    return True
