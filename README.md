# AWS EC2 + ALB Deployment Script

This repository contains a Python script that **automates the deployment of a web application** on AWS using **EC2, Security Groups, Target Groups, and an Application Load Balancer (ALB)**.

The script provisions all required AWS resources, installs Apache on the EC2 instance, deploys a sample template from [Tooplate](https://www.tooplate.com/), and makes the site available via an ALB DNS endpoint.

---

## 🚀 Features

* Automatically fetches your **public IP** for SSH access.
* Creates:

  * **EC2 Key Pair**
  * **Security Groups** for EC2 and ALB
  * **EC2 Instance** (Amazon Linux 2023 AMI)
  * **Target Group**
  * **Application Load Balancer (ALB)**
  * **Listener (HTTP 80)**
* Deploys a **sample HTML template** with Apache (`httpd`).
* Tags EC2 instance with a friendly `Name` for easy identification.

---

## 📦 Prerequisites

Before running the script, ensure you have:

1. **Python 3.7+** installed.
2. **AWS CLI configured** with credentials (`aws configure`).
3. **Required Python packages**:

   ```bash
   pip install boto3 requests
   ```
4. Proper **IAM permissions** to create:

   * EC2 instances
   * Key pairs
   * Security groups
   * ALBs and target groups

---

## ⚙️ Usage

1. Clone the repository:

   ```bash
   git clone https://github.com/Swasthik-Prabhu/aws_python_script.git
   cd aws_python_script
   ```

2. Run the script:

   ```bash
   python aws_python_script.py
   ```

3. After successful execution, you’ll see:

   * EC2 instance ID
   * Security group IDs
   * Target group ARN
   * ALB DNS URL

   Example output:

   ```
   Key pair tooplate-key created....
   Security group tooplate-sg created with ID: sg-0abcd1234
   EC2 instance launched with ID: i-0abcd1234
   waiting for the instance to be running...
   EC2 instance is running with private IP: 10.0.1.23
   Target group created.
   ALB created. Access website at: http://tooplate-alb-1234567890.us-east-1.elb.amazonaws.com
   Listener created.
   Instance "i-0abcd1234" registered with target group.
   ```

4. Open the printed **ALB DNS URL** in your browser to view the deployed site.

---

5. Add the security group of ELB in the Security group of the instance to the port 80 so that the instance can be accessed by the load balancer and marks it as healthy and you can access the website using the ELB.
## 🛠️ Customization

* **Template name**: The `template` variable at the top controls resource naming (`tooplate-sg`, `tooplate-alb`, etc.).
* **AMI & instance type**: Modify `get_latest_ami` or `InstanceType` in `launch_instance`.
* **User data script**: Update the `user_data` variable to install custom software or deploy different web content.

---

## 🧹 Cleanup

To avoid ongoing AWS charges, delete the created resources when done:

* EC2 instance
* Security groups
* Key pair
* Target group
* Application Load Balancer

You can do this via the **AWS Console** or with the AWS CLI:

```bash
aws ec2 terminate-instances --instance-ids <instance-id>
aws ec2 delete-security-group --group-id <sg-id>
aws ec2 delete-key-pair --key-name tooplate-key
aws elbv2 delete-target-group --target-group-arn <tg-arn>
aws elbv2 delete-load-balancer --load-balancer-arn <alb-arn>
```

---

## 📖 Notes

* Default VPC is used (`ec2.describe_vpcs()['Vpcs'][0]`).
* ALB is **internet-facing** and listens on port 80.
* SSH access is restricted to **your public IP** only.
* HTTP access (port 80) is open to the world.

---

## 📝 License

This project is licensed under the MIT License.

---
