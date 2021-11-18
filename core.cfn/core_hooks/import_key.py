import os
from runway.cfngin.session_cache import get_session

def import_key(provider, context, **kwargs):
    session = get_session(provider.region)
    client = session.client('ec2')
    resource = session.resource('ec2')

    key_name = kwargs.get('key_name')
    if key_exists(client, key_name):
        print("key %s already exists" % key_name)
        return True
    file_name = kwargs.get('key_location')

    dir_path = os.path.dirname(os.path.realpath(__file__))
    with open(dir_path+'/'+file_name, "r") as file:
        public_key = file.read()

    try:
        resource.import_key_pair(KeyName=key_name, PublicKeyMaterial=public_key)
        print("Created key %s" % key_name)
    except:
        return False
    return True


def key_exists(client, key_name):
    try:
        key_pair_info = client.describe_key_pairs(KeyNames=[key_name])
        return True
    except:
        return False
