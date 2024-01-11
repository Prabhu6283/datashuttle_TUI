import re

import pytest

from datashuttle.configs.canonical_tags import tags
from datashuttle.utils import formatting, utils
from datashuttle.utils.custom_exceptions import NeuroBlueprintError


class TestUnit:
    """
    Currently contains misc. unit tests.
    """

    @pytest.mark.parametrize(
        "underscore_position", ["left", "right", "both", "none"]
    )
    @pytest.mark.parametrize(
        "key", [tags("date"), tags("time"), tags("datetime")]
    )
    def test_datetime_string_replacement(self, key, underscore_position):
        """
        Test the function that replaces @DATE, @TIME@ or @DATETIME@
        keywords with the date / time / datetime. Also, it will
        pre/append underscores to the tags if they are not
        already there (e.g if user input "sub-001@DATE").
        Note cannot use regex \d{8} format because we are in an
        f-string.
        """
        start = "sub-001"
        end = "other-tag"
        name = self.make_name(key, underscore_position, start, end)

        if key == tags("date"):
            regex = re.compile(rf"{start}_date-\d\d\d\d\d\d\d\d_{end}")
        elif key == tags("time"):
            regex = re.compile(rf"{start}_time-\d\d\d\d\d\d_{end}")
        elif key == tags("datetime"):
            regex = re.compile(
                rf"{start}_datetime-\d\d\d\d\d\d\d\dT\d\d\d\d\d\d_{end}"
            )

        name_list = [name]
        formatting.update_names_with_datetime(name_list)

        assert (
            re.search(regex, name_list[0]) is not None
        ), "datetime formatting is incorrect."

    @pytest.mark.parametrize(
        "prefix_and_names",
        [
            ["sub", "sub 001"],
            ["sub", ["sub 001"]],
            ["ses", ["ses- 001", "ses-002"]],
        ],
    )
    def test_spaces_in_format_names(self, prefix_and_names):
        prefix, names = prefix_and_names
        with pytest.raises(NeuroBlueprintError) as e:
            formatting.check_and_format_names(names, prefix)

        assert str(e.value) == f"{prefix} names cannot include spaces."

    @pytest.mark.parametrize("prefix", ["sub", "ses"])
    def test_process_to_keyword_in_sub_input(self, prefix):
        """ """
        results = formatting.update_names_with_range_to_flag(
            [f"{prefix}-001", f"{prefix}-01{tags('to')}123"], prefix
        )
        assert results == [f"{prefix}-001"] + [
            f"{prefix}-{str(num).zfill(2)}" for num in range(1, 124)
        ]

        results = formatting.update_names_with_range_to_flag(
            [f"{prefix}-1{tags('to')}3_hello-world"], prefix
        )
        assert results == [
            f"{prefix}-1_hello-world",
            f"{prefix}-2_hello-world",
            f"{prefix}-3_hello-world",
        ]

        results = formatting.update_names_with_range_to_flag(
            [
                f"{prefix}-01{tags('to')}3_hello",
                f"{prefix}-4{tags('to')}005_goodbye",
                f"{prefix}-006{tags('to')}0007_hello",
            ],
            prefix,
        )

        assert results == [
            f"{prefix}-01_hello",
            f"{prefix}-02_hello",
            f"{prefix}-03_hello",
            f"{prefix}-004_goodbye",
            f"{prefix}-005_goodbye",
            f"{prefix}-0006_hello",
            f"{prefix}-0007_hello",
        ]

    @pytest.mark.parametrize("prefix", ["sub", "ses"])
    @pytest.mark.parametrize(
        "bad_input",
        [
            f"1{tags('to')}2",
            f"prefix-1{tags('to')}_date",
            f"prefix-@01{tags('to')}02",
            f"prefix-01{tags('to')}1M1",
        ],
    )
    def test_process_to_keyword_bad_input_raises_error(
        self, prefix, bad_input
    ):
        bad_input = bad_input.replace("prefix", prefix)

        with pytest.raises(ValueError) as e:
            formatting.update_names_with_range_to_flag([bad_input], prefix)

        assert (
            str(e.value)
            == f"The name: {bad_input} is not in required format for {tags('to')} keyword. "
            f"The start must be  be {prefix}-<NUMBER>{tags('to')}<NUMBER>)."
        )

    def test_formatting_check_dashes_and_underscore_alternate_correctly(self):
        """"""
        all_names = ["sub_001_date-010101"]
        with pytest.raises(NeuroBlueprintError) as e:
            formatting.check_dashes_and_underscore_alternate_correctly(
                all_names
            )

        assert (
            str(e.value)
            == "The first delimiter of 'sub' or 'ses' must be dash not underscore e.g. sub-001."
        )

        alternate_error = (
            "Subject and session names must contain alternating dashes"
            " and underscores (used for separating key-value pairs)."
        )

        all_names = ["sub-001-date_101010"]
        with pytest.raises(NeuroBlueprintError) as e:
            formatting.check_dashes_and_underscore_alternate_correctly(
                all_names
            )

        assert str(e.value) == alternate_error

        all_names = ["sub-001_ses-002-suffix"]
        with pytest.raises(NeuroBlueprintError) as e:
            formatting.check_dashes_and_underscore_alternate_correctly(
                all_names
            )
        assert str(e.value) == alternate_error

        all_names = ["sub-001_ses-002-task-check"]
        with pytest.raises(NeuroBlueprintError) as e:
            formatting.check_dashes_and_underscore_alternate_correctly(
                all_names
            )
        assert str(e.value) == alternate_error

        # check these don't raise
        all_names = ["ses-001_hello-world_one-hundred"]
        formatting.check_dashes_and_underscore_alternate_correctly(all_names)

        all_names = ["ses-001_hello-world_suffix"]
        formatting.check_dashes_and_underscore_alternate_correctly(all_names)

    def test_get_value_from_bids_name_regexp(self):
        """
        Test the regexp that finds the value from a BIDS-name
        key-value pair.
        """
        bids_name = "sub-0123125_ses-11312_datetime-5345323_id-3asd@523"

        sub = utils.get_value_from_key_regexp(bids_name, "sub")[0]
        assert sub == "0123125"

        ses = utils.get_value_from_key_regexp(bids_name, "ses")[0]
        assert ses == "11312"

        datetime = utils.get_value_from_key_regexp(bids_name, "datetime")[0]
        assert datetime == "5345323"

        id = utils.get_value_from_key_regexp(bids_name, "id")[0]
        assert id == "3asd@523"

    def test_num_leading_zeros(self):
        """
        Check num_leading_zeros handles prefixed and non-prefixed
        case from -1 to -(101x 0)1.
        """
        for i in range(101):
            assert formatting.num_leading_zeros("1".zfill(i + 1)) == i
            assert formatting.num_leading_zeros("sub-" + "1".zfill(i + 1)) == i
            assert formatting.num_leading_zeros("ses-" + "1".zfill(i + 1)) == i

    @pytest.mark.parametrize("prefix", ["sub", "ses"])
    def test_inconsistent_leading_zeros_in_list_of_names(self, prefix):
        """
        Ensure a list of sub / ses names that contain inconsistent leading zeros
        (e.g. ["sub-001", "sub-02"]) leads to an error.
        """
        names = [f"{prefix}-001", f"{prefix}-02", f"{prefix}-003"]

        with pytest.raises(NeuroBlueprintError) as e:
            formatting.check_and_format_names(names, prefix)

        assert (
            str(e.value) == f"The length of the {prefix} values (e.g. '001') "
            f"must be consistent across all {prefix} names."
        )

    @pytest.mark.parametrize("prefix", ["sub", "ses"])
    def test_duplicate_ids_in_list_of_names(self, prefix):
        """
        Ensure a list of sub / ses names that contain duplicate sub / ses
        ids (e.g. ["sub-001", "sub-001_@DATE@"]) leads to an error.
        """
        names = [f"{prefix}-001", f"{prefix}-002", f"{prefix}-001_@DATE@"]

        with pytest.raises(NeuroBlueprintError) as e:
            formatting.check_and_format_names(names, prefix)

        assert (
            str(e.value) == f"{prefix} names must all have unique "
            f"integer ids after the {prefix} prefix."
        )

    @pytest.mark.parametrize("key", ["sub", "ses", "date", "id"])
    @pytest.mark.parametrize("return_as_int", [True, False])
    @pytest.mark.parametrize("sort", [True, False])
    def test_get_values_from_bids_formatted_name(
        self, key, return_as_int, sort
    ):
        """
        Unit test the function `get_values_from_bids_formatted_name()`
        which extracts values from BIDS-like names with a range of
        possible inputs.
        """
        if return_as_int and key == "id":
            return

        all_names = [
            "sub-01_ses-0101_date-123456_id-abcde",
            "sub-02_ses-0999_date-234567_id-bcdef",
            "sub-99_ses-1000_date-345678_id-cdefg",
        ]

        all_expected_values = {
            "sub": ["01", "02", "99"],
            "ses": ["0101", "0999", "1000"],
            "date": ["123456", "234567", "345678"],
            "id": ["abcde", "bcdef", "cdefg"],
        }

        values = utils.get_values_from_bids_formatted_name(
            all_names, key, return_as_int, sort
        )

        expected_values = all_expected_values[key]

        if return_as_int:
            expected_values = [int(val) for val in expected_values]

        if sort:
            expected_values = sorted(expected_values)

        assert values == expected_values

    def test_get_values_from_bids_formatted_name_error(self):
        """
        Check errors that catch unpredictable behaviour
        are displayed correctly.
        """
        with pytest.raises(BaseException) as e:
            utils.get_values_from_bids_formatted_name(
                ["sub-001_date-12345", "sub-001_date-12345_date-23456"], "date"
            )

        assert (
            "There is more than one instance of date in"
            " sub-001_date-12345_date-23456" in str(e.value)
        )

        with pytest.raises(BaseException) as e:
            utils.get_values_from_bids_formatted_name(
                ["sub-a_date-12345", "sub-b_date-12345_date-23456"],
                "sub",
                return_as_int=True,
            )
        assert "Invalid character in sub number: sub-a_date-12345" == str(
            e.value
        )

    # -------------------------------------------------------
    #
    #
    # ---------------
    # Utlis
    # ----------------------------------------------------------------------

    def make_name(self, key, underscore_position, start, end):
        """
        Make name with / without underscore to test every
        possibility.
        """
        if underscore_position == "left":
            name = f"{start}_{key}{end}"

        elif underscore_position == "right":
            name = f"{start}{key}_{end}"

        elif underscore_position == "both":
            name = f"{start}_{key}_{end}"

        elif underscore_position == "none":
            name = f"{start}{key}{end}"

        return name
