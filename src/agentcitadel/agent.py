"""The agency loop."""

from typing import Any, Literal
from uuid import uuid4

from agentcitadel.guard.pipeline import GuardPipeline, resolve
from agentcitadel.guard.policy.engine import evaluate
from agentcitadel.guard.policy.schema import Action, Policy
from agentcitadel.observe.recorder import Recorder
from agentcitadel.protocols import Approver, LLMProvider
from agentcitadel.tools.registry import ToolRegistry
from agentcitadel.types import Message, Span, ToolCall, Verdict


class CitadelAgent:
    """Runs a guarded agent loop and records every step."""

    def __init__(
        self,
        provider: LLMProvider,
        tools: ToolRegistry,
        recorder: Recorder,
        policy: Policy,
        approver: Approver,
        input_guard: GuardPipeline,
        output_guard: GuardPipeline,
        system: str = "",
        max_turns: int = 10,
    ) -> None:
        self.provider = provider
        self.tools = tools
        self.recorder = recorder
        self.policy = policy
        self.approver = approver
        self.input_guard = input_guard
        self.output_guard = output_guard
        self.system = system
        self.max_turns = max_turns

    async def _span(
        self,
        run_id: str,
        kind: Literal["llm", "tool", "guard", "policy"],
        name: str,
        input: dict[str, Any],
        output: dict[str, Any],
    ) -> None:
        """Record one step."""
        await self.recorder.record(
            Span(run_id=run_id, kind=kind, name=name, input=input, output=output)
        )

    async def run(self, prompt: str) -> Message:
        """Guard the input, loop until the model stops calling tools, guard the output."""
        run_id = str(uuid4())

        results = await self.input_guard.run(prompt, {"position": "input"})
        await self._span(
            run_id,
            "guard",
            "input",
            {"content": prompt},
            {"results": [r.model_dump(mode="json") for r in results]},
        )
        if resolve(results) is Verdict.BLOCK:
            reason = next(r.reason for r in results if r.verdict is Verdict.BLOCK)
            return Message(role="assistant", content=f"blocked: {reason}")

        messages = [Message(role="user", content=prompt)]
        if self.system:
            messages.insert(0, Message(role="system", content=self.system))

        for _ in range(self.max_turns):
            reply = await self.provider.complete(messages, self.tools.schemas())
            await self._span(
                run_id,
                "llm",
                self.provider.model,
                {"messages": len(messages)},
                {"content": reply.content, "tool_calls": len(reply.tool_calls)},
            )
            messages.append(reply)

            if not reply.tool_calls:
                break

            for call in reply.tool_calls:
                result = await self._handle_call(run_id, call)
                messages.append(
                    Message(role="tool", content=result, tool_call_id=call.id)
                )
        # Runs only if the loop finished without a break (in this case no more tool calls, model is done)
        else:
            return Message(role="assistant", content="stopped: max turns reached")

        final = messages[-1]
        results = await self.output_guard.run(final.content, {"position": "output"})
        await self._span(
            run_id,
            "guard",
            "output",
            {"content": final.content},
            {"results": [r.model_dump(mode="json") for r in results]},
        )
        if resolve(results) is Verdict.BLOCK:
            reason = next(r.reason for r in results if r.verdict is Verdict.BLOCK)
            return Message(role="assistant", content=f"blocked: {reason}")
        return final

    async def _handle_call(self, run_id: str, call: ToolCall) -> str:
        """
        Authorize a tool call, then run it if permitted.

        No model can be called from the registry until it first passed
        through this method.
        """
        action, reason = evaluate(self.policy, call.name)

        if action is Action.ASK:
            approved = await self.approver.request(call, reason)
            action = Action.ALLOW if approved else action.DENY
            reason = f"{reason} (human {'approved' if approved else 'denied'})"

        await self._span(
            run_id,
            "policy",
            call.name,
            {"arguments": call.arguments},
            {"action": action.value, "reason": reason},
        )

        if action is Action.DENY:
            return f"denied: {reason}"

        result = await self.tools.run(call)
        await self._span(
            run_id,
            "tool",
            call.name,
            {"arguments": call.arguments},
            result.model_dump(mode="json"),
        )

        return result.content
