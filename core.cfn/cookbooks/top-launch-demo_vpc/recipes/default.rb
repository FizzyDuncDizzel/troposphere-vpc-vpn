#
# Cookbook Name:: vpn
# Recipe:: default
#
# Copyright 2017, Sturdy Networks
#
# All rights reserved - Do Not Redistribute
#


# include_recipe "#{cookbook_name}::platform"

# Read in environment attributes and set openvpn config settings if our standard
# attributes are set
sturdy_openvpn_update_attributes cookbook_name.chomp('_vpn') do
  action :nothing
end.run_action(:update)

# Logging/metrics/SSM management
include_recipe 'sturdy_openvpn::management'

# Install OpenVPN
include_recipe 'sturdy_openvpn::install'

# Create config/ssl files on S3 and setup LDAP auth
# include_recipe 'sturdy_openvpn::config'

# Alternatively, comment out the config recipe and use PAM auth
include_recipe "#{cookbook_name}::pam"

# Configure and start OpenVPN server
include_recipe 'sturdy_openvpn::server'
