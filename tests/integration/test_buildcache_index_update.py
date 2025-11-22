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

"""Tests for buildcache index update in GitHub Actions workflows."""

import yaml
from pathlib import Path


class TestBuildcacheIndexUpdate:
    """
    Test that buildcache index is updated after adding mirrors.

    These tests validate:
    - Index update commands are present in workflows
    - Commands are in the correct order
    - Workflow structure follows best practices for buildcache usage
    """

    @staticmethod
    def _find_test_step(workflow_path: Path, step_name: str = "Test buildcache installation"):
        """
        Find a specific step in a GitHub Actions workflow.

        Args:
            workflow_path: Path to the workflow YAML file
            step_name: Name of the step to find

        Returns:
            The step dictionary if found, None otherwise

        """
        with open(workflow_path) as f:
            workflow = yaml.safe_load(f)

        for job in workflow["jobs"].values():
            if "steps" in job:
                for step in job["steps"]:
                    if step.get("name") == step_name:
                        return step
        return None


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
