"""Tests for the backporter tool."""

import subprocess
from pathlib import Path

import pytest

from backporter.core import (
    BackportInput,
    backport,
    find_recipe_file,
    get_recipe_version,
    update_sha256sums,
    update_srcrev,
)
from backporter.parser import parse_upgrade_commit


@pytest.fixture
def git_layer(tmp_path):
    """Create a minimal git repo with a recipe file."""
    layer = tmp_path / "meta-aws"
    recipes_dir = layer / "recipes-devtools" / "python"
    recipes_dir.mkdir(parents=True)

    # Create a recipe file
    recipe_file = recipes_dir / "python3-botocore_1.43.19.bb"
    recipe_file.write_text(
        'SUMMARY = "python3 botocore"\n'
        'DESCRIPTION = "The low-level, core functionality of boto3."\n'
        'SRC_URI = "git://github.com/boto/botocore.git;protocol=https;branch=master"\n'
        'SRCREV = "oldoldoldoldoldoldoldoldoldoldoldoldold0"\n'
        "inherit setuptools3\n"
    )

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=layer, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"], cwd=layer, capture_output=True, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"], cwd=layer, capture_output=True, check=True
    )
    subprocess.run(["git", "add", "--all"], cwd=layer, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=layer, capture_output=True, check=True)
    subprocess.run(
        ["git", "branch", "-M", "wrynose-next"], cwd=layer, capture_output=True, check=True
    )

    return layer


@pytest.fixture
def git_layer_sha256(tmp_path):
    """Create a minimal git repo with a sha256sum-based recipe."""
    layer = tmp_path / "meta-aws"
    recipes_dir = layer / "recipes-devtools" / "amazon-corretto"
    recipes_dir.mkdir(parents=True)

    recipe_file = recipes_dir / "corretto-21-bin_21.0.10.9.1.bb"
    recipe_file.write_text(
        'SUMMARY = "Amazon Corretto 21"\n'
        'SRC_URI:append:aarch64 = " https://corretto.aws/downloads/resources/${PV}/amazon-corretto-${PV}-linux-aarch64.tar.gz;name=aarch64"\n'
        'SRC_URI:append:x86-64 = " https://corretto.aws/downloads/resources/${PV}/amazon-corretto-${PV}-linux-x64.tar.gz;name=x86-64"\n'
        'SRC_URI[x86-64.sha256sum] = "aaaa1111aaaa1111aaaa1111aaaa1111aaaa1111aaaa1111aaaa1111aaaa1111"\n'
        'SRC_URI[aarch64.sha256sum] = "bbbb2222bbbb2222bbbb2222bbbb2222bbbb2222bbbb2222bbbb2222bbbb2222"\n'
        "require corretto-bin-common.inc\n"
    )

    subprocess.run(["git", "init"], cwd=layer, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"], cwd=layer, capture_output=True, check=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"], cwd=layer, capture_output=True, check=True
    )
    subprocess.run(["git", "add", "--all"], cwd=layer, capture_output=True, check=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=layer, capture_output=True, check=True)
    subprocess.run(
        ["git", "branch", "-M", "scarthgap-next"], cwd=layer, capture_output=True, check=True
    )

    return layer


class TestFindRecipeFile:
    def test_finds_recipe(self, git_layer):
        result = find_recipe_file(git_layer, "python3-botocore")
        assert result is not None
        assert result.name == "python3-botocore_1.43.19.bb"

    def test_returns_none_for_missing_recipe(self, git_layer):
        result = find_recipe_file(git_layer, "nonexistent-recipe")
        assert result is None


class TestGetRecipeVersion:
    def test_extracts_version(self):
        path = Path("python3-botocore_1.43.19.bb")
        assert get_recipe_version(path) == "1.43.19"

    def test_complex_version(self):
        path = Path("corretto-21-bin_21.0.11.10.1.bb")
        assert get_recipe_version(path) == "21.0.11.10.1"


class TestUpdateSrcrev:
    def test_replaces_srcrev(self):
        content = 'SRCREV = "oldoldoldoldoldoldoldoldoldoldoldoldold0"\n'
        result = update_srcrev(content, "newnewnewnewnewnewnewnewnewnewnewnewnewnew1")
        assert 'SRCREV = "newnewnewnewnewnewnewnewnewnewnewnewnewnew1"' in result
        assert "oldoldold" not in result

    def test_no_srcrev(self):
        content = 'SUMMARY = "test"\n'
        result = update_srcrev(content, "abc123")
        assert result == content


class TestUpdateSha256sums:
    def test_replaces_sha256sums(self):
        content = (
            'SRC_URI[x86-64.sha256sum] = "aaaa1111aaaa1111aaaa1111aaaa1111aaaa1111aaaa1111aaaa1111aaaa1111"\n'
            'SRC_URI[aarch64.sha256sum] = "bbbb2222bbbb2222bbbb2222bbbb2222bbbb2222bbbb2222bbbb2222bbbb2222"\n'
        )
        result = update_sha256sums(
            content,
            {
                "x86-64": "cccc3333cccc3333cccc3333cccc3333cccc3333cccc3333cccc3333cccc3333",
                "aarch64": "dddd4444dddd4444dddd4444dddd4444dddd4444dddd4444dddd4444dddd4444",
            },
        )
        assert "cccc3333" in result
        assert "dddd4444" in result
        assert "aaaa1111" not in result
        assert "bbbb2222" not in result


class TestBackport:
    def test_srcrev_backport(self, git_layer):
        input = BackportInput(
            recipe="python3-botocore",
            version="1.43.55",
            target_branch="wrynose-next",
            srcrev="b71d5637f58df4bc61953b80902b3c040c7af889",
        )

        result = backport(git_layer, input)

        assert result.success is True
        assert result.old_version == "1.43.19"
        assert result.new_version == "1.43.55"
        assert result.branch_name == "backport/python3-botocore_1.43.55_to_wrynose-next"

        # Verify the file was renamed
        new_file = git_layer / "recipes-devtools" / "python" / "python3-botocore_1.43.55.bb"
        assert new_file.exists()

        # Verify SRCREV was updated
        content = new_file.read_text()
        assert "b71d5637f58df4bc61953b80902b3c040c7af889" in content
        assert "oldoldold" not in content

        # Verify old file is gone
        old_file = git_layer / "recipes-devtools" / "python" / "python3-botocore_1.43.19.bb"
        assert not old_file.exists()

    def test_sha256sum_backport(self, git_layer_sha256):
        input = BackportInput(
            recipe="corretto-21-bin",
            version="21.0.11.10.1",
            target_branch="scarthgap-next",
            sha256sums={
                "x86-64": "1d03a3bd5091728492d92f0ef341aca7d8885ece9a150119558f3e3d62b58745",
                "aarch64": "90a07c1c693ac9333a8a6ec79432f0d13c0564fec6617b0222d43f86858f65b8",
            },
        )

        result = backport(git_layer_sha256, input)

        assert result.success is True
        assert result.old_version == "21.0.10.9.1"
        assert result.new_version == "21.0.11.10.1"

        # Verify file was renamed
        new_file = (
            git_layer_sha256
            / "recipes-devtools"
            / "amazon-corretto"
            / "corretto-21-bin_21.0.11.10.1.bb"
        )
        assert new_file.exists()

        # Verify sha256sums were updated
        content = new_file.read_text()
        assert "1d03a3bd5091728492d92f0ef341aca7d8885ece9a150119558f3e3d62b58745" in content
        assert "90a07c1c693ac9333a8a6ec79432f0d13c0564fec6617b0222d43f86858f65b8" in content
        assert "aaaa1111" not in content
        assert "bbbb2222" not in content

    def test_recipe_not_found(self, git_layer):
        input = BackportInput(
            recipe="nonexistent-recipe",
            version="1.0.0",
            target_branch="wrynose-next",
            srcrev="abc123",
        )

        result = backport(git_layer, input)

        assert result.success is False
        assert "not found" in result.message.lower()

    def test_already_at_version(self, git_layer):
        input = BackportInput(
            recipe="python3-botocore",
            version="1.43.19",
            target_branch="wrynose-next",
            srcrev="abc123",
        )

        result = backport(git_layer, input)

        assert result.success is False
        assert "already at version" in result.message.lower()


class TestParseUpgradeCommit:
    def test_parses_srcrev_commit(self, git_layer):
        # Create a commit that looks like an upgrade
        recipes_dir = git_layer / "recipes-devtools" / "python"
        old_file = recipes_dir / "python3-botocore_1.43.19.bb"
        new_file = recipes_dir / "python3-botocore_1.43.20.bb"

        content = old_file.read_text().replace(
            "oldoldoldoldoldoldoldoldoldoldoldoldold0",
            "aabbccddaabbccddaabbccddaabbccddaabbccdd",
        )
        new_file.write_text(content)
        old_file.unlink()

        subprocess.run(["git", "add", "--all"], cwd=git_layer, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "python3-botocore: upgrade 1.43.19 -> 1.43.20"],
            cwd=git_layer,
            capture_output=True,
            check=True,
        )

        result = parse_upgrade_commit(git_layer, "HEAD")

        assert result is not None
        assert result["recipe"] == "python3-botocore"
        assert result["version"] == "1.43.20"
        assert result["old_version"] == "1.43.19"
        assert result["srcrev"] == "aabbccddaabbccddaabbccddaabbccddaabbccdd"
