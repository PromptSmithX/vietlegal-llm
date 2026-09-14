"""Optional Transformers backend for the Kaggle GPU execution path."""

from __future__ import annotations

import hashlib
import time
from typing import Any

from .baseline import BaselineConfig


class TransformersGenerator:
    def __init__(self, config: BaselineConfig) -> None:
        try:
            import torch  # type: ignore[import-not-found]
            from transformers import (  # type: ignore[import-not-found]
                AutoModelForCausalLM,
                AutoTokenizer,
                set_seed,
            )
        except ImportError as exc:  # pragma: no cover - exercised on GPU environments
            raise RuntimeError("install the project with the baseline extra") from exc
        if not torch.cuda.is_available():  # pragma: no cover - hardware dependent
            raise RuntimeError("a CUDA GPU is required for the Qwen3-4B baseline")
        set_seed(config.seed)
        self._torch: Any = torch
        self._config = config
        self._tokenizer: Any = AutoTokenizer.from_pretrained(
            config.model_id, revision=config.revision
        )
        self._model: Any = AutoModelForCausalLM.from_pretrained(
            config.model_id,
            revision=config.revision,
            torch_dtype=torch.float16,
            device_map={"": 0},
            trust_remote_code=False,
            use_safetensors=True,
        )
        self.chat_template_sha256 = hashlib.sha256(
            (self._tokenizer.chat_template or "").encode("utf-8")
        ).hexdigest()

    def generate(
        self, prompt: str
    ) -> tuple[str, int, int, float]:  # pragma: no cover - GPU dependent
        messages = [{"role": "user", "content": prompt}]
        text = self._tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=self._config.enable_thinking,
        )
        inputs = self._tokenizer(
            text, return_tensors="pt", truncation=True, max_length=self._config.max_input_tokens
        ).to("cuda")
        started = time.perf_counter()
        with self._torch.inference_mode():
            output = self._model.generate(
                **inputs, max_new_tokens=self._config.max_new_tokens, do_sample=False
            )
        generated = output[0][inputs.input_ids.shape[-1] :]
        return (
            self._tokenizer.decode(generated, skip_special_tokens=True),
            int(inputs.input_ids.shape[-1]),
            int(generated.shape[-1]),
            (time.perf_counter() - started) * 1000,
        )
