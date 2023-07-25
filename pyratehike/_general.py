"""private module defining the _Dispatcher class and the _check_inputs
function.
"""

from typing import Dict, Generic, List, TypeVar

T = TypeVar("T")


class _Dispatcher(Generic[T]):
    """class for dispatching functionality of generic class "T"."""

    __slots__ = ("_methods",)
    _methods: Dict[str, T]

    def __init__(self, default: T) -> None:
        """The constructor initializes the default value.

        Parameters
        ----------
        default : "T"
            the base class, the default return value when dispatching

        Returns
        -------
        None
        """

        self._methods = {"default": default}

    def set_method(self, signature: str, method: T) -> None:
        """Add a method to the list.

        Parameters
        ----------
        signature : str
            the reference for dispatching
        method : "T"
            the class to return for a given signature

        Returns
        -------
        None
        """

        self._methods[signature] = method

    def dispatch(self, signature: str = "default") -> T:
        """Choose a method from the list

        Parameters
        ----------
        signature : str
            the reference for dispatching

        Returns
        -------
        "T"
            the requested class
        """

        return self._methods[signature]


def _check_inputs(parameter: str, options: List[str], value: str) -> None:
    """helper method to check inputs

    if the value is not in the list of options, a ValueError is thrown.

    parameters
    ----------
    parameter : str
        name of the parameter that is checked
    options : list of str
        a list of allowed options
    value : str
        the value passed as input

    returns
    -------
    None
    """

    if value not in options:
        lastoption: str = options.pop()
        str_options: str = ", ".join(options) + " or " + lastoption
        raise ValueError(
            f"Input Error: {parameter} should be {str_options}, got {value}."
        )
