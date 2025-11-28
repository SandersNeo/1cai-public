"""
Temporal Graph Neural Network

Time-aware graph neural network for code evolution tracking.
Implements temporal attention and multi-scale aggregation.

Based on:
- Temporal Graph Networks (TGN)
- Nested Learning paradigm
"""

from typing import Dict, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

# Check for torch_geometric
try:
    from torch_geometric.nn import GATConv

    TORCH_GEOMETRIC_AVAILABLE = True
except ImportError:
    logger.warning("torch_geometric not available, using fallback implementation")
    TORCH_GEOMETRIC_AVAILABLE = False


class TemporalAttention(nn.Module):
    """
    Temporal attention mechanism

    Applies time-aware attention to graph nodes based on temporal distance.
    Recent nodes get higher attention weights.
    """

    def __init__(self, hidden_dim: int, time_decay: float = 86400.0):
        """
        Initialize temporal attention

        Args:
            hidden_dim: Hidden dimension size
            time_decay: Time decay constant (default: 1 day in seconds)
        """
        super().__init__()
        self.query = nn.Linear(hidden_dim, hidden_dim)
        self.key = nn.Linear(hidden_dim, hidden_dim)
        self.value = nn.Linear(hidden_dim, hidden_dim)
        self.scale = hidden_dim**0.5
        self.time_decay = time_decay

    def forward(self, x: torch.Tensor, timestamps: torch.Tensor) -> torch.Tensor:
        """
        Apply temporal attention

        Args:
            x: Node features [num_nodes, hidden_dim]
            timestamps: Node timestamps [num_nodes]

        Returns:
            Attended features [num_nodes, hidden_dim]
        """
        Q = self.query(x)
        K = self.key(x)
        V = self.value(x)

        # Compute time-aware attention scores
        # Recent nodes get higher weights
        time_diff = timestamps.unsqueeze(1) - timestamps.unsqueeze(0)
        time_decay = torch.exp(-torch.abs(time_diff) / self.time_decay)

        # Attention with temporal bias
        attention_scores = (Q @ K.T) / self.scale
        attention_scores = attention_scores + torch.log(time_decay + 1e-10)
        attention = torch.softmax(attention_scores, dim=-1)

        return attention @ V


class TimeEncoder(nn.Module):
    """
    Encode timestamps as learnable features

    Converts timestamps to continuous representations.
    """

    def __init__(self, hidden_dim: int):
        """
        Initialize time encoder

        Args:
            hidden_dim: Output dimension
        """
        super().__init__()
        self.linear = nn.Linear(1, hidden_dim)
        self.activation = nn.ReLU()

    def forward(self, timestamps: torch.Tensor) -> torch.Tensor:
        """
        Encode timestamps

        Args:
            timestamps: Timestamps [num_nodes]

        Returns:
            Time embeddings [num_nodes, hidden_dim]
        """
        # Normalize to days since epoch
        t_norm = timestamps / 86400.0

        # Encode
        time_emb = self.linear(t_norm.unsqueeze(-1))
        return self.activation(time_emb)


