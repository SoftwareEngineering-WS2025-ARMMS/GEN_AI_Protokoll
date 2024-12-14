import json

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageToolCall
from openai.types.chat.chat_completion_message_tool_call import Function

from backend.utils.FunctionTool import FunctionTool

class OpenAIClient:

    __key_path__ = '.venv/CHATGPT_API'

    def __init__(self, key):
        self.client = OpenAI(api_key=key)
        self.messages = list()

    @classmethod
    def new_client(cls) -> 'OpenAIClient':
        with open(cls.__key_path__, 'r') as file:
            key = file.readline()
        return cls(key)

    def prompt(self, user_prompt: str, system_prompt: str | None = None, tools: list[FunctionTool] | None = None) -> dict:
        """
        Sends a message to a ChatGPT conversation and returns the response.
        :param user_prompt: The prompt to ask ChatGPT client.
        :param system_prompt: The prompt to make the user prompt structured in a specific way.
        :param tools: A list of function tools that can be given to the client to make it able to answer
        :return: A dictionary {'content': message, 'tools': returned_tools} with message being the resulting message of the prompt,
        and returned_tools being the tools that the prompt used with their corresponding arguments as a list of dictionaries
        {'tool': tool, 'args': args} with tool being the FunctionTool used, and args a dictionary {arg_name: arg_value}
        """

        if system_prompt is not None:
            self.messages.append(
                {
                    "role": "system",
                    "content": system_prompt,
                }
            )

        self.messages.append(
            {
                "role": "user",
                "content": user_prompt,
            }
        )

        if tools is not None:
            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=self.messages,
                tools=[tool.metadata for tool in tools],
            )
        else:
            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=self.messages
            )
        output = completion.choices[0].message
        self.messages.append(output)
        content = output.content
        tool_calls = output.tool_calls

        returned_tools = []
        for call in tool_calls:
            call_type, function = call.type, call.function
            assert call_type == 'function', "Only function tools are supported for the moment."
            name, args = function.name, function.arguments
            tool = list(filter(lambda tool: tool.metadata['function']['name'] == name, tools))
            assert len(tool) == 1, ("Either the returned tool does not correspond to one of the given tools or"
                                    " tools has two FunctionTools with the same name")
            returned_tools.append({'tool': tool[0], 'args': json.loads(args)})

        return {'content': content, 'tools': returned_tools}