from typing import Any, Callable, Optional, Union

from ..base import BaseComponent
from ..base.schema import Document, IO_Type
from .chats import ChatLLM
from .completions import LLM
from .prompts import BasePromptComponent


class SimpleLinearPipeline(BaseComponent):
    """
    A simple pipeline for running a function with a prompt, a language model, and an
        optional post-processor.
    """

    prompt: BasePromptComponent
    llm: Union[ChatLLM, LLM]
    post_processor: Union[BaseComponent, Callable[[IO_Type], IO_Type]]

    def run(
        self,
        *,
        llm_kwargs: Optional[dict] = {},
        post_processor_kwargs: Optional[dict] = {},
        **prompt_kwargs,
    ):
        """
        Run the function with the given arguments and return the final output as a
            Document object.

        Args:
            llm_kwargs (dict): Keyword arguments for the llm call.
            post_processor_kwargs (dict): Keyword arguments for the post_processor.
            **prompt_kwargs: Keyword arguments for populating the prompt.

        Returns:
            Document: The final output of the function as a Document object.
        """
        prompt = self.prompt(**prompt_kwargs)
        llm_output = self.llm(prompt.text, **llm_kwargs)
        if self.post_processor is not None:
            final_output = self.post_processor(llm_output, **post_processor_kwargs)[0]
        else:
            final_output = llm_output

        return Document(final_output)


class GatedLinearPipeline(SimpleLinearPipeline):
    """
    A pipeline that extends the SimpleLinearPipeline class and adds a condition
        attribute.

    Attributes:
        condition (Callable[[IO_Type], Any]): A callable function that represents the
            condition.

    """

    condition: Callable[[IO_Type], Any]

    def run(
        self,
        *,
        condition_text: Optional[str] = None,
        llm_kwargs: Optional[dict] = {},
        post_processor_kwargs: Optional[dict] = {},
        **prompt_kwargs,
    ) -> Document:
        """
        Run the pipeline with the given arguments and return the final output as a
            Document object.

        Args:
            condition_text (str): The condition text to evaluate. Default to None.
            llm_kwargs (dict): Additional keyword arguments for the language model call.
            post_processor_kwargs (dict): Additional keyword arguments for the
                post-processor.
            **prompt_kwargs: Keyword arguments for populating the prompt.

        Returns:
            Document: The final output of the pipeline as a Document object.

        Raises:
            ValueError: If condition_text is None
        """
        if condition_text is None:
            raise ValueError("`condition_text` must be provided")

        if self.condition(condition_text)[0]:
            return super().run(
                llm_kwargs=llm_kwargs,
                post_processor_kwargs=post_processor_kwargs,
                **prompt_kwargs,
            )

        return Document(None)
