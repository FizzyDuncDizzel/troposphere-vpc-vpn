# vpn

Deploys the VPN server in AWS.

## Use

Connect to the VPN using the `client.ovpn` configuration file (stored in the Chef data bucket as `ENVIRONMENT/vpnservers/client.ovpn`) using your Sturdy LDAP credentials.

## Deployment

See READMEs in the Sturdy core stack and sturdy_openvpn cookbook.

### Updating Cookbook

Create an updated cookbooks package via `berks package` and upload it to the vpnservers Chef config directory on S3.

After uploading the cookbook archive, terminate the VPN instance to trigger its rebuild with the latest Chef code.

See "Updating VPN Server Configuration" in sturdy-stacker-core for more info.
