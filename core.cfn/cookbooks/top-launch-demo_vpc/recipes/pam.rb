#
# Cookbook Name:: vpn
# Recipe:: pam
#
# Copyright 2017, Sturdy Networks
#
# All rights reserved - Do Not Redistribute
#

# sturdy_openvpn::config, but for local PAM auth

# Create/deploy OpenVPN SSL keypair
sturdy_openvpn_create_ssl node['sturdy']['openvpn']['vpn_url'] do
  bucket node['sturdy']['openvpn']['chef_data_bucket_name']
  folder node['sturdy']['openvpn']['chef_data_bucket_folder']
  region node['sturdy']['openvpn']['chef_data_bucket_region']
end
# Update client .ovpn connection file on S3
sturdy_openvpn_create_client_config node['sturdy']['openvpn']['vpn_address'] do
  bucket node['sturdy']['openvpn']['chef_data_bucket_name']
  folder node['sturdy']['openvpn']['chef_data_bucket_folder']
  region node['sturdy']['openvpn']['chef_data_bucket_region']
  reneg_sec node['openvpn']['config']['reneg-sec']
end

pam_plugin = case node['platform_family']
             when 'debian'
               '/usr/lib/openvpn/openvpn-plugin-auth-pam.so'
             else # RHEL / amazon
               '/usr/lib64/openvpn/plugins/openvpn-plugin-auth-pam.so'
             end
node.default['openvpn']['config']['plugin'] = "#{pam_plugin} openvpn"
node.default['openvpn']['config']['auth-user-pass-verify'] = nil
node.default['openvpn']['config']['script-security'] = nil

file '/etc/pam.d/openvpn' do
  content "auth    required        pam_unix.so    shadow    nodelay\n"\
          "account required        pam_unix.so\n"
  mode 0644
end

# Deploy users here (e.g. user resource, users cookbook ,etc)
user 'duncan' do
  manage_home true # syntax here for chef >= 12.14.60
  comment 'LOCAL SYSTEM AUTH USER'
  home '/home/duncan'
  shell '/bin/bash'
  # The hash to use here can be generated via "mkpasswd -m sha-512" on linux
  # systems or by using the python passlib module (from pypi) on any system:
  # python -c "from __future__ import print_function; from builtins import input; from passlib.hash import sha512_crypt; print(sha512_crypt.encrypt(input('clear-text password: ')))"
  password '$6$rounds=656000$BMkB8AYIqIHTNqWH$/9.49u4MN7e4Y2dflwI5DvjrrrHysAvEsJ4DD5fewTrg2O6WdbX5cLA3lrcvy9USShFHr7jfjiZR4Yx8IFnM80'
end
