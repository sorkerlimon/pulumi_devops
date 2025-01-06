import pulumi
import pulumi_aws as aws

# Reference existing VPC
vpc = aws.ec2.Vpc.get("classtune-vpc",
    id="vpc-064681d4b6b8fa26c"
)

# Reference existing subnet
subnet = aws.ec2.Subnet.get("classtune-subnet-public1-ap-southeast-1a",
    id="subnet-0f44ca2c89fe0990d"
)

# EC2 Instance
instance = aws.ec2.Instance("classtune-ec2",
    instance_type="t2.micro",
    ami="ami-06650ca7ed78ff6fa",  # Ubuntu 20.04 LTS in ap-southeast-1
    subnet_id=subnet.id,
    vpc_security_group_ids=["sg-0f3718488c1032dc5"],
    key_name="classtune-limon",
    associate_public_ip_address=True,  # This ensures the instance gets a public IP
    tags={
        "Name": "classtune-ec2"
    }
)

# Export the instance's public IP and public DNS
pulumi.export('instance_id', instance.id)
pulumi.export('instance_public_ip', instance.public_ip)
pulumi.export('instance_public_dns', instance.public_dns)