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
        Helper method to find a specific step in a GitHub Actions workflow.
        
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

    def test_compiler_workflow_updates_index(self):
        """Test that compiler buildcache workflow updates index after adding mirror."""
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "build-and-publish-compiler.yml"
        
        test_step = self._find_test_step(workflow_path)
        assert test_step is not None, "Test buildcache installation step not found"
        
        # Check that the step includes buildcache update-index command
        run_script = test_step["run"]
        assert "spack buildcache update-index" in run_script, \
            "Workflow should update buildcache index after adding mirror"
        assert "slurm-factory-buildcache" in run_script, \
            "Workflow should update the slurm-factory-buildcache mirror"
        
        # Ensure update-index comes after mirror add
        mirror_add_pos = run_script.find("spack mirror add")
        update_index_pos = run_script.find("spack buildcache update-index")
        assert mirror_add_pos < update_index_pos, \
            "buildcache update-index should come after mirror add"

    def test_slurm_workflow_updates_index(self):
        """Test that slurm buildcache workflow trusts keys and uses cache-only installation."""
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "build-and-publish-slurm.yml"
        
        test_step = self._find_test_step(workflow_path)
        assert test_step is not None, "Test buildcache installation step not found"
        
        # Check that the step includes buildcache keys command (modern approach)
        run_script = test_step["run"]
        assert "spack buildcache keys --install --trust" in run_script, \
            "Workflow should install and trust buildcache keys"
        
        # Modern approach uses --cache-only flag instead of listing
        assert "--cache-only" in run_script, \
            "Workflow should use --cache-only for buildcache installation"
        
        # Ensure keys are installed before installing from buildcache
        keys_pos = run_script.find("spack buildcache keys")
        install_pos = run_script.find("--cache-only")
        assert keys_pos < install_pos, \
            "buildcache keys should be installed before installing packages"

    def test_compiler_workflow_structure(self):
        """Test that compiler workflow has proper structure for buildcache testing."""
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "build-and-publish-compiler.yml"
        
        test_step = self._find_test_step(workflow_path)
        assert test_step is not None, "Test buildcache installation step not found"
        
        run_script = test_step["run"]
        
        # Verify the order of operations for Docker-based test:
        # 1. Add mirror
        # 2. Update index
        # 3. List packages
        # 4. Install from buildcache
        
        mirror_add_pos = run_script.find("spack mirror add")
        update_index_pos = run_script.find("spack buildcache update-index")
        list_pos = run_script.find("spack buildcache list")
        install_pos = run_script.find("spack install")
        
        # All commands should be present
        assert mirror_add_pos >= 0, "mirror add should be present"
        assert update_index_pos >= 0, "update-index should be present"
        assert list_pos >= 0, "buildcache list should be present"
        assert install_pos >= 0, "install should be present"
        
        # Check order (no mirror remove in Docker-based workflow)
        assert mirror_add_pos < update_index_pos, "add should come before update-index"
        assert update_index_pos < list_pos, "update-index should come before list"
        assert list_pos < install_pos, "list should come before install"

    def test_slurm_workflow_structure(self):
        """Test that slurm workflow has proper structure for buildcache testing."""
        workflow_path = Path(__file__).parent.parent.parent / ".github" / "workflows" / "build-and-publish-slurm.yml"
        
        test_step = self._find_test_step(workflow_path)
        assert test_step is not None, "Test buildcache installation step not found"
        
        run_script = test_step["run"]
        
        # Verify the order of operations (modern Spack 1.0+ approach):
        # 1. Add mirrors
        # 2. Install and trust keys
        # 3. Install from buildcache using --cache-only
        
        first_mirror_add = run_script.find("spack mirror add")
        keys_pos = run_script.find("spack buildcache keys")
        install_pos = run_script.find("--cache-only")
        
        # All commands should be present
        assert first_mirror_add >= 0, "mirror add should be present"
        assert keys_pos >= 0, "buildcache keys should be present"
        assert install_pos >= 0, "--cache-only install should be present"
        
        # Check order
        assert first_mirror_add < keys_pos, "mirror add should come before keys install"
        assert keys_pos < install_pos, "keys install should come before cache-only install"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
