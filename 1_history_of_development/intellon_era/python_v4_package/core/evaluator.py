"""
Intellon v4 — Evaluator

The LLM judge + differential learning loop.

1. Generator produces an attempt
2. LLM judge scores it (stateless, temperature 0)
3. Register compares attempt vs previous attempt
4. Score went up? → reinforcement node (what changed = good)
5. Score went down? → correction node (what changed = bad)
6. Next attempt has these nodes in context

The LLM is a ruler. It measures. Intellon does the learning.
"""

from __future__ import annotations
import json
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

from .models import Node, Tier, NodeFlag, Pointer, Origin, DiffResult
from .generator import Generator

if TYPE_CHECKING:
    from .engine import Engine
    from .librarian import Librarian


# ======================================================================
# Evaluation scores
# ======================================================================

@dataclass
class EvalScore:
    accuracy: float = 0.0       # Is the information correct? (1-10)
    fluency: float = 0.0        # Does it read like natural language? (1-10)
    completeness: float = 0.0   # Does it address the prompt fully? (1-10)
    relevance: float = 0.0      # Is everything relevant? (1-10)
    note: str = ""              # Judge's explanation

    @property
    def total(self) -> float:
        return self.accuracy + self.fluency + self.completeness + self.relevance

    @property
    def average(self) -> float:
        return self.total / 4.0


@dataclass
class Attempt:
    prompt: str
    response: str
    score: EvalScore
    attempt_number: int
    timestamp: float = field(default_factory=time.time)


@dataclass
class LearningRecord:
    prompt: str
    attempts: list[Attempt] = field(default_factory=list)
    improvements: list[str] = field(default_factory=list)
    regressions: list[str] = field(default_factory=list)
    nodes_created: int = 0

    @property
    def score_trajectory(self) -> list[float]:
        return [a.score.average for a in self.attempts]

    @property
    def improved(self) -> bool:
        t = self.score_trajectory
        return len(t) >= 2 and t[-1] > t[0]


# ======================================================================
# LLM Judge
# ======================================================================

class Judge:
    """
    Stateless LLM evaluator. Each call is independent.
    Temperature 0, no conversation history.
    """

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key
        self.model = model
        self._call_count = 0

    def evaluate(self, prompt: str, response: str) -> EvalScore:
        """Score a response. Returns EvalScore."""
        import urllib.request

        eval_prompt = f"""Rate this AI system's response. Be consistent and objective.

Prompt given to the system: {prompt}
System's response: {response}

Score each dimension from 1 (terrible) to 10 (perfect):
- accuracy: Is the information factually correct?
- fluency: Does it read like natural, grammatical English?
- completeness: Does it fully address what was asked?
- relevance: Is everything in the response relevant to the prompt?

Return ONLY valid JSON, no other text:
{{"accuracy": N, "fluency": N, "completeness": N, "relevance": N, "note": "brief explanation of the biggest issue or strength"}}"""

        try:
            data = json.dumps({
                "model": self.model,
                "max_tokens": 200,
                "temperature": 0,
                "messages": [{"role": "user", "content": eval_prompt}]
            }).encode()

            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=data,
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                },
            )

            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read())

            # Extract text from response
            text = result["content"][0]["text"].strip()
            # Parse JSON (handle potential markdown wrapping)
            text = text.strip("`").strip()
            if text.startswith("json"):
                text = text[4:].strip()
            scores = json.loads(text)

            self._call_count += 1
            return EvalScore(
                accuracy=float(scores.get("accuracy", 1)),
                fluency=float(scores.get("fluency", 1)),
                completeness=float(scores.get("completeness", 1)),
                relevance=float(scores.get("relevance", 1)),
                note=scores.get("note", ""),
            )

        except Exception as e:
            return EvalScore(note=f"Judge error: {e}")

    @property
    def calls_made(self) -> int:
        return self._call_count


class MockJudge:
    """
    Offline judge for testing without an API key.
    Uses simple heuristics instead of LLM scoring.
    """

    def __init__(self):
        self._call_count = 0

    def evaluate(self, prompt: str, response: str) -> EvalScore:
        self._call_count += 1

        if not response or response == "(unknown)" or response == "(no relevant knowledge)":
            return EvalScore(accuracy=1, fluency=1, completeness=1, relevance=1,
                             note="No response produced")

        words = response.split()
        prompt_words = set(prompt.lower().split())

        # Fluency: does it have articles, verbs, punctuation?
        has_article = any(w in response.lower() for w in ["a", "an", "the"])
        has_verb = any(w in response.lower() for w in ["is", "are", "was", "has", "can"])
        has_period = response.endswith(".")
        fluency = 3 + (2 if has_article else 0) + (2 if has_verb else 0) + (1 if has_period else 0) + min(len(words) / 5, 2)

        # Relevance: how many prompt keywords appear in response?
        overlap = len(prompt_words & set(response.lower().split()))
        relevance = min(3 + overlap * 2, 10)

        # Completeness: longer = more complete (rough)
        completeness = min(2 + len(words) / 3, 10)

        # Accuracy: hard to judge without LLM, give benefit of doubt
        accuracy = 5 if len(words) > 2 else 2

        return EvalScore(
            accuracy=min(accuracy, 10),
            fluency=min(fluency, 10),
            completeness=min(completeness, 10),
            relevance=min(relevance, 10),
            note="mock judge — heuristic scoring",
        )

    @property
    def calls_made(self) -> int:
        return self._call_count


