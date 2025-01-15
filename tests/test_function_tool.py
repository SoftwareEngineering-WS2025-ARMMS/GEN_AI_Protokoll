from typing import Callable
import pytest

from src.utils import FunctionTool


@pytest.fixture
def give_function() -> Callable:
    def calculate_area(length: float, width: float = 0.) -> float:
        """
        Calculate the area of a rectangle.

        :param length: The length of the rectangle (must be a positive float).
        :param width: The width of the rectangle (must be a positive float).
        :return: The area of the rectangle as a float.
        """
        if length <= 0 or width <= 0:
            raise ValueError("Length and width must be positive numbers.")
        return length * width

    return calculate_area


def test_metadata(give_function: Callable) -> None:
    tool = FunctionTool(give_function)
    assert tool.metadata == {
        "type": "function",
        "function": {
            "name": "calculate_area",
            "description": "Calculate the area of a rectangle.\n"
                           "The function returns: The area of the rectangle "
                           "as a float.",
            "parameters": {
                "type": "object",
                "properties": {
                    "length": {
                        "type": "number",
                        "description": "The length of the rectangle (must be a positive float).",
                    },
                    "width": {
                        "type": "number",
                        "description": "The width of the rectangle (must be a positive float)."
                    }
                },
                "required": ["length"]
            }
        }
    }


def test_callable(give_function: Callable) -> None:
    tool = FunctionTool(give_function)
    assert abs(tool(1.5, 2.1) - 3.15) < 1e-5


def test_function(give_function: Callable) -> None:
    tool = FunctionTool(give_function)
    assert tool.function == give_function


def test_metadata_added(give_function: Callable) -> None:
    tool = FunctionTool(give_function, metadata={"type": "function"})
    assert tool.metadata == {
        "type": "function",
    }