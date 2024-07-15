import subprocess
import os

# Function to install dependencies with version constraints to avoid conflicts
def install_dependencies():
    # Example version constraints that you need to adjust based on compatibility
    boto3_version = "1.24.12"  # Example version, adjust based on research
    aiobotocore_version = "2.12.3"  # Specifying the version if aiobotocore is needed

    subprocess.check_call([os.sys.executable, "-m", "pip", "install", f"boto3=={boto3_version}"])
    # Install aiobotocore only if your project requires it
    subprocess.check_call([os.sys.executable, "-m", "pip", "install", f"aiobotocore=={aiobotocore_version}"])

# Call the function to ensure dependencies are installed before importing them
#install_dependencies()

def load_aws_credentials_from_csv():
    credentials_path = os.path.join('key', 'robosherpa_accessKeys.csv')
    with open(credentials_path, mode='r', encoding='utf-8-sig') as csvfile:  # Note the encoding here
        reader = csv.DictReader(csvfile)
        for row in reader:  # Assuming there's only one set of credentials
            return {
                'aws_access_key_id': row['Access key ID'],
                'aws_secret_access_key': row['Secret access key']
            }

import boto3

import os
import csv
import pdb

region_name = 'us-west-2'  # Update this to your target region
credentials = load_aws_credentials_from_csv()


        
def create_key_pair(key_name, credentials=None):
    if credentials is None:
        credentials = {}  # Use default credentials
    
    ec2 = boto3.resource('ec2', region_name='us-west-2', **credentials)
    
    # Check if the key pair already exists
    existing_key_pairs = ec2.key_pairs.filter(KeyNames=[key_name])
    if list(existing_key_pairs):  # If the key pair exists
        print(f"Key pair {key_name} already exists.")
    else:
        # Create a new key pair
        key_pair = ec2.create_key_pair(KeyName=key_name)
        
        # Save the private key to a file
        with open(f"{key_name}.pem", "w") as file:
            file.write(key_pair.key_material)
        
        # Make sure the key is not publicly viewable
        os.chmod(f"{key_name}.pem", 0o400)
        print(f"Key pair {key_name} created and saved as {key_name}.pem")


def get_latest_ubuntu_lts_ami(region_name='us-west-2'):
    ec2 = boto3.client('ec2', region_name=region_name)
    filters = [
        {'Name': 'owner-id', 'Values': ['099720109477']},  # Canonical
        {'Name': 'name', 'Values': ['ubuntu/images/hvm-ssd/ubuntu-*-amd64-server-*']}
    ]
    images = ec2.describe_images(Filters=filters)['Images']
    
    if not images:
        raise ValueError("No Ubuntu LTS AMIs found. Check filters and region.")
    
    latest_image = max(images, key=lambda x: x['CreationDate'])
    return latest_image['ImageId']

def get_latest_amazon_linux_ami(region_name='us-west-2'):
    ec2 = boto3.client('ec2', region_name=region_name)
    filters = [
        {'Name': 'name', 'Values': ['amzn2-ami-hvm-*-x86_64-gp2']},
        {'Name': 'state', 'Values': ['available']}
    ]
    images = ec2.describe_images(Owners=['amazon'], Filters=filters)['Images']
    latest_image = max(images, key=lambda x: x['CreationDate'])
    return latest_image['ImageId']

def get_user_data_script():
    user_data_script = """#!/bin/bash
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
sudo ./easyrsa build-client-full client1 nopass

# Generate Diffie-Hellman parameters
sudo ./easyrsa gen-dh
sudo cp pki/dh.pem /etc/openvpn/dh2048.pem  # Adjust the filename as per your server.conf

# Copy certificates and keys
sudo cp pki/ca.crt pki/private/server.key pki/issued/server.crt pki/dh.pem /etc/openvpn

# Step 2: Configure OpenVPN
# Copy the sample server configuration to /etc/openvpn
sudo cp /usr/share/doc/openvpn-*/sample/sample-config-files/server.conf /etc/openvpn

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
# - Configure client settings for remote server, port, and protocol"""
    return user_data_script

def launch_instance(key_name):
    global region_name
    ami_id = get_latest_ubuntu_lts_ami(region_name)
    ec2 = boto3.resource('ec2', region_name=region_name)

    # User data script to install and configure OpenVPN
    user_data_script = get_user_data_script()

    # Specify your security group ID here
    security_group_id = 'sg-05ba7947e78044962'  # ssh group

    instances = ec2.create_instances(
        ImageId=ami_id,  # Use the dynamically fetched AMI ID
        MinCount=1,
        MaxCount=1,
        InstanceType='t2.micro',
        KeyName=key_name,
        UserData=user_data_script,  # Pass the user data script
        SecurityGroupIds=[security_group_id]
    )
    instance = instances[0]
    instance.wait_until_running()  # Wait for the instance to enter running state
    instance.load()  # Reload the instance attributes
    return instance.id, instance.public_ip_address  # Return both ID and public IP

import subprocess

# Main function
def main():
    global region_name, credentials
    boto3.setup_default_session(
        aws_access_key_id=credentials['aws_access_key_id'],
        aws_secret_access_key=credentials['aws_secret_access_key']
    )
    
    key_name = 'ec2-keypair'
    create_key_pair(key_name)
    instance_id, public_ip = launch_instance(key_name)  # Adjust launch_instance to return public_ip
    print(f"Launched EC2 Instance")
    print(f"Instance ID: {instance_id}")
    print(f"Public IP: {public_ip}")

    # Wait for instance status checks to complete
    ec2_client = boto3.client('ec2', region_name=region_name)
    print("Waiting for instance status checks to complete...")
    waiter = ec2_client.get_waiter('instance_status_ok')
    waiter.wait(InstanceIds=[instance_id])
    print("Instance is ready.")

    # SSH and SCP commands
    try:
        print("Attempting to SSH into the instance to copy setupUbuntuVPN.sh...")
        scp_command = f"scp -i {key_name}.pem setupUbuntuVPN.sh ubuntu@{public_ip}:/home/ubuntu/"
        subprocess.run(scp_command, check=True, shell=True)
        print("setupUbuntuVPN.sh copied successfully. Now running setupUbuntuVPN.sh on the server...")
        
        ssh_run_script = f"ssh -o StrictHostKeyChecking=no -i {key_name}.pem ubuntu@{public_ip}" 
        subprocess.run(ssh_run_script, check=True, shell=True)
        print("setupUbuntuVPN.sh executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to copy or execute setupUbuntuVPN.sh: {e}")

if __name__ == "__main__":
    main()