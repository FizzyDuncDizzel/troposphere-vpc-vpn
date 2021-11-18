name 'top-launch-demo_vpc'
maintainer 'Sturdy Networks'
maintainer_email 'devops@sturdynetworks.com'
license 'All rights reserved'
description 'Installs/Configures the VPC VPN'
long_description IO.read(File.join(File.dirname(__FILE__), 'README.md'))
version '1.0.0'

chef_version '>= 12.15'
supports 'ubuntu', '>= 16.04'

depends 'sturdy_openvpn', '~> 4.0'
