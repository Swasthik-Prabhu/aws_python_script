import boto3
import requests

template = "tooplate"

# Step 1: Get my public IP
def get_my_ip():
    return requests.get("https://checkip.amazonaws.com").text.strip() + "/32"

# Step 2: Create key pair
def create_key_pair(ec2, key_pair_name):
    key_pair = ec2.create_key_pair(KeyName=key_pair_name)
    with open(f"{key_pair_name}.pem", "w") as f:
        f.write(key_pair['KeyMaterial'])
    return key_pair

# Step 3: Create security group
def create_security_group(ec2, sg_name, description, ingress_rules, vpc_id):
    sg = ec2.create_security_group(GroupName=sg_name, Description=description, VpcId=vpc_id)
    sg_id = sg['GroupId']
    ec2.authorize_security_group_ingress(GroupId=sg_id, IpPermissions=ingress_rules)
    return sg_id

# Step 4: Get latest Amazon Linux 2023 AMI
def get_latest_ami(ec2):
    images = ec2.describe_images(
        Owners=['amazon'],
        Filters=[
            {'Name': 'name', 'Values': ['al2023-ami-*-x86_64']},
            {'Name': 'architecture', 'Values': ['x86_64']},
            {'Name': 'state', 'Values': ['available']}
        ]
    )
    return sorted(images['Images'], key=lambda x: x['CreationDate'], reverse=True)[0]['ImageId']

# Step 5: Launch EC2 instance
def launch_instance(ec2, ami_id, key_pair_name, sg_id, user_data):
    instance = ec2.run_instances(
        ImageId=ami_id,
        InstanceType='t2.micro',
        KeyName=key_pair_name,
        SecurityGroupIds=[sg_id],
        MinCount=1,
        MaxCount=1,
        UserData=user_data
    )
    instance_id = instance['Instances'][0]['InstanceId']

    # Add Name tag
    ec2.create_tags(
        Resources=[instance_id],
        Tags=[{'Key': 'Name', 'Value': f"{template}-instance"}]
    )

    return instance_id

# Step 6: Wait until instance is running
def wait_for_instance(ec2, instance_id):
    waiter = ec2.get_waiter('instance_running')
    waiter.wait(InstanceIds=[instance_id])
    desc = ec2.describe_instances(InstanceIds=[instance_id])
    return desc['Reservations'][0]['Instances'][0]['PrivateIpAddress']

# Step 7: Create target group
def create_target_group(elbv2, vpc_id):
    response = elbv2.create_target_group(
        Name=f"{template}-tg",
        Protocol='HTTP',
        Port=80,
        VpcId=vpc_id,
        TargetType='instance',
        HealthCheckProtocol='HTTP',
        HealthCheckPort='80',
        HealthCheckPath='/',
        Matcher={'HttpCode': '200'}
    )
    return response['TargetGroups'][0]['TargetGroupArn']

# Step 8: Create ALB
def create_alb(elbv2, ec2, vpc_id, elb_sg_id):
    subnets = [sub['SubnetId'] for sub in ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['Subnets']]
    response = elbv2.create_load_balancer(
        Name=f"{template}-alb",
        Subnets=subnets,
        SecurityGroups=[elb_sg_id],
        Scheme='internet-facing',
        Type='application',
        IpAddressType='ipv4'
    )
    lb_arn = response['LoadBalancers'][0]['LoadBalancerArn']
    lb_dns = response['LoadBalancers'][0]['DNSName']
    return lb_arn, lb_dns

# Step 9: Create Listener
def create_listener(elbv2, lb_arn, target_group_arn):
    elbv2.create_listener(
        LoadBalancerArn=lb_arn,
        Protocol='HTTP',
        Port=80,
        DefaultActions=[{'Type': 'forward', 'TargetGroupArn': target_group_arn}]
    )

# Step 10: Register EC2 instance with Target Group
def register_instance_with_tg(elbv2, target_group_arn, instance_id):
    elbv2.register_targets(
        TargetGroupArn=target_group_arn,
        Targets=[{'Id': instance_id, 'Port': 80}]
    )

# Step 11: Main workflow
def main():
    ec2 = boto3.client('ec2')
    elbv2 = boto3.client('elbv2')

    # create key pair 
    key_pair_name = f"{template}-key"
    create_key_pair(ec2, key_pair_name)
    print(f"Key pair {key_pair_name} created....")

    vpc_id = ec2.describe_vpcs()['Vpcs'][0]['VpcId']

    # get my ip
    my_ip = get_my_ip()

    # create EC2 security group ingress rules
    ec2_ingress = [
        {'IpProtocol': 'tcp', 'FromPort': 22, 'ToPort': 22, 'IpRanges': [{'CidrIp': my_ip}]},
        {'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
    ]

    # create EC2 security group
    sg_id = create_security_group(ec2, f"{template}-sg", "Allow SSH + HTTP", ec2_ingress, vpc_id)
    print(f"Security group {template}-sg created with ID: {sg_id}")

    # create ALB ingress rules
    elb_ingress = [
        {'IpProtocol': 'tcp', 'FromPort': 80, 'ToPort': 80, 'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
    ]

    # create ALB security group
    elb_sg_id = create_security_group(ec2, f"{template}-elb-sg", "Allow HTTP for ALB", elb_ingress, vpc_id)
    print(f"ALB security group created with ID: {elb_sg_id}")

    # get latest Amazon Linux 2023 AMI
    ami_id = get_latest_ami(ec2)
    print(f"Latest Amazon Linux 2023 AMI ID: {ami_id}")

    # user data to install website
    user_data = '''#!/bin/bash
    yum update -y
    yum install -y httpd wget unzip
    systemctl start httpd
    systemctl enable httpd
    cd /var/www/html
    wget https://www.tooplate.com/zip-templates/2136_kool_form_pack.zip
    unzip 2136_kool_form_pack.zip
    cp -r 2136_kool_form_pack/* .
    rm -rf 2136_kool_form_pack 2136_kool_form_pack.zip
    chown -R apache:apache /var/www/html
    '''

    # launch EC2 instance
    instance_id = launch_instance(ec2, ami_id, key_pair_name, sg_id, user_data)
    print(f"EC2 instance launched with ID: {instance_id}")

    # wait for instance
    print("waiting for the instance to be running...")
    private_ip = wait_for_instance(ec2, instance_id)
    print(f"EC2 instance is running with private IP: {private_ip}")

    # create target group
    target_group_arn = create_target_group(elbv2, vpc_id)
    print("Target group created.")

    # create ALB
    lb_arn, lb_dns = create_alb(elbv2, ec2, vpc_id, elb_sg_id)
    print(f"ALB created. Access website at: http://{lb_dns}")

    # create listener
    create_listener(elbv2, lb_arn, target_group_arn)
    print("Listener created.")

    # register instance with target group
    register_instance_with_tg(elbv2, target_group_arn, instance_id)
    print(f'Instance "{instance_id}" registered with target group.')

if __name__ == '__main__':
    main()
