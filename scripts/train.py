from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset
from torch.optim import AdamW
from transformers import AutoTokenizer

from triage_api.labels import SEVERITY_RANK, SUBTYPE_TO_INDEX
from triage_api.model import HierarchicalTriageModel


MAX_TURNS = 8


def inject_noise(text: str) -> str:
    replacements = {"because": "bc", "you": "u", "are": "r", "please": "pls"}
    words = text.split()
    return " ".join(replacements.get(word.lower(), word) for word in words)


def maybe_augment_turns(turns: list[dict]) -> list[dict]:
    augmented: list[dict] = []
    for turn in turns:
        content = turn["content"]
        if random.random() < 0.25:
            content = inject_noise(content)
        augmented.append({"role": turn["role"], "content": content})
    return augmented


class TriageDataset(Dataset):
    def __init__(self, records: list[dict], tokenizer: AutoTokenizer) -> None:
        self.records = records
        self.tokenizer = tokenizer

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> dict:
        record = self.records[index]
        turns = maybe_augment_turns(record["conversation_turns"])
        texts = [f"[{turn['role'].upper()}] {turn['content']}" for turn in turns[-MAX_TURNS:]]
        if len(texts) < MAX_TURNS:
            texts = texts + [""] * (MAX_TURNS - len(texts))

        encoded_turns = self.tokenizer(
            texts,
            padding="max_length",
            truncation=True,
            max_length=128,
            return_tensors="pt",
        )
        encoded_history = self.tokenizer(
            record.get("prior_summary") or "previous_high_crisis: no; prior_subtypes: none; repeated_emergencies: 0",
            padding="max_length",
            truncation=True,
            max_length=96,
            return_tensors="pt",
        )

        return {
            "turn_input_ids": encoded_turns["input_ids"],
            "turn_attention_mask": encoded_turns["attention_mask"],
            "history_input_ids": encoded_history["input_ids"].squeeze(0),
            "history_attention_mask": encoded_history["attention_mask"].squeeze(0),
            "severity_label": torch.tensor(SEVERITY_RANK[record["severity_label"]], dtype=torch.long),
            "subtype_label": torch.tensor(SUBTYPE_TO_INDEX[record["subtype_label"]], dtype=torch.long),
            "emergency_flag": torch.tensor(float(record["emergency_flag"]), dtype=torch.float32),
        }


def collate_batch(batch: list[dict]) -> dict[str, torch.Tensor]:
    return {
        "turn_input_ids": torch.stack([item["turn_input_ids"] for item in batch], dim=0),
        "turn_attention_mask": torch.stack([item["turn_attention_mask"] for item in batch], dim=0),
        "history_input_ids": torch.stack([item["history_input_ids"] for item in batch], dim=0),
        "history_attention_mask": torch.stack([item["history_attention_mask"] for item in batch], dim=0),
        "severity_label": torch.stack([item["severity_label"] for item in batch], dim=0),
        "subtype_label": torch.stack([item["subtype_label"] for item in batch], dim=0),
        "emergency_flag": torch.stack([item["emergency_flag"] for item in batch], dim=0),
    }


def load_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def train(args: argparse.Namespace) -> None:
    tokenizer = AutoTokenizer.from_pretrained(args.encoder_name)
    records = load_jsonl(Path(args.data))
    dataset = TriageDataset(records, tokenizer)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, collate_fn=collate_batch)

    model = HierarchicalTriageModel(encoder_name=args.encoder_name)
    optimizer = AdamW(model.parameters(), lr=args.learning_rate)
    severity_loss = nn.CrossEntropyLoss(weight=torch.tensor([1.0, 1.4, 2.5]))
    subtype_loss = nn.CrossEntropyLoss()
    emergency_loss = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([2.0]))

    model.train()
    for epoch in range(args.epochs):
        running = 0.0
        for batch in loader:
            outputs = model(
                turn_input_ids=batch["turn_input_ids"],
                turn_attention_mask=batch["turn_attention_mask"],
                history_input_ids=batch["history_input_ids"],
                history_attention_mask=batch["history_attention_mask"],
            )
            loss = (
                severity_loss(outputs.severity_logits, batch["severity_label"])
                + subtype_loss(outputs.subtype_logits, batch["subtype_label"])
                + emergency_loss(outputs.emergency_logits, batch["emergency_flag"])
            )
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            running += float(loss.item())

        avg_loss = running / max(len(loader), 1)
        print(f"epoch={epoch + 1} loss={avg_loss:.4f}")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), output_path)
    print(f"saved checkpoint to {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--encoder-name", default="microsoft/deberta-v3-base")
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    return parser.parse_args()


if __name__ == "__main__":
    train(parse_args())
