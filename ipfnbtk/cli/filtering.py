#  Copyright 2020 Jeremy Schulman
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

"""
This file contains the filtering functions that are using to process the '--include' and '--exclude' command line
options.  The code in this module is not specific to the netcfgbu inventory column names, can could be re-used for other
CSV related tools and use-cases.
"""

from typing import List, AnyStr, Optional, Callable, Dict, Sequence
import re
import operator


__all__ = ["create_filter"]


value_pattern = r"(?P<value>\S+)$"
wordsep_re = re.compile(r"\s+|,")


def mk_op_filter(_reg, _fieldn):
    """ create a single op filter """

    def op_filter(rec):
        """ using the regular expression match call """
        return _reg.match(rec[_fieldn])

    op_filter.__doc__ = f"limit_{_fieldn}({_reg.pattern})"
    op_filter.__name__ = op_filter.__doc__
    op_filter.__qualname__ = op_filter.__doc__

    return op_filter


def create_filter_function(op_filters, optest_fn):
    """ create a filtering functions based on the operational test """

    def filter_fn(rec):
        """ for each of the filters """
        for op_fn in op_filters:
            if optest_fn(op_fn(rec)):
                return False

        return True

    return filter_fn


def create_filter(
    constraints: List[AnyStr],
    field_names: Sequence[AnyStr],
    include: Optional[bool] = True,
) -> Callable[[Dict], bool]:
    """
    This function returns a function that is used to filter inventory records.

    Parameters
    ----------
    constraints:
        A list of contraint expressions that are in the form "<field-name>=<value>".

    field_names:
        A list of known field names

    include:
        When True, the filter function will match when the constraint is true,
        for example if the contraint is "os_name=eos", then it would match
        records that have os_name field euqal to "eos".

        When False, the filter function will match when the constraint is not
        true. For exampl if the constraint is "os_name=eos", then the filter
        function would match recoreds that have os_name fields not equal to
        "eos".

    Returns
    -------
    The returning filter function expects an inventory record as the single
    input parameter, and the function returns True/False on match.
    """
    fieldn_pattern = "^(?P<keyword>" + "|".join(fieldn for fieldn in field_names) + ")"
    field_value_reg = re.compile(fieldn_pattern + "=" + value_pattern)

    op_filters = list()
    for filter_expr in constraints:

        # next check for keyword=value filtering use-case

        if (mo := field_value_reg.match(filter_expr)) is None:
            raise ValueError(f"Invalid filter expression: {filter_expr}")

        fieldn, value = mo.groupdict().values()

        try:
            value_reg = re.compile(f"^{value}$", re.IGNORECASE)

        except re.error as exc:
            raise ValueError(
                f"Invalid filter regular-expression: {filter_expr}: {str(exc)}"
            )

        op_filters.append(mk_op_filter(value_reg, fieldn))

    optest_fn = operator.not_ if include else operator.truth
    filter_fn = create_filter_function(op_filters, optest_fn)
    filter_fn.op_filters = op_filters
    filter_fn.constraints = constraints

    return filter_fn
