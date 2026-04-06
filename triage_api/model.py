from __future__ import annotations

from dataclasses import dataclass

import torch
import torch.nn as nn
from transformers import AutoModel

from .labels import SEVERITY_LABELS, SUBTYPE_LABELS


@dataclass
class ModelOutput:
    severity_logits: torch.Tensor
    subtype_logits: torch.Tensor
    emergency_logits: torch.Tensor
    risk_score: torch.Tensor


class HierarchicalTriageModel(nn.Module):
    def __init__(
        self,
        encoder_name: str = "microsoft/deberta-v3-base",
        context_layers: int = 2,
        max_turns: int = 8,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        self.encoder = AutoModel.from_pretrained(encoder_name)
        hidden_size = int(self.encoder.config.hidden_size)
        self.max_turns = max_turns

        self.turn_positions = nn.Embedding(max_turns + 2, hidden_size)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=hidden_size,
            nhead=8,
            dim_feedforward=hidden_size * 4,
            dropout=dropout,
            batch_first=True,
            activation="gelu",
        )
        self.context_encoder = nn.TransformerEncoder(encoder_layer, num_layers=context_layers)

        self.history_projection = nn.Sequential(
            nn.Linear(hidden_size, hidden_size),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.fusion = nn.Sequential(
            nn.Linear(hidden_size * 2, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.GELU(),
            nn.Dropout(dropout),
        )

        self.severity_head = nn.Linear(hidden_size, len(SEVERITY_LABELS))
        self.subtype_head = nn.Linear(hidden_size, len(SUBTYPE_LABELS))
        self.emergency_head = nn.Linear(hidden_size, 1)
        self.risk_score_head = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.GELU(),
            nn.Linear(hidden_size // 2, 1),
            nn.Sigmoid(),
        )

    @staticmethod
    def masked_mean(last_hidden_state: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        mask = attention_mask.unsqueeze(-1).float()
        masked = last_hidden_state * mask
        denom = mask.sum(dim=1).clamp_min(1e-6)
        return masked.sum(dim=1) / denom

    def encode_sequence(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        return self.masked_mean(outputs.last_hidden_state, attention_mask)

    def forward(
        self,
        turn_input_ids: torch.Tensor,
        turn_attention_mask: torch.Tensor,
        history_input_ids: torch.Tensor,
        history_attention_mask: torch.Tensor,
    ) -> ModelOutput:
        batch_size, num_turns, seq_len = turn_input_ids.shape
        flat_ids = turn_input_ids.view(batch_size * num_turns, seq_len)
        flat_mask = turn_attention_mask.view(batch_size * num_turns, seq_len)
        turn_embeddings = self.encode_sequence(flat_ids, flat_mask)
        turn_embeddings = turn_embeddings.view(batch_size, num_turns, -1)

        positions = torch.arange(num_turns, device=turn_embeddings.device).unsqueeze(0)
        turn_embeddings = turn_embeddings + self.turn_positions(positions)
        context_encoded = self.context_encoder(turn_embeddings)
        turn_mask = (turn_attention_mask.sum(dim=-1) > 0).float().unsqueeze(-1)
        conversation_embedding = (context_encoded * turn_mask).sum(dim=1) / turn_mask.sum(dim=1).clamp_min(1.0)

        history_embedding = self.encode_sequence(history_input_ids, history_attention_mask)
        history_embedding = self.history_projection(history_embedding)
        fused = self.fusion(torch.cat([conversation_embedding, history_embedding], dim=-1))

        return ModelOutput(
            severity_logits=self.severity_head(fused),
            subtype_logits=self.subtype_head(fused),
            emergency_logits=self.emergency_head(fused).squeeze(-1),
            risk_score=self.risk_score_head(fused).squeeze(-1) * 100.0,
        )
