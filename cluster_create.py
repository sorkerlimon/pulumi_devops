import pulumi
import pulumi_aws as aws
import base64 

# Create ECS Cluster
cluster = aws.ecs.Cluster("DevCluster")

# Create IAM Role for EC2 instances
ecs_instance_role = aws.iam.Role("ecsInstanceRole",
    assume_role_policy="""{
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": "sts:AssumeRole",
                "Principal": {
                    "Service": "ec2.amazonaws.com"
                },
                "Effect": "Allow",
                "Sid": ""
            }
        ]
    }"""
)

# Attach ECS instance policy to role
ecs_instance_role_policy_attachment = aws.iam.RolePolicyAttachment(
    "ecsInstanceRolePolicyAttachment",
    role=ecs_instance_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AmazonEC2ContainerServiceforEC2Role"
)

# Create instance profile
ecs_instance_profile = aws.iam.InstanceProfile(
    "ecsInstanceProfile",
    role=ecs_instance_role.name
)
# Create Auto Scaling Group
asg = aws.autoscaling.Group(
    "ecsAutoScalingGroup",
    vpc_zone_identifiers=[
        "subnet-0f44ca2c89fe0990d",
    ],
    desired_capacity=1,
    min_size=1,
    max_size=1,
    # Fix: Specify launch template as an object
    launch_template={
        "id": aws.ec2.LaunchTemplate(
            "ecsLaunchTemplate",
            image_id="ami-06650ca7ed78ff6fa",
            instance_type="t2.micro",
            vpc_security_group_ids=["sg-0f3718488c1032dc5"],
            iam_instance_profile={
                "name": ecs_instance_profile.name
            },
            user_data=pulumi.Output.all(cluster.name).apply(
                lambda args: base64.b64encode(f"""#!/bin/bash
echo ECS_CLUSTER={args[0]} >> /etc/ecs/ecs.config""".encode()).decode()
            ),
            key_name="classtune-limon"
        ).id,
        "version": "$Latest"  # Use the latest version of the launch template
    },
    tags=[{
        "key": "Name",
        "value": "ecs-instance",
        "propagate_at_launch": True
    }]
)
# Set up VPC reference
vpc = aws.ec2.Vpc.get("classtune-vpc", "vpc-064681d4b6b8fa26c")

# Create ECS Capacity Provider with a valid name
capacity_provider = aws.ecs.CapacityProvider("custom-capacity-provider",  # Changed from ecsCapacityProvider
    auto_scaling_group_provider=aws.ecs.CapacityProviderAutoScalingGroupProviderArgs(
        auto_scaling_group_arn=asg.arn,
        managed_scaling=aws.ecs.CapacityProviderAutoScalingGroupProviderManagedScalingArgs(
            status="ENABLED",
            target_capacity=100,
            minimum_scaling_step_size=1,
            maximum_scaling_step_size=1
        ),
        managed_termination_protection="DISABLED"
    )
)

# Associate Capacity Provider with Cluster
cluster_capacity_providers = aws.ecs.ClusterCapacityProviders("clusterCapacityProviders",
    cluster_name=cluster.name,
    capacity_providers=[capacity_provider.name],
    default_capacity_provider_strategies=[aws.ecs.ClusterCapacityProvidersDefaultCapacityProviderStrategyArgs(
        base=1,
        weight=100,
        capacity_provider=capacity_provider.name
    )]
)

# Export the cluster name
pulumi.export('cluster_name', cluster.name)
pulumi.export('cluster_arn', cluster.arn)