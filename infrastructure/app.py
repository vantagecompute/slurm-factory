#!/usr/bin/env python3
# Copyright 2025 Vantage Compute Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""CDK app for slurm-factory infrastructure."""

import os
from aws_cdk import App, Environment
from infrastructure.stacks import SlurmFactoryBinaryCache

app = App()

# Get configuration from environment or context
github_org = os.environ.get("CDK_GITHUB_ORG", "vantagecompute")
github_repo = os.environ.get("CDK_GITHUB_REPO", "slurm-factory")
domain_name = os.environ.get("CDK_DOMAIN_NAME", "slurm-factory-spack-binary-cache.vantagecompute.ai")
hosted_zone_id = os.environ.get("CDK_HOSTED_ZONE_ID", "Z076740924E27W77EXSVN")

# AWS environment
account = os.environ.get("CDK_DEFAULT_ACCOUNT")
region = os.environ.get("CDK_DEFAULT_REGION", "us-east-1")

env = Environment(account=account, region=region) if account else None

# Create the stack
SlurmFactoryBinaryCache(
    app,
    "SlurmFactoryInfraStack",
    github_org=github_org,
    github_repo=github_repo,
    domain_name=domain_name,
    hosted_zone_id=hosted_zone_id,
    env=env,
    description="Infrastructure for slurm-factory Spack binary cache",
)

app.synth()