class TemporalGNN(nn.Module):
    """
    Temporal Graph Neural Network for code evolution

    Architecture:
    - Time-aware graph convolutions
    - Temporal attention mechanism
    - Multi-scale temporal aggregation
    - Impact prediction head

    Example:
        >>> model = TemporalGNN(node_features=128, hidden_dim=256)
        >>> output = model(x, edge_index, timestamps, edge_times)
        >>> impact = output["impact"]
    """

    def __init__(
        self,
        node_features: int = 128,
        hidden_dim: int = 256,
        num_layers: int = 3,
        num_heads: int = 4,
        dropout: float = 0.1,
    ):
        """
        Initialize Temporal GNN

        Args:
            node_features: Input feature dimension
            hidden_dim: Hidden layer dimension
            num_layers: Number of GNN layers
            num_heads: Number of attention heads (if using GAT)
            dropout: Dropout rate
        """
        super().__init__()

        self.node_features = node_features
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers

        # Graph convolution layers
        if TORCH_GEOMETRIC_AVAILABLE:
            self.conv_layers = nn.ModuleList(
                [
                    GATConv(
                        node_features if i == 0 else hidden_dim,
                        hidden_dim,
                        heads=num_heads,
                        concat=False,
                        dropout=dropout,
                    )
                    for i in range(num_layers)
                ]
            )
        else:
            # Fallback: simple linear layers
            self.conv_layers = nn.ModuleList(
                [nn.Linear(node_features if i == 0 else hidden_dim, hidden_dim)
                           for i in range(num_layers)]
            )

        # Temporal components
        self.temporal_attention = TemporalAttention(hidden_dim)
        self.time_encoder = TimeEncoder(hidden_dim)

        # Dropout
        self.dropout = nn.Dropout(dropout)

        # Output heads
        self.impact_predictor = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 1),
            nn.Sigmoid(),  # Impact score 0-1
        )

        self.change_classifier = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim // 2, 3),  # add/modify/delete
        )

        logger.info(
            f"Created TemporalGNN with {num_layers} layers, "
            f"hidden_dim={hidden_dim}, torch_geometric={TORCH_GEOMETRIC_AVAILABLE}"
        )

    def forward(
        self,
        x: torch.Tensor,
        edge_index: torch.Tensor,
        timestamps: torch.Tensor,
        edge_times: Optional[torch.Tensor] = None,
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass with temporal information

        Args:
            x: Node features [num_nodes, node_features]
            edge_index: Edge indices [2, num_edges]
            timestamps: Node creation times [num_nodes]
            edge_times: Edge creation times [num_edges] (optional)

        Returns:
            Dict with:
                - embeddings: Node embeddings [num_nodes, hidden_dim]
                - impact: Impact scores [num_nodes, 1]
                - change_type: Change type logits [num_nodes, 3]
        """
        # Encode time
        time_emb = self.time_encoder(timestamps)

        # Add time encoding to features
        if x.shape[1] == self.node_features:
            x = x + time_emb
        else:
            # If dimensions don't match, project first
            x = torch.cat([x, time_emb], dim=-1)
            x = nn.Linear(x.shape[1], self.node_features).to(x.device)(x)
            x = x + time_emb

        # Graph convolutions
        for i, conv in enumerate(self.conv_layers):
            if TORCH_GEOMETRIC_AVAILABLE:
                x = conv(x, edge_index)
            else:
                # Fallback: simple transformation
                x = conv(x)

            x = F.relu(x)
            x = self.dropout(x)

        # Temporal attention
        x = self.temporal_attention(x, timestamps)

        # Predictions
        impact = self.impact_predictor(x)
        change_type = self.change_classifier(x)

        return {"embeddings": x, "impact": impact, "change_type": change_type}

    def predict_impact(
        self, x: torch.Tensor, edge_index: torch.Tensor, timestamps: torch.Tensor, target_node_idx: int
    ) -> Tuple[float, np.ndarray]:
        """
        Predict impact of changing a specific node

        Args:
            x: Node features
            edge_index: Edge indices
            timestamps: Node timestamps
            target_node_idx: Index of node to change

        Returns:
            Tuple of (impact_score, affected_node_indices)
        """
        with torch.no_grad():
            output = self.forward(x, edge_index, timestamps)
            impact_scores = output["impact"].squeeze().numpy()

            # Target node impact
            target_impact = float(impact_scores[target_node_idx])

            # Find affected nodes (impact > threshold)
            threshold = 0.5
            affected_indices = np.where(impact_scores > threshold)[0]

            return target_impact, affected_indices


class GraphEvolutionTracker:
    """
    Track graph evolution over time

    Maintains history of graph changes and provides
    temporal queries.
    """

    def __init__(self, max_history: int = 1000):
        """
        Initialize evolution tracker

        Args:
            max_history: Maximum history entries to keep
        """
        self.max_history = max_history
        self.history = []

        logger.info("Created GraphEvolutionTracker with max_history=%s", max_history)

    def record_change(self, node_id: str, change_type: str, timestamp: float, metadata: Optional[Dict] = None):
        """
        Record a graph change

        Args:
            node_id: Changed node ID
            change_type: "add" | "modify" | "delete"
            timestamp: Change timestamp
            metadata: Optional metadata
        """
        change = {"node_id": node_id, "change_type": change_type,
            "timestamp": timestamp, "metadata": metadata or {}}

        self.history.append(change)

        # Evict old entries
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history :]

    def get_changes_since(self, timestamp: float, node_id: Optional[str] = None) -> list:
        """
        Get changes since timestamp

        Args:
            timestamp: Start timestamp
            node_id: Optional node ID filter

        Returns:
            List of changes
        """
        changes = [c for c in self.history if c["timestamp"] >= timestamp]

        if node_id:
            changes = [c for c in changes if c["node_id"] == node_id]

        return changes

    def get_change_frequency(self, node_id: str) -> float:
        """
        Get change frequency for node

        Args:
            node_id: Node ID

        Returns:
            Changes per day
        """
        node_changes = [c for c in self.history if c["node_id"] == node_id]

        if len(node_changes) < 2:
            return 0.0

        # Calculate time span
        timestamps = [c["timestamp"] for c in node_changes]
        time_span_days = (max(timestamps) - min(timestamps)) / 86400.0

        if time_span_days == 0:
            return 0.0

        return len(node_changes) / time_span_days

    def get_stats(self) -> Dict:
        """Get tracker statistics"""
        if not self.history:
            return {"total_changes": 0, "unique_nodes": 0, "avg_frequency": 0.0}

        unique_nodes = set(c["node_id"] for c in self.history)

        return {
            "total_changes": len(self.history),
            "unique_nodes": len(unique_nodes),
            "history_size": len(self.history),
            "max_history": self.max_history,
        }
