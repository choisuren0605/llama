from copy import deepcopy
from typing import Callable, List

from theflow import Function, Node, Param

from kotaemon.base import BaseComponent, Document

from .chats import LCAzureChatOpenAI
from .completions import LLM
from .prompts import BasePromptComponent


class Thought(BaseComponent):
    prompt: str = Param(
        help=(
            "The prompt template string. This prompt template has Python-like variable"
            " placeholders, that then will be substituted with real values when this"
            " component is executed"
        )
    )
    llm: LLM = Node(LCAzureChatOpenAI, help="The LLM model to execute the input prompt")
    post_process: Function = Node(
        help=(
            "The function post-processor that post-processes LLM output prediction ."
            "It should take a string as input (this is the LLM output text) and return "
            "a dictionary, where the key should"
        )
    )

    @Node.auto(depends_on="prompt")
    def prompt_template(self):
        """Automatically wrap around param prompt. Can ignore"""
        return BasePromptComponent(template=self.prompt)

    def run(self, **kwargs) -> Document:
        """Run the chain of thought"""
        prompt = self.prompt_template(**kwargs).text
        response = self.llm(prompt).text
        response = self.post_process(response)

        return Document(response)

    def get_variables(self) -> List[str]:
        return []

    def __add__(self, next_thought: "Thought") -> "ManualSequentialChainOfThought":
        return ManualSequentialChainOfThought(
            thoughts=[self, next_thought], llm=self.llm
        )


class ManualSequentialChainOfThought(BaseComponent):

    thoughts: List[Thought] = Param(
        default_callback=lambda *_: [], help="List of Thought"
    )
    llm: LLM = Param(help="The LLM model to use (base of kotaemon.llms.BaseLLM)")
    terminate: Callable = Param(
        default=lambda _: False,
        help="Callback on terminate condition. Default to always return False",
    )

    def run(self, **kwargs) -> Document:
        """Run the manual chain of thought"""

        inputs = deepcopy(kwargs)
        for idx, thought in enumerate(self.thoughts):
            if self.llm:
                thought.llm = self.llm
            self._prepare_child(thought, f"thought{idx}")

            output = thought(**inputs)
            inputs.update(output.content)
            if self.terminate(inputs):
                break

        return Document(inputs)

    def __add__(self, next_thought: Thought) -> "ManualSequentialChainOfThought":
        return ManualSequentialChainOfThought(
            thoughts=self.thoughts + [next_thought], llm=self.llm
        )
