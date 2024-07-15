# How to get AWS Access Keys

To create an AWS Access Key ID and Secret Access Key, follow these steps:

1. **Sign in to the AWS Management Console**: Go to the AWS Management Console and log in with your AWS account.

2. **Access the IAM (Identity and Access Management) Service**: In the search bar at the top, type "IAM" and select it from the results.

3. **Navigate to Users**: On the IAM dashboard, find the "Users" section in the navigation pane on the left side and click on it.

4. **Select Your User or Create a New One**: 
   - If you already have a user, click on the user's name to open the user details page.
   - If you need to create a new user, click the "Add user" button, enter the user details, select the "Programmatic access" checkbox under the AWS access type, and follow the prompts to set permissions.

5. **Manage Access Keys**:
   - On the user details page, find the "Security credentials" tab.
   - Scroll down to the "Access keys" section.

6. **Create New Access Key**:
   - Click the "Create access key" button.
   - A new Access Key ID and Secret Access Key will be generated.

7. **Download Credentials**:
   - Make sure to download the credentials by clicking the "Download .csv" button or copy the Access Key ID and Secret Access Key to a secure location. AWS does not show the secret access key again after the creation process.

Remember to handle these credentials securely. Do not share them or include them in your source code. Use IAM roles for applications running on AWS services, and consider using the AWS Secrets Manager or environment variables for managing access keys in your applications.


# How to attach a policy to generate key pair

The error message indicates that the AWS user `arn:aws:iam::471112928902:user/robosherpa` does not have the necessary permissions to perform the `CreateKeyPair` operation on EC2 resources. This is an IAM (Identity and Access Management) permissions issue.

To resolve this issue, you need to ensure that the IAM user `robosherpa` has the necessary permissions. Here's a step-by-step guide to address the problem:

1. **Log into the AWS Management Console** as an admin user or as a user with permissions to modify IAM policies.
2. **Navigate to the IAM service**.
3. **Find the user** `robosherpa` in the list of IAM users.
4. **Attach a policy** to the user that grants permissions to create a key pair. You can either attach an existing policy that includes the [`ec2:CreateKeyPair`](AWSVPNServer/spawnAWS.py) permission or create a new policy with the required permissions and attach it to the user.

If you decide to create a new policy, here is an example policy document that grants the necessary permissions:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ec2:DescribeKeyPairs",
                "ec2:CreateKeyPair",
                "ec2:DescribeImages",
                "ec2:TerminateInstances",
                "ec2:DescribeInstances",
                "ec2:DescribeInstanceStatus"
            ],
            "Resource": "*"
        }
    ]
}
```

This policy allows the `CreateKeyPair` action on all EC2 resources. Adjust the `Resource` field as necessary to restrict permissions according to your security requirements.

After attaching the necessary permissions to the `robosherpa` user, try running your script again. If the permissions are correctly set, the `CreateKeyPair` operation should succeed.


# How to set ssh permissions 

The error message `ssh: connect to host 54.191.22.178 port 22: Connection timed out` indicates that the SSH client is unable to establish a connection to the server at `54.191.22.178` on port 22. This can be due to several reasons:

1. **Security Group Configuration**: The security group attached to your EC2 instance may not allow inbound traffic on port 22 (SSH) from your IP address. You need to ensure that the security group has an inbound rule that allows SSH traffic (port 22) from your IP address or from all IP addresses (0.0.0.0/0).

2. **Network ACLs**: Network Access Control Lists (NACLs) can also block traffic. Ensure that the NACLs associated with your VPC allow inbound and outbound traffic on port 22.

3. **Instance State**: Ensure that the EC2 instance is running. If the instance is stopped, you won't be able to connect.

4. **Public IP Address**: Confirm that `54.191.22.178` is the current public IP address of your EC2 instance. If the instance was stopped and started again, it might have received a new public IP address unless you have an Elastic IP assigned.

5. **SSH Service**: Ensure that the SSH service is running on the EC2 instance. This is typically the case with standard AMIs, but if the instance has been customized, the SSH service might be stopped or misconfigured.

6. **Network Issues**: There could be network issues on your side preventing you from reaching the EC2 instance.

### Steps to Troubleshoot:

1. **Check Security Group Settings**:
   - Go to the EC2 Dashboard in the AWS Management Console.
   - Select your instance and look at the "Security" tab to find the security group.
   - Check the inbound rules of the security group to ensure SSH (port 22) is allowed.

2. **Verify Instance State and Public IP**:
   - Ensure the instance is running.
   - Confirm the public IP address of the instance.

3. **Check Network ACLs**:
   - Go to the VPC Dashboard and find the NACLs associated with your subnet.
   - Ensure the NACLs allow inbound and outbound traffic on port 22.

4. **Try Connecting Again**:
   - If you've made changes to the security group or NACLs, try connecting again using the same SSH command.

If after these checks and adjustments you still cannot connect, consider checking your local network settings or trying from a different network to rule out local network issues.