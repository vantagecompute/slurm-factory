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
    """Test that buildcache index is updated after adding mirrors."""

    def test_compiler_workflow_updates_index(self):
        """Test that compiler buildcache workflow updates index after adding mirror."""
        workflow_path = Path(__file__).parent.parent / ".github" / "workflows" / "build-and-publish-compiler-buildcache.yml"
        
        with open(workflow_path) as f:
            workflow = yaml.safe_load(f)
        
        # Find the test buildcache installation job
        test_step = None
        for job in workflow["jobs"].values():
            if "steps" in job:
                for step in job["steps"]:
                    if step.get("name") == "Test buildcache installation":
                        test_step = step
                        break
        
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
        """Test that slurm buildcache workflow updates index after adding mirrors."""
        workflow_path = Path(__file__).parent.parent / ".github" / "workflows" / "build-and-publish-slurm-all.yml"
        
        with open(workflow_path) as f:
            workflow = yaml.safe_load(f)
        
        # Find the test buildcache installation job
        test_step = None
        for job in workflow["jobs"].values():
            if "steps" in job:
                for step in job["steps"]:
                    if step.get("name") == "Test buildcache installation":
                        test_step = step
                        break
        
        assert test_step is not None, "Test buildcache installation step not found"
        
        # Check that the step includes buildcache update-index command
        run_script = test_step["run"]
        assert "spack buildcache update-index" in run_script, \
            "Workflow should update buildcache index after adding mirrors"
        
        # Should update both mirrors
        assert run_script.count("spack buildcache update-index") >= 2, \
            "Workflow should update both compiler-buildcache and deps-buildcache mirrors"
        
        # Ensure update-index comes after mirror add
        mirror_add_pos = run_script.find("spack mirror add")
        update_index_pos = run_script.find("spack buildcache update-index")
        assert mirror_add_pos < update_index_pos, \
            "buildcache update-index should come after mirror add"

    def test_compiler_workflow_structure(self):
        """Test that compiler workflow has proper structure for buildcache testing."""
        workflow_path = Path(__file__).parent.parent / ".github" / "workflows" / "build-and-publish-compiler-buildcache.yml"
        
        with open(workflow_path) as f:
            workflow = yaml.safe_load(f)
        
        # Find the test buildcache installation step
        test_step = None
        for job in workflow["jobs"].values():
            if "steps" in job:
                for step in job["steps"]:
                    if step.get("name") == "Test buildcache installation":
                        test_step = step
                        break
        
        assert test_step is not None, "Test buildcache installation step not found"
        
        run_script = test_step["run"]
        
        # Verify the order of operations:
        # 1. Remove old mirror
        # 2. Add new mirror
        # 3. Update index
        # 4. List packages
        # 5. Install from buildcache
        
        mirror_remove_pos = run_script.find("spack mirror remove")
        mirror_add_pos = run_script.find("spack mirror add")
        update_index_pos = run_script.find("spack buildcache update-index")
        list_pos = run_script.find("spack buildcache list")
        install_pos = run_script.find("spack install")
        
        # All commands should be present
        assert mirror_remove_pos >= 0, "mirror remove should be present"
        assert mirror_add_pos >= 0, "mirror add should be present"
        assert update_index_pos >= 0, "update-index should be present"
        assert list_pos >= 0, "buildcache list should be present"
        assert install_pos >= 0, "install should be present"
        
        # Check order
        assert mirror_remove_pos < mirror_add_pos, "remove should come before add"
        assert mirror_add_pos < update_index_pos, "add should come before update-index"
        assert update_index_pos < list_pos, "update-index should come before list"
        assert list_pos < install_pos, "list should come before install"

    def test_slurm_workflow_structure(self):
        """Test that slurm workflow has proper structure for buildcache testing."""
        workflow_path = Path(__file__).parent.parent / ".github" / "workflows" / "build-and-publish-slurm-all.yml"
        
        with open(workflow_path) as f:
            workflow = yaml.safe_load(f)
        
        # Find the test buildcache installation step
        test_step = None
        for job in workflow["jobs"].values():
            if "steps" in job:
                for step in job["steps"]:
                    if step.get("name") == "Test buildcache installation":
                        test_step = step
                        break
        
        assert test_step is not None, "Test buildcache installation step not found"
        
        run_script = test_step["run"]
        
        # Verify the order of operations:
        # 1. Remove old mirrors
        # 2. Add new mirrors
        # 3. Update indexes
        # 4. List packages
        # 5. Install from buildcache
        
        first_mirror_add = run_script.find("spack mirror add")
        first_update_index = run_script.find("spack buildcache update-index")
        list_pos = run_script.find("spack buildcache list")
        install_pos = run_script.find("spack install")
        
        # All commands should be present
        assert first_mirror_add >= 0, "mirror add should be present"
        assert first_update_index >= 0, "update-index should be present"
        assert list_pos >= 0, "buildcache list should be present"
        assert install_pos >= 0, "install should be present"
        
        # Check order
        assert first_mirror_add < first_update_index, "mirror add should come before update-index"
        assert first_update_index < list_pos, "update-index should come before list"
        assert list_pos < install_pos, "list should come before install"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
