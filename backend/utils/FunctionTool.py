import inspect
import json
from typing import get_origin, get_args

class FunctionTool:
    """
    A wrapper of a function and its description for a ChatGPT-understandable tool.
    A FunctionTool object is callable and calls function it wraps.
    It also has the metadata member containing the description of the function as defined in its documentation. \n
    Example:
    >>> def fun(x: int) -> int:
    ...   '''Adds 1 to x
    ...   :param x: An integer
    ...   :return: an incremented x
    ...   '''
    ...   return x + 1
    >>> fun_tool = FunctionTool(fun)
    >>> fun_tool(5)
    6
    >>> fun_tool.metadata['function']['parameters']['properties']['x']['description']
    'An integer'
    """

    @staticmethod
    def _get_type_name(annotation):
        if annotation == inspect.Parameter.empty:
            return "string"
        if getattr(annotation, '__name__', None):
            return annotation.__name__.lower()
        if get_origin(annotation) is type(None):
            return "null"
        if get_origin(annotation) is not None:  # Handle Union types
            types = [FunctionTool._get_type_name(arg) for arg in get_args(annotation)]
            return " | ".join(set(types))
        return str(annotation).lower()

    @staticmethod
    def _extract_section(lines, start_tag):
        section = []
        capturing = False
        for line in lines:
            if start_tag and line.strip().lower().startswith(start_tag.lower()):
                capturing = True
                section.append(line.split(start_tag, 1)[1].strip())
            elif not start_tag and not line.strip().startswith(':') and line.strip():
                capturing = True
                section.append(line.strip())
            elif capturing and line.strip():
                if line.strip().startswith(':') or line.strip().lower() == 'examples:':
                    break
                section.append(line.strip())
        return "\n".join(section)

    @staticmethod
    def __metadata__(func: callable) -> dict:
        """
        Creates the function metadata as a tool usable by OpenAI prompts using the docstring of the given function.
        :param func: The function, which in the best case has a description of its functionality, parameters and return
        :return: A dictionary with the metadata which OpenAI prompts understand as a JSON object
        """

        signature = inspect.signature(func)

        func_name = func.__name__

        if inspect.isclass(func):
            func = func.__init__

        docstring = inspect.getdoc(func) or "No description available"
        lines = docstring.splitlines()
        description = FunctionTool._extract_section(lines, "")
        returning = FunctionTool._extract_section(lines, ":return:")
        description = description + '\nThe function returns: ' + returning

        parameters = {
            "type": "object",
            "properties": {},
            "required": [],
            "optional": {}
        }

        examples = FunctionTool._extract_section(lines, "Examples:")

        type_mapping = {
            "str": "string",
            "int": "integer",
            "float": "number",
            "bool": "boolean",
            "list": "array",
            "dict": "object"
        }

        self = inspect.ismethod(func)

        for name, param in signature.parameters.items():
            if self:
                self = False
                continue

            param_type = FunctionTool._get_type_name(param.annotation)
            param_type = type_mapping.get(param_type, param_type)


            param_description = FunctionTool._extract_section(lines, f":param {name}:") or "No description available"
            explicit_type = FunctionTool._extract_section(lines, f":type {name}:")
            if explicit_type:
                param_type = type_mapping.get(explicit_type.lower(), param_type)

            param_entry = {
                "type": param_type,
                "description": param_description
            }

            if param.default == inspect.Parameter.empty:
                parameters["required"].append(name)
            else:
                parameters["optional"][name] = {
                    "default": param.default,
                    **param_entry
                }

            parameters["properties"][name] = param_entry

        schema = {
            "type": "function",
            "function": {
                "name": func_name,
                "description": description,
                "parameters": parameters
            }
        }

        if examples:
            schema["function"]["examples"] = examples

        return schema


    def __init__(self: "FunctionTool", function: callable, metadata: dict| None = None) -> None:
        """
        Creates a new function tool that can be used by OpenAI prompts. If metadata is not specified, the constructor
        creates the function using its documentation string.
        Example of use:
            metadata = {
                "type": "function",
                "function": {
                    "name": "get_n_day_weather_forecast",
                    "description": "Get an N-day weather forecast",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city and state, e.g. San Francisco, CA",
                            },
                            "format": {
                                "type": "string",
                                "enum": ["celsius", "fahrenheit"],
                                "description": "The temperature unit to use. Infer this from the users location.",
                            },
                            "num_days": {
                                "type": "integer",
                                "description": "The number of days to forecast",
                            }
                        },
                        "required": ["location", "format", "num_days"]
                    },
                }
            }
            FunctionTool(get_n_day_weather_forecast, metadata)
        :param self: The function tool object to create.
        :param function: The function whose parameters can be determined by OpenAI.
        :param metadata: The metadata of the function, including its description and its parameters.
        """
        self.function = function
        if metadata is None:
            self.metadata = FunctionTool.__metadata__(function)
        else:
            self.metadata = metadata

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)


if __name__ == "__main__":
    f = FunctionTool(FunctionTool.__metadata__)
    g = f(FunctionTool)
    print(json.dumps(g, indent=4))