import boto3
import sys
from spawnAWS import load_aws_credentials_from_csv  # Adjust the import statement as necessary

def terminate_instance(region_name, instance_id):
    """
    Terminates an AWS EC2 instance based on the provided instance ID.

    Parameters:
    - region_name: The AWS region where the instance is located.
    - instance_id: The ID of the instance to terminate.
    """
    # Retrieve AWS credentials
    credentials = load_aws_credentials_from_csv()

    # Configure boto3 to use the retrieved credentials
    session = boto3.Session(
        aws_access_key_id=credentials['aws_access_key_id'],
        aws_secret_access_key=credentials['aws_secret_access_key'],
        region_name=region_name
    )
    ec2 = session.resource('ec2')
    instance = ec2.Instance(instance_id)
    response = instance.terminate()
    print(f"Terminating instance {instance_id}, status: {response['TerminatingInstances'][0]['CurrentState']['Name']}")

# Example usage
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python terminateServer.py <instance_id>")
        sys.exit(1)
    instance_id = sys.argv[1]
    region = 'us-west-2'  # Example region
    terminate_instance(region, instance_id)