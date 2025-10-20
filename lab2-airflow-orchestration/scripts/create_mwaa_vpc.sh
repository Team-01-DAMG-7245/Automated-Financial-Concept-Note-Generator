#!/bin/bash

set -e

export AWS_PROFILE=aurelia
export AWS_REGION=us-east-1

echo "🌐 Creating VPC infrastructure for MWAA..."
echo ""

# Create VPC
echo "1️⃣ Creating VPC..."
VPC_ID=$(aws ec2 create-vpc \
    --cidr-block 10.0.0.0/16 \
    --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=aurelia-mwaa-vpc},{Key=Project,Value=AURELIA}]' \
    --query 'Vpc.VpcId' \
    --output text)

echo "  ✅ VPC created: $VPC_ID"

# Enable DNS hostnames
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames
echo "  ✅ DNS hostnames enabled"
echo ""

# Create Internet Gateway
echo "2️⃣ Creating Internet Gateway..."
IGW_ID=$(aws ec2 create-internet-gateway \
    --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=aurelia-igw},{Key=Project,Value=AURELIA}]' \
    --query 'InternetGateway.InternetGatewayId' \
    --output text)

aws ec2 attach-internet-gateway --vpc-id $VPC_ID --internet-gateway-id $IGW_ID
echo "  ✅ Internet Gateway created and attached: $IGW_ID"
echo ""

# Create Private Subnets (MWAA requires 2 in different AZs)
echo "3️⃣ Creating Private Subnets..."
SUBNET_1=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 10.0.1.0/24 \
    --availability-zone us-east-1a \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=aurelia-private-subnet-1},{Key=Project,Value=AURELIA}]' \
    --query 'Subnet.SubnetId' \
    --output text)

SUBNET_2=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 10.0.2.0/24 \
    --availability-zone us-east-1b \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=aurelia-private-subnet-2},{Key=Project,Value=AURELIA}]' \
    --query 'Subnet.SubnetId' \
    --output text)

echo "  ✅ Private Subnet 1: $SUBNET_1 (us-east-1a)"
echo "  ✅ Private Subnet 2: $SUBNET_2 (us-east-1b)"
echo ""

# Create Public Subnets for NAT Gateways
echo "4️⃣ Creating Public Subnets..."
PUBLIC_SUBNET_1=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 10.0.101.0/24 \
    --availability-zone us-east-1a \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=aurelia-public-subnet-1},{Key=Project,Value=AURELIA}]' \
    --query 'Subnet.SubnetId' \
    --output text)

PUBLIC_SUBNET_2=$(aws ec2 create-subnet \
    --vpc-id $VPC_ID \
    --cidr-block 10.0.102.0/24 \
    --availability-zone us-east-1b \
    --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=aurelia-public-subnet-2},{Key=Project,Value=AURELIA}]' \
    --query 'Subnet.SubnetId' \
    --output text)

echo "  ✅ Public Subnet 1: $PUBLIC_SUBNET_1 (us-east-1a)"
echo "  ✅ Public Subnet 2: $PUBLIC_SUBNET_2 (us-east-1b)"
echo ""

# Allocate Elastic IPs for NAT Gateways
echo "5️⃣ Allocating Elastic IPs..."
EIP_1=$(aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text)
EIP_2=$(aws ec2 allocate-address --domain vpc --query 'AllocationId' --output text)
echo "  ✅ EIP 1: $EIP_1"
echo "  ✅ EIP 2: $EIP_2"
echo ""

# Create NAT Gateways
echo "6️⃣ Creating NAT Gateways (this takes 2-3 minutes)..."
NAT_1=$(aws ec2 create-nat-gateway \
    --subnet-id $PUBLIC_SUBNET_1 \
    --allocation-id $EIP_1 \
    --tag-specifications 'ResourceType=natgateway,Tags=[{Key=Name,Value=aurelia-nat-1},{Key=Project,Value=AURELIA}]' \
    --query 'NatGateway.NatGatewayId' \
    --output text)

NAT_2=$(aws ec2 create-nat-gateway \
    --subnet-id $PUBLIC_SUBNET_2 \
    --allocation-id $EIP_2 \
    --tag-specifications 'ResourceType=natgateway,Tags=[{Key=Name,Value=aurelia-nat-2},{Key=Project,Value=AURELIA}]' \
    --query 'NatGateway.NatGatewayId' \
    --output text)

echo "  ⏳ NAT Gateway 1: $NAT_1 (provisioning...)"
echo "  ⏳ NAT Gateway 2: $NAT_2 (provisioning...)"
echo ""
echo "  ⏳ Waiting for NAT Gateways to become available (2-3 minutes)..."

aws ec2 wait nat-gateway-available --nat-gateway-ids $NAT_1 $NAT_2

echo "  ✅ NAT Gateways are now available!"
echo ""

# Create Route Tables
echo "7️⃣ Creating Route Tables..."
PUBLIC_RT=$(aws ec2 create-route-table \
    --vpc-id $VPC_ID \
    --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=aurelia-public-rt},{Key=Project,Value=AURELIA}]' \
    --query 'RouteTable.RouteTableId' \
    --output text)

PRIVATE_RT_1=$(aws ec2 create-route-table \
    --vpc-id $VPC_ID \
    --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=aurelia-private-rt-1},{Key=Project,Value=AURELIA}]' \
    --query 'RouteTable.RouteTableId' \
    --output text)

PRIVATE_RT_2=$(aws ec2 create-route-table \
    --vpc-id $VPC_ID \
    --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=aurelia-private-rt-2},{Key=Project,Value=AURELIA}]' \
    --query 'RouteTable.RouteTableId' \
    --output text)

echo "  ✅ Route tables created"
echo ""

# Create Routes
echo "8️⃣ Creating Routes..."
aws ec2 create-route --route-table-id $PUBLIC_RT --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID > /dev/null
aws ec2 create-route --route-table-id $PRIVATE_RT_1 --destination-cidr-block 0.0.0.0/0 --nat-gateway-id $NAT_1 > /dev/null
aws ec2 create-route --route-table-id $PRIVATE_RT_2 --destination-cidr-block 0.0.0.0/0 --nat-gateway-id $NAT_2 > /dev/null
echo "  ✅ Routes configured"
echo ""

# Associate Route Tables
echo "9️⃣ Associating Route Tables with Subnets..."
aws ec2 associate-route-table --route-table-id $PUBLIC_RT --subnet-id $PUBLIC_SUBNET_1 > /dev/null
aws ec2 associate-route-table --route-table-id $PUBLIC_RT --subnet-id $PUBLIC_SUBNET_2 > /dev/null
aws ec2 associate-route-table --route-table-id $PRIVATE_RT_1 --subnet-id $SUBNET_1 > /dev/null
aws ec2 associate-route-table --route-table-id $PRIVATE_RT_2 --subnet-id $SUBNET_2 > /dev/null
echo "  ✅ Route tables associated"
echo ""

# Create Security Group
echo "🔟 Creating Security Group..."
SG_ID=$(aws ec2 create-security-group \
    --group-name aurelia-mwaa-sg \
    --description "Security group for MWAA environment" \
    --vpc-id $VPC_ID \
    --query 'GroupId' \
    --output text)

# Add tags to security group
aws ec2 create-tags \
    --resources $SG_ID \
    --tags Key=Name,Value=aurelia-mwaa-sg Key=Project,Value=AURELIA

# Allow all traffic within security group (required for MWAA)
aws ec2 authorize-security-group-ingress \
    --group-id $SG_ID \
    --protocol all \
    --source-group $SG_ID > /dev/null

echo "  ✅ Security Group created: $SG_ID"
echo ""

# Save configuration
mkdir -p ../infrastructure/vpc
cat > ../infrastructure/vpc/network-config.env << ENVEOF
export VPC_ID=$VPC_ID
export SUBNET_1=$SUBNET_1
export SUBNET_2=$SUBNET_2
export SECURITY_GROUP=$SG_ID
export NAT_GATEWAY_1=$NAT_1
export NAT_GATEWAY_2=$NAT_2
export INTERNET_GATEWAY=$IGW_ID
ENVEOF

echo "✅ VPC configuration saved to infrastructure/vpc/network-config.env"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ VPC Infrastructure Setup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Network Configuration:"
echo "  VPC:              $VPC_ID"
echo "  Private Subnet 1: $SUBNET_1 (us-east-1a)"
echo "  Private Subnet 2: $SUBNET_2 (us-east-1b)"
echo "  Security Group:   $SG_ID"
echo ""
echo "To use this configuration, run:"
echo "  source infrastructure/vpc/network-config.env"
echo ""
echo "Next step: Create MWAA environment"
