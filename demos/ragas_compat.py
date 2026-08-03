"""
Workaround for a ragas 0.4.3 / langchain_community packaging mismatch.

ragas.llms.base unconditionally imports langchain_community.chat_models.vertexai
at module load time, even though we never use Google Vertex AI. Recent
langchain_community releases removed that submodule (Vertex support moved to
a separate langchain-google-vertexai package), so the bare `import ragas`
crashes before we get a chance to do anything.

This file must be imported BEFORE any `import ragas` statement. It registers
a fake module in sys.modules so Python's import system is satisfied without
ever needing the real (missing) file.
"""

import sys
import types

_FAKE_MODULE_NAME = "langchain_community.chat_models.vertexai"

if _FAKE_MODULE_NAME not in sys.modules:
    fake_vertexai_module = types.ModuleType(_FAKE_MODULE_NAME)

    class ChatVertexAI:
        def __init__(self, *args, **kwargs):
            raise RuntimeError(
                "ChatVertexAI is a compatibility stub (see demos/ragas_compat.py). "
                "This project does not use Google Vertex AI."
            )

    fake_vertexai_module.ChatVertexAI = ChatVertexAI
    sys.modules[_FAKE_MODULE_NAME] = fake_vertexai_module