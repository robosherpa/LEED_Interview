#!/bin/bash
sudo apt update -y
sudo apt install -y openvpn easy-rsa

# Step 1: Setup Easy-RSA for CA and generate server and client certificates
sudo su
sudo make-cadir /etc/openvpn/easy-rsa
cd /etc/openvpn/easy-rsa

# Create vars file from template
# cp vars.example vars
# Update vars file as needed here, especially the KEY_* variables for your organization

# Initialize the PKI
sudo ./easyrsa init-pki

# Build the CA
sudo ./easyrsa build-ca nopass

# Generate server certificate and key
sudo ./easyrsa build-server-full server nopass

# Generate client certificate and key
sudo ./easyrsa build-client-full client nopass

# Generate Diffie-Hellman parameters
sudo ./easyrsa gen-dh
sudo cp pki/dh.pem /etc/openvpn/dh2048.pem  # Adjust the filename as per your server.conf

# Copy certificates and keys
sudo cp pki/ca.crt pki/private/server.key pki/issued/server.crt pki/dh.pem /etc/openvpn

# Step 2: Configure OpenVPN
# Copy the sample server configuration to /etc/openvpn
sudo cp /usr/share/doc/openvpn/examples/sample-config-files/server.conf.gz /etc/openvpn
sudo gunzip /etc/openvpn/server.conf.gz

# Edit /etc/openvpn/server.conf as needed, especially to point to the key and certificate locations
# Ensure to uncomment and set the appropriate directives for ca, cert, key, and dh

# Enable IP forwarding
sudo su -c 'echo "net.ipv4.ip_forward = 1" > /etc/sysctl.d/99-openvpn-forward.conf'
sysctl --system

# Step 3: Setup NAT for VPN clients
sudo iptables -t nat -A POSTROUTING -s 10.8.0.0/24 -o eth0 -j MASQUERADE
# Make sure to replace eth0 with your actual public network interface if different

# Persist iptables rules
sudo mkdir -p /etc/iptables
sudo su -c 'iptables-save > /etc/iptables/rules.v4'

# Generate TLS-Auth Key (if using TLS-Auth and missing):
sudo openvpn --genkey --secret /etc/openvpn/ta.key

# Enable and start OpenVPN service
sudo systemctl enable --now openvpn@server

# Additional security steps:
# - Harden server security (firewall settings, ssh configurations)
# - Regularly update software packages
# - Configure logging and monitoring for OpenVPN

# Client configuration setup:
# Generate the Private Key (client.key):
sudo openssl genpkey -algorithm RSA -out client.key -pkeyopt rsa_keygen_bits:2048

# Generate a Certificate Signing Request (CSR) for the Client:
sudo openssl req -new -key client.key -out client.csr

# Generate a new CA private key
sudo openssl genpkey -algorithm RSA -out ca.key -pkeyopt rsa_keygen_bits:2048

# Create a new CA certificate (ca.crt) using the CA private key
sudo openssl req -x509 -new -nodes -key ca.key -sha256 -days 3650 -out ca.crt

# Sign the CSR with your CA to generate the client.crt (this assumes you have a CA setup):
sudo openssl x509 -req -in client.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out client.crt -days 3650

# - Generate and securely distribute client configuration files (.ovpn)
# - Include CA certificate, client certificate, and client key in the client configuration
# - Configure client settings for remote server, port, and protocol