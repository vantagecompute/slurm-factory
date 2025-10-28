"""CDK Stacks for slurm-factory infrastructure."""

import hashlib

from aws_cdk import (
    Stack,
    RemovalPolicy,
    CfnOutput,
    Duration,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_iam as iam,
    aws_certificatemanager as acm,
    aws_route53 as route53,
    aws_route53_targets as targets,
)
from constructs import Construct


class SlurmFactoryBinaryCache(Stack):
    """Stack for Spack binary cache S3 bucket and CloudFront distribution."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        github_org: str = "vantagecompute",
        github_repo: str = "slurm-factory",
        domain_name: str | None = None,
        hosted_zone_id: str | None = None,
        **kwargs,
    ) -> None:
        """
        Initialize the binary cache stack.

        Args:
            scope: CDK app or parent construct
            construct_id: Unique identifier for this stack
            github_org: GitHub organization name for OIDC
            github_repo: GitHub repository name for OIDC
            domain_name: Optional custom domain (e.g., cache.slurm-factory.com)
            hosted_zone_id: Optional Route53 hosted zone ID for DNS validation
            **kwargs: Additional stack properties
        """
        super().__init__(scope, construct_id, **kwargs)

        # Generate a deterministic 5-character suffix for bucket name uniqueness
        # Uses account ID to ensure consistency across deployments
        account_hash = hashlib.md5(self.account.encode()).hexdigest()[:5]
        bucket_name = f"slurm-factory-spack-buildcache-{account_hash}"

        # S3 Bucket for binary cache
        self.bucket = s3.Bucket(
            self,
            "BinaryCacheBucket",
            bucket_name=bucket_name,
            versioned=False,
            public_read_access=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.RETAIN,
            auto_delete_objects=False,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldVersions",
                    enabled=True,
                    noncurrent_version_expiration=Duration.days(90),
                ),
            ],
        )

        # Origin Access Control for CloudFront (newer than OAI)
        oac = cloudfront.S3OriginAccessControl(
            self,
            "OAC",
            signing=cloudfront.Signing.SIGV4_ALWAYS,
        )

        # CloudFront distribution
        distribution_props = {
            "default_behavior": cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin(
                    self.bucket,
                    origin_access_control_id=oac.origin_access_control_id,
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                compress=True,
            ),
            "price_class": cloudfront.PriceClass.PRICE_CLASS_100,
            "comment": "CDN for slurm-factory Spack binary cache",
        }

        # Certificate for custom domain (if provided)
        certificate = None
        if domain_name and hosted_zone_id:
            hosted_zone = route53.HostedZone.from_hosted_zone_attributes(
                self,
                "HostedZone",
                hosted_zone_id=hosted_zone_id,
                zone_name=".".join(domain_name.split(".")[-2:]),  # Extract base domain
            )

            # Certificate must be in us-east-1 for CloudFront
            certificate = acm.Certificate(
                self,
                "Certificate",
                domain_name=domain_name,
                validation=acm.CertificateValidation.from_dns(hosted_zone),
            )

            distribution_props["domain_names"] = [domain_name]
            distribution_props["certificate"] = certificate

        self.distribution = cloudfront.Distribution(
            self,
            "Distribution",
            **distribution_props,
        )

        # Grant CloudFront OAC access to the bucket
        self.bucket.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                principals=[iam.ServicePrincipal("cloudfront.amazonaws.com")],
                actions=["s3:GetObject"],
                resources=[f"{self.bucket.bucket_arn}/*"],
                conditions={
                    "StringEquals": {
                        "AWS:SourceArn": f"arn:aws:cloudfront::{self.account}:distribution/{self.distribution.distribution_id}"
                    }
                },
            )
        )

        # Route53 DNS records for custom domain (A and AAAA for IPv4/IPv6)
        if domain_name and hosted_zone_id:
            # Create A record (IPv4)
            route53.ARecord(
                self,
                "AliasRecord",
                zone=hosted_zone,
                record_name=domain_name.split(".")[0],
                target=route53.RecordTarget.from_alias(
                    targets.CloudFrontTarget(self.distribution)
                ),
            )
            # Create AAAA record (IPv6)
            route53.AaaaRecord(
                self,
                "AliasRecordIPv6",
                zone=hosted_zone,
                record_name=domain_name.split(".")[0],
                target=route53.RecordTarget.from_alias(
                    targets.CloudFrontTarget(self.distribution)
                ),
            )

        # GitHub OIDC Provider
        # Note: This resource is manually managed and should not be deleted
        # If it already exists, delete the stack and recreate without changing this resource
        github_provider = iam.OpenIdConnectProvider(
            self,
            "GitHubOIDC",
            url="https://token.actions.githubusercontent.com",
            client_ids=["sts.amazonaws.com"],
            thumbprints=[
                "6938fd4d98bab03faadb97b34396831e3780aea1",  # GitHub Actions thumbprint
                "1c58a3a8518e8759bf075b76b750d4f2df264fcd",  # Backup thumbprint
            ],
        )

        # IAM Role for GitHub Actions
        github_repo_path = f"repo:{github_org}/{github_repo}:*"
        
        self.github_actions_role = iam.Role(
            self,
            "GitHubActionsRole",
            role_name="slurm-factory-github-actions",
            assumed_by=iam.FederatedPrincipal(
                federated=github_provider.open_id_connect_provider_arn,
                conditions={
                    "StringLike": {
                        "token.actions.githubusercontent.com:sub": github_repo_path,
                    },
                    "StringEquals": {
                        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
                    },
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity",
            ),
            description=f"Role for GitHub Actions in {github_org}/{github_repo}",
            max_session_duration=Duration.hours(3),  # 3 hours for long-running builds
        )

        # Grant GitHub Actions role permissions
        self.bucket.grant_read_write(self.github_actions_role)

        # Additional permissions for GitHub Actions
        self.github_actions_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:ListBucket",
                    "s3:GetBucketLocation",
                    "s3:ListBucketMultipartUploads",
                ],
                resources=[self.bucket.bucket_arn],
            )
        )

        self.github_actions_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "s3:PutObject",
                    "s3:GetObject",
                    "s3:DeleteObject",
                    "s3:AbortMultipartUpload",
                    "s3:ListMultipartUploadParts",
                ],
                resources=[f"{self.bucket.bucket_arn}/*"],
            )
        )

        # Outputs
        CfnOutput(
            self,
            "BucketName",
            value=self.bucket.bucket_name,
            description="S3 bucket name for binary cache",
        )

        CfnOutput(
            self,
            "BucketArn",
            value=self.bucket.bucket_arn,
            description="S3 bucket ARN",
        )

        CfnOutput(
            self,
            "DistributionDomain",
            value=self.distribution.distribution_domain_name,
            description="CloudFront distribution domain name",
        )

        CfnOutput(
            self,
            "DistributionId",
            value=self.distribution.distribution_id,
            description="CloudFront distribution ID",
        )

        CfnOutput(
            self,
            "GitHubActionsRoleArn",
            value=self.github_actions_role.role_arn,
            description="IAM role ARN for GitHub Actions",
        )

        if domain_name:
            CfnOutput(
                self,
                "CustomDomain",
                value=f"https://{domain_name}",
                description="Custom domain URL",
            )