# ======================================================================
# Differential Learning Loop
# ======================================================================

class Evaluator:
    """
    The full generate → judge → learn loop.
    Runs multiple attempts per prompt, learns from score differentials.
    """

    def __init__(self, engine: "Engine", judge: Judge | MockJudge | None = None):
        self.engine = engine
        self.generator = Generator(engine)
        self.judge = judge or MockJudge()
        self._records: list[LearningRecord] = []

    def learn(self, prompt: str, iterations: int = 5,
              on_attempt: Callable | None = None) -> LearningRecord:
        """
        Run the generate → judge → differential learn loop.

        Each iteration:
        1. Generate response (deterministic given current network state)
        2. Judge scores it
        3. Store evaluation as a node (changes the network)
        4. Compare to previous attempt if score changed
        5. Create reinforcement or correction nodes
        6. Next iteration sees these nodes in context → different output
        """
        lib = self.engine.librarian
        record = LearningRecord(prompt=prompt)

        for i in range(iterations):
            # Generate — deterministic, but network may have changed
            response = self.generator.respond(prompt)

            # Judge
            score = self.judge.evaluate(prompt, response)

            attempt = Attempt(
                prompt=prompt,
                response=response,
                score=score,
                attempt_number=i + 1,
            )
            record.attempts.append(attempt)

            if on_attempt:
                on_attempt(attempt)

            # ALWAYS store evaluation node — this changes the network
            # so the next attempt gets different context
            self._store_evaluation(attempt, lib)

            # Differential learning (compare to previous if scores differ)
            if i > 0:
                prev = record.attempts[i - 1]
                self._differential_learn(prev, attempt, record, lib)

        self._records.append(record)
        return record

    def _store_evaluation(self, attempt: Attempt, lib: "Librarian"):
        """
        Store the evaluation result as a node in the network.
        Wire reverse pointers so the librarian finds it when
        the same prompt words appear again.
        """
        eval_node = Node(
            name="evaluation",
            tier=Tier.TRIAL,
            flags={NodeFlag.ACTIVE},
        )
        eval_node.content = {
            "type": "evaluation",
            "attempt": attempt.attempt_number,
            "prompt": attempt.prompt[:100],
            "response": attempt.response[:200],
            "scores": {
                "accuracy": attempt.score.accuracy,
                "fluency": attempt.score.fluency,
                "completeness": attempt.score.completeness,
                "relevance": attempt.score.relevance,
                "average": round(attempt.score.average, 2),
            },
            "judge_note": attempt.score.note,
        }

        # Forward pointers: evaluation → prompt words
        prompt_words = attempt.prompt.lower().split()
        for word in prompt_words:
            clean = word.strip(".,!?;:'\"")
            ids = lib.recognize(clean)
            if ids:
                eval_node.pointers.append(
                    Pointer(target=ids[0], relation="evaluates"))
                # REVERSE pointer: prompt word → evaluation node
                # This is how the librarian finds it on the next attempt
                word_node = lib.get_node(ids[0])
                if word_node:
                    word_node.pointers.append(
                        Pointer(target=eval_node.id, relation="has_evaluation"))

        lib.store_node(eval_node)

    def _differential_learn(self, prev: Attempt, curr: Attempt,
                            record: LearningRecord, lib: "Librarian"):
        """
        Compare two attempts. Create learning nodes from the differential.
        """
        # Score differential
        score_delta = curr.score.average - prev.score.average
        accuracy_delta = curr.score.accuracy - prev.score.accuracy
        fluency_delta = curr.score.fluency - prev.score.fluency
        completeness_delta = curr.score.completeness - prev.score.completeness
        relevance_delta = curr.score.relevance - prev.score.relevance

        # Compare the actual responses
        register = self.engine._get_register()
        from .models import Assignment

        prev_node = Node(name="prev_attempt")
        prev_node.content = prev.response

        curr_node = Node(name="curr_attempt")
        curr_node.content = curr.response

        assignment = Assignment(
            foundation=list(lib._nodes[addr] for addr in lib._foundation if addr in lib._nodes),
            context=[prev_node, curr_node],
            input_raw={"type": "differential_learn"},
        )
        register.load_assignment(assignment)
        records = register.compare(prev_node, curr_node)
        package = register.hand_back()

        # What changed between attempts?
        same_aspects = [r for r in records if r.result == DiffResult.SAME]
        diff_aspects = [r for r in records if r.result == DiffResult.DIFFERENT]

        # Create learning node — ALWAYS
        # The node's presence changes the network for next attempt
        if score_delta > 0:
            node_type = "reinforcement"
        elif score_delta < 0:
            node_type = "correction"
        else:
            node_type = "observation"

        learning_node = Node(
            name=node_type,
            tier=Tier.TRIAL,
            flags={NodeFlag.ACTIVE},
        )

        learning_content = {
            "type": node_type,
            "prompt_structure": self._extract_structure(curr.prompt),
            "score_delta": round(score_delta, 2),
            "score_breakdown": {
                "accuracy": round(accuracy_delta, 2),
                "fluency": round(fluency_delta, 2),
                "completeness": round(completeness_delta, 2),
                "relevance": round(relevance_delta, 2),
            },
            "prev_response": prev.response[:100],
            "curr_response": curr.response[:100],
            "what_changed": [r.detail for r in diff_aspects[:5]],
            "what_stayed": [r.detail for r in same_aspects[:3]],
            "judge_note": curr.score.note,
        }
        learning_node.content = learning_content

        # Forward + REVERSE pointers — this is how the librarian
        # finds learning nodes when the same prompt comes in again
        for word in curr.prompt.lower().split():
            clean = word.strip(".,!?;:'\"")
            ids = lib.recognize(clean)
            if ids:
                learning_node.pointers.append(
                    Pointer(target=ids[0], relation=f"{node_type}_context"))
                word_node = lib.get_node(ids[0])
                if word_node:
                    word_node.pointers.append(
                        Pointer(target=learning_node.id, relation=f"has_{node_type}"))

        lib.store_node(learning_node)
        record.nodes_created += 1

        if score_delta > 0:
            record.improvements.append(
                f"attempt {curr.attempt_number}: +{score_delta:.1f} — {curr.score.note}")
        elif score_delta < 0:
            record.regressions.append(
                f"attempt {curr.attempt_number}: {score_delta:.1f} — {curr.score.note}")

    def _extract_structure(self, text: str) -> str:
        """Extract structural pattern of the prompt."""
        lib = self.engine.librarian
        tokens = text.lower().strip(".,!?").split()
        parts = []
        for token in tokens:
            clean = token.strip(".,!?;:'\"")
            ids = lib.recognize(clean)
            parts.append("known" if ids else "unknown")
        return " ".join(parts)

    def run_experiment(self, prompts: list[str], iterations: int = 5,
                       on_progress: Callable | None = None) -> dict[str, Any]:
        """
        Run the full experiment: multiple prompts, multiple iterations each.
        Returns trajectory data for analysis.
        """
        results = {
            "prompts": len(prompts),
            "iterations": iterations,
            "records": [],
            "trajectory": [],  # avg score at each iteration across all prompts
            "judge_calls": 0,
        }

        # Initialize trajectory tracking
        iteration_scores = [[] for _ in range(iterations)]

        for pi, prompt in enumerate(prompts):
            if on_progress:
                on_progress(pi + 1, len(prompts), prompt)

            record = self.learn(prompt, iterations=iterations)
            results["records"].append({
                "prompt": prompt,
                "trajectory": record.score_trajectory,
                "improved": record.improved,
                "improvements": record.improvements,
                "regressions": record.regressions,
                "nodes_created": record.nodes_created,
                "final_response": record.attempts[-1].response if record.attempts else "",
            })

            # Add to per-iteration scores
            for i, score in enumerate(record.score_trajectory):
                if i < iterations:
                    iteration_scores[i].append(score)

        # Compute average trajectory
        for scores in iteration_scores:
            if scores:
                results["trajectory"].append(sum(scores) / len(scores))
            else:
                results["trajectory"].append(0)

        results["judge_calls"] = self.judge.calls_made

        # Summary
        improved_count = sum(1 for r in results["records"] if r["improved"])
        results["improved_count"] = improved_count
        results["improvement_rate"] = improved_count / len(prompts) if prompts else 0

        return results

    @property
    def records(self) -> list[LearningRecord]:
        return list(self._records)


# ======================================================================
# Default experiment prompts
# ======================================================================

EXPERIMENT_PROMPTS = [
    "Describe a cat.",
    "What is the difference between a cat and a dog?",
    "What do animals need to survive?",
    "Write a sentence about a bird.",
    "What is addition?",
    "Describe something big.",
    "What does a person do?",
    "How are a cat and a dog similar?",
    "What is the opposite of hot?",
    "Describe water.",
    "What is a house?",
    "Name an animal that can fly.",
    "What is the relationship between day and night?",
    "Describe food.",
    "What do people read?",
    "What is a tree?",
    "How does a fish move?",
    "What is time?",
    "Describe the world.",
    "What makes something alive?",
]
