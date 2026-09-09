"""Tests for recipe identification and upgrade decision logic.

These cover the cases that caused a 217 pull request backlog in meta-aws:
same-version regeneration on every scheduled run, and the guards that keep
hand-authored and multi-recipe pull requests out of the automation's way.
"""

import pytest

from upgrader.recipes import (
    CREATE,
    SKIP_BEHIND,
    SKIP_DUPLICATE,
    SUPERSEDE,
    decide,
    recipe_and_version,
    version_key,
)


class TestVersionKey:
    def test_numeric_components_compare_numerically(self) -> None:
        # String comparison would place 1.43.9 above 1.43.10.
        assert version_key("1.43.9") < version_key("1.43.10")

    def test_equal_versions_have_equal_keys(self) -> None:
        assert version_key("1.20.0") == version_key("1.20.0")

    def test_major_bump(self) -> None:
        assert version_key("0.10.5") < version_key("1.0.0")

    @pytest.mark.parametrize(
        "lower,higher",
        [
            ("1.46.0", "1.46.1"),
            ("2.36.23", "2.36.39"),
            ("1.11.886", "1.11.887"),
            ("3.3.5068.0", "3.3.5226.0"),
            ("11.0.32.10.1", "11.0.33.1.1"),
            ("5.8.0", "5.10.0"),
        ],
    )
    def test_real_meta_aws_versions(self, lower: str, higher: str) -> None:
        assert version_key(lower) < version_key(higher)

    def test_versions_without_digits_are_all_equal(self) -> None:
        # _git.bb recipes have no comparable version; callers fall back to
        # recency for these.
        assert version_key("git") == version_key("git")
        assert not version_key("git") < version_key("git")

    def test_digitless_sorts_below_numbered(self) -> None:
        assert version_key("git") < version_key("1.0.0")


class TestRecipeAndVersion:
    def test_single_modified_recipe(self) -> None:
        files = [("recipes-support/aws-cli/aws-cli_1.46.1.bb", "modified")]
        assert recipe_and_version(files) == ("aws-cli", "1.46.1")

    def test_upgrade_rename_prefers_added_version(self) -> None:
        # devtool upgrade renames the recipe; the added file is the new version.
        files = [
            ("recipes-sdk/aws-c-mqtt/aws-c-mqtt_1.0.0.bb", "added"),
            ("recipes-sdk/aws-c-mqtt/aws-c-mqtt_0.16.2.bb", "removed"),
        ]
        assert recipe_and_version(files) == ("aws-c-mqtt", "1.0.0")

    def test_renamed_status(self) -> None:
        files = [("recipes-support/aws-cli/aws-cli_1.46.1.bb", "renamed")]
        assert recipe_and_version(files) == ("aws-cli", "1.46.1")

    def test_git_versioned_recipe(self) -> None:
        files = [
            (
                "recipes-iot/aws-iot-securetunneling-localproxy/"
                "aws-iot-securetunneling-localproxy_git.bb",
                "modified",
            )
        ]
        assert recipe_and_version(files) == (
            "aws-iot-securetunneling-localproxy",
            "git",
        )

    def test_recipe_with_hyphens_and_digits(self) -> None:
        files = [("recipes-devtools/amazon-corretto/corretto-11-bin_11.0.32.10.1.bb", "added")]
        assert recipe_and_version(files) == ("corretto-11-bin", "11.0.32.10.1")

    def test_ignores_non_recipe_files(self) -> None:
        files = [
            ("recipes-sdk/s2n/s2n_1.7.9.bb", "modified"),
            ("recipes-sdk/s2n/s2n/run-ptest", "modified"),
            ("README.md", "modified"),
        ]
        assert recipe_and_version(files) == ("s2n", "1.7.9")

    def test_bbappend(self) -> None:
        files = [
            (
                "dynamic-layers/virtualization-layer/recipes-extended/"
                "cloud-init/cloud-init_1.2.3.bbappend",
                "modified",
            )
        ]
        assert recipe_and_version(files) == ("cloud-init", "1.2.3")

    def test_multiple_recipes_is_not_identifiable(self) -> None:
        # A release fast-forward merge touches many recipes. It must never be
        # mistaken for an upgrade, matched against, or closed.
        files = [
            ("recipes-sdk/aws-c-io/aws-c-io_1.0.0.bb", "modified"),
            ("recipes-sdk/aws-c-mqtt/aws-c-mqtt_1.0.0.bb", "modified"),
        ]
        assert recipe_and_version(files) is None

    def test_no_recipe_files_is_not_identifiable(self) -> None:
        # Hand-authored hygiene changes, e.g. meta-aws#16872.
        files = [("conf/layer.conf", "modified"), ("README.md", "modified")]
        assert recipe_and_version(files) is None

    def test_empty(self) -> None:
        assert recipe_and_version([]) is None

    def test_removal_only_still_identifiable(self) -> None:
        files = [("recipes-sdk/s2n/s2n_1.7.8.bb", "removed")]
        assert recipe_and_version(files) == ("s2n", "1.7.8")


class TestDecide:
    def test_no_existing_pull_request_creates(self) -> None:
        assert decide("1.0.0", None) == CREATE

    def test_same_version_is_a_duplicate(self) -> None:
        # The regression this change exists to prevent: aws-iot-fleetwise-edge
        # accumulated 18 open pull requests all targeting 1.3.5.
        assert decide("1.3.5", "1.3.5") == SKIP_DUPLICATE

    def test_higher_version_supersedes(self) -> None:
        assert decide("1.43.90", "1.43.89") == SUPERSEDE

    def test_lower_version_does_not_regress(self) -> None:
        assert decide("1.43.88", "1.43.89") == SKIP_BEHIND

    def test_numeric_comparison_not_lexical(self) -> None:
        assert decide("1.43.10", "1.43.9") == SUPERSEDE

    def test_git_versions_are_always_duplicates(self) -> None:
        # Two _git.bb upgrades compare equal, so the second is a duplicate
        # rather than a supersession.
        assert decide("git", "git") == SKIP_DUPLICATE

    @pytest.mark.parametrize(
        "candidate,existing,expected",
        [
            ("1.0.0", "0.10.5", SUPERSEDE),
            ("0.10.5", "1.0.0", SKIP_BEHIND),
            ("1.20.0", "1.20.0", SKIP_DUPLICATE),
            ("2.36.39", "2.36.37", SUPERSEDE),
            ("1.46.0", "1.46.1", SKIP_BEHIND),
        ],
    )
    def test_matrix(self, candidate: str, existing: str, expected: str) -> None:
        assert decide(candidate, existing) == expected
