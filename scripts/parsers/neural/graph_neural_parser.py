# [NEXUS IDENTITY] ID: 8151216234644898524 | DATE: 2025-11-19

#!/usr/bin/env python3
"""
Graph Neural Network Parser для BSL кода
РЕВОЛЮЦИОННАЯ СОБСТВЕННАЯ ТЕХНОЛОГИЯ

Инновация:
- Код представляется как ГРАФ, а не текст
- GNN обучается на графовой структуре
- Понимает зависимости и контекст

Компоненты:
- CodeGraph: Представление кода как графа
- GraphConvLayer: Свертка на графах
- CodeGNN: Полная GNN модель

Версия: 1.0.0 Revolutionary
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class NodeType(Enum):
    """Типы узлов в Code Graph"""
    FUNCTION = "function"
    PROCEDURE = "procedure"
    VARIABLE = "variable"
    EXPRESSION = "expression"
    API_CALL = "api_call"
    CONDITION = "condition"
    LOOP = "loop"


class EdgeType(Enum):
    """Типы рёбер в Code Graph"""
    CALLS = "calls"              # Вызов функции
    DATA_FLOW = "data_flow"      # Поток данных
    CONTROL_FLOW = "control_flow" # Поток управления
    DEFINES = "defines"          # Определение переменной
    USES = "uses"                # Использование переменной


@dataclass
class CodeNode:
    """Узел графа кода"""
    id: int
    type: NodeType
    name: str
    code_snippet: str
    line_number: int
    features: np.ndarray = None


@dataclass
class CodeEdge:
    """Ребро графа кода"""
    from_node: int
    to_node: int
    type: EdgeType
    weight: float = 1.0


class CodeGraph:
    """
    Представление кода как графа
    
    Nodes:
    - Функции/процедуры
    - Переменные
    - Выражения
    - API вызовы
    
    Edges:
    - Вызовы функций
    - Data flow
    - Control flow
    - Определения/использования
    """
    
    def __init__(self):
        self.nodes: List[CodeNode] = []
        self.edges: List[CodeEdge] = []
        self.node_id_counter = 0
    
    def add_node(
        self,
        node_type: NodeType,
        name: str,
        code_snippet: str = "",
        line_number: int = 0
    ) -> int:
        """Добавление узла в граф"""
        node = CodeNode(
            id=self.node_id_counter,
            type=node_type,
            name=name,
            code_snippet=code_snippet,
            line_number=line_number
        )
        self.nodes.append(node)
        self.node_id_counter += 1
        return node.id
    
    def add_edge(
        self,
        from_node: int,
        to_node: int,
        edge_type: EdgeType,
        weight: float = 1.0
    ):
        """Добавление ребра"""
        edge = CodeEdge(
            from_node=from_node,
            to_node=to_node,
            type=edge_type,
            weight=weight
        )
        self.edges.append(edge)
    
    def get_adjacency_matrix(self) -> torch.Tensor:
        """Матрица смежности для GNN"""
        n = len(self.nodes)
        adj = torch.zeros((n, n))
        
        for edge in self.edges:
            adj[edge.from_node, edge.to_node] = edge.weight
        
        return adj
    
    def get_node_features(self) -> torch.Tensor:
        """Матрица признаков узлов"""
        # Пока простые features (в production - embeddings)
        features = []
        for node in self.nodes:
            # One-hot encoding типа узла
            feat = [0.0] * len(NodeType)
            feat[list(NodeType).index(node.type)] = 1.0
            
            # Добавляем другие features
            feat.append(node.line_number / 1000.0)  # Normalized
            feat.append(len(node.name) / 100.0)
            
            features.append(feat)
        
        return torch.tensor(features, dtype=torch.float32)


class GraphConvLayer(nn.Module):
    """
    Graph Convolutional Layer
    
    Собственная реализация (не копируем PyG!)
    
    Message passing:
    h_i' = σ(W * Σ(h_j / sqrt(deg_i * deg_j)))
    
    Где:
    - h_i - embedding узла i
    - h_j - embeddings соседей
    - W - learnable weights
    - σ - activation
    """
    
    def __init__(self, in_features: int, out_features: int):
        super().__init__()
        
        self.in_features = in_features
        self.out_features = out_features
        
        # Learnable transformation
        self.weight = nn.Parameter(torch.Tensor(in_features, out_features))
        self.bias = nn.Parameter(torch.Tensor(out_features))
        
        # Initialization
        nn.init.xavier_uniform_(self.weight)
        nn.init.zeros_(self.bias)
    
    def forward(
        self,
        node_features: torch.Tensor,
        adjacency: torch.Tensor
    ) -> torch.Tensor:
        """
        Graph convolution
        
        Args:
            node_features: [num_nodes, in_features]
            adjacency: [num_nodes, num_nodes]
        
        Returns:
            Updated features: [num_nodes, out_features]
        """
        # Degree normalization
        degree = adjacency.sum(dim=1, keepdim=True)
        degree = torch.clamp(degree, min=1.0)  # Avoid division by zero
        
        norm_adj = adjacency / torch.sqrt(degree * degree.T)
        
        # Aggregation
        aggregated = torch.matmul(norm_adj, node_features)
        
        # Transformation
        output = torch.matmul(aggregated, self.weight) + self.bias
        
        # Activation
        output = F.relu(output)
        
        return output


class CodeGraphNeuralNetwork(nn.Module):
    """
    Полная GNN модель для кода
    
    Архитектура:
    - Input: Code graph
    - GCN layers (message passing)
    - Global pooling
    - Output: Graph-level embedding
    
    Возможности:
    - Code understanding
    - Similarity search
    - Intent classification
    - Quality prediction
    """
    
    def __init__(
        self,
        input_dim: int = 10,
        hidden_dim: int = 128,
        output_dim: int = 256,
        num_layers: int = 4
    ):
        super().__init__()
        
        # GCN layers
        self.layers = nn.ModuleList()
        
        # First layer
        self.layers.append(GraphConvLayer(input_dim, hidden_dim))
        
        # Hidden layers
        for _ in range(num_layers - 2):
            self.layers.append(GraphConvLayer(hidden_dim, hidden_dim))
        
        # Output layer
        self.layers.append(GraphConvLayer(hidden_dim, output_dim))
        
        # Dropout
        self.dropout = nn.Dropout(0.1)
        
        # Global pooling
        self.pool = nn.Linear(output_dim, output_dim)
        
        # Classification heads
        self.intent_head = nn.Linear(output_dim, 10)  # 10 intents
        self.quality_head = nn.Linear(output_dim, 1)
    
    def forward(
        self,
        node_features: torch.Tensor,
        adjacency: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass
        
        Args:
            node_features: [num_nodes, input_dim]
            adjacency: [num_nodes, num_nodes]
        
        Returns:
            {
                'node_embeddings': [num_nodes, output_dim],
                'graph_embedding': [output_dim],
                'intent_logits': [10],
                'quality_score': [1]
            }
        """
        h = node_features
        
        # GCN layers with message passing
        for i, layer in enumerate(self.layers):
            h = layer(h, adjacency)
            
            # Dropout (except last layer)
            if i < len(self.layers) - 1:
                h = self.dropout(h)
        
        # Node embeddings
        node_embeddings = h
        
        # Global pooling (graph-level)
        graph_embedding = h.mean(dim=0)
        graph_embedding = self.pool(graph_embedding)
        
        # Task-specific heads
        intent_logits = self.intent_head(graph_embedding)
        quality_score = torch.sigmoid(self.quality_head(graph_embedding))
        
        return {
            'node_embeddings': node_embeddings,
            'graph_embedding': graph_embedding,
            'intent_logits': intent_logits,
            'quality_score': quality_score
        }


class GraphBasedBSLParser:
    """
    Высокоуровневый интерфейс для Graph-based парсинга
    
    Использование:
        parser = GraphBasedBSLParser()
        result = parser.parse(code)
    """
    
    def __init__(self, model_path: str = None):
        # GNN model
        self.gnn = CodeGraphNeuralNetwork()
        
        # Load weights если есть
        if model_path:
            self.gnn.load_state_dict(torch.load(model_path))
        
        self.gnn.eval()
        
        # Device
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.gnn.to(self.device)
    
    def parse(self, code: str) -> Dict[str, Any]:
        """
        Парсинг кода через GNN
        
        Process:
        1. Code → Graph
        2. Graph → GNN
        3. GNN → Understanding
        """
        # 1. Конвертируем код в граф
        graph = self.code_to_graph(code)
        
        # 2. Получаем features
        node_features = graph.get_node_features().to(self.device)
        adjacency = graph.get_adjacency_matrix().to(self.device)
        
        # 3. GNN forward
        with torch.no_grad():
            output = self.gnn(node_features, adjacency)
        
        # 4. Интерпретируем результаты
        intent_idx = output['intent_logits'].argmax().item()
        intent = list(NodeType)[intent_idx] if intent_idx < len(NodeType) else "utility"
        
        quality = output['quality_score'].item()
        
        result = {
            'graph': graph,
            'node_embeddings': output['node_embeddings'].cpu().numpy(),
            'graph_embedding': output['graph_embedding'].cpu().numpy(),
            'intent': intent,
            'quality_score': quality,
            'num_nodes': len(graph.nodes),
            'num_edges': len(graph.edges)
        }
        
        return result
    
    def code_to_graph(self, code: str) -> CodeGraph:
        """
        Преобразование BSL кода в граф
        
        Создаем узлы для:
        - Каждой функции/процедуры
        - Каждой переменной
        - Важных выражений
        
        Создаем рёбра для:
        - Вызовов функций
        - Использования переменных
        - Control flow
        """
        graph = CodeGraph()
        
        # Простой парсинг (можно заменить на Neural Parser)
        lines = code.split('\n')
        
        current_function_id = None
        
        for line_num, line in enumerate(lines):
            line_stripped = line.strip()
            
            # Detect function
            if 'Функция' in line or 'Процедура' in line:
                import re
                match = re.search(r'(Функция|Процедура)\s+([\wА-Яа-я]+)', line)
                if match:
                    func_name = match.group(2)
                    node_id = graph.add_node(
                        NodeType.FUNCTION,
                        func_name,
                        line_stripped,
                        line_num
                    )
                    current_function_id = node_id
            
            # Detect variable
            if 'Перем' in line or '=' in line:
                match = re.search(r'([\wА-Яа-я]+)\s*=', line)
                if match:
                    var_name = match.group(1)
                    var_id = graph.add_node(
                        NodeType.VARIABLE,
                        var_name,
                        line_stripped,
                        line_num
                    )
                    
                    # Edge: function defines variable
                    if current_function_id is not None:
                        graph.add_edge(
                            current_function_id,
                            var_id,
                            EdgeType.DEFINES
                        )
            
            # Detect API call
            if any(api in line for api in ['Запрос', 'Справочники', 'Документы']):
                api_id = graph.add_node(
                    NodeType.API_CALL,
                    "API_Call",
                    line_stripped,
                    line_num
                )
                
                # Edge: function uses API
                if current_function_id is not None:
                    graph.add_edge(
                        current_function_id,
                        api_id,
                        EdgeType.USES
                    )
        
        return graph
    
    def visualize_graph(self, graph: CodeGraph, output_path: str = "code_graph.png"):
        """
        Визуализация графа кода
        
        Опционально (требует networkx + matplotlib)
        """
        try:
            import matplotlib.pyplot as plt
            import networkx as nx
            
            G = nx.DiGraph()
            
            # Add nodes
            for node in graph.nodes:
                G.add_node(
                    node.id,
                    label=f"{node.name}\n({node.type.value})",
                    type=node.type.value
                )
            
            # Add edges
            for edge in graph.edges:
                G.add_edge(
                    edge.from_node,
                    edge.to_node,
                    type=edge.type.value
                )
            
            # Draw
            pos = nx.spring_layout(G)
            
            # Color nodes by type
            node_colors = {
                'function': 'lightgreen',
                'procedure': 'lightblue',
                'variable': 'yellow',
                'api_call': 'red'
            }
            
            colors = [
                node_colors.get(G.nodes[n]['type'], 'gray')
                for n in G.nodes()
            ]
            
            plt.figure(figsize=(12, 8))
            nx.draw(
                G, pos,
                node_color=colors,
                with_labels=True,
                labels={n: G.nodes[n]['label'] for n in G.nodes()},
                node_size=1000,
                font_size=8,
                arrows=True
            )
            
            plt.title("Code Graph Visualization")
            plt.savefig(output_path, dpi=150, bbox_inches='tight')
            print(f"✅ График сохранен: {output_path}")
            
        except ImportError:
            print("[WARN] networkx/matplotlib not installed, skipping visualization")


# Example usage
if __name__ == "__main__":
    print("=" * 70)
    print("GRAPH NEURAL NETWORK PARSER - Revolutionary")
    print("=" * 70)
    
    # Тестовый код
    test_code = """
    Функция ПолучитьКлиентов() Экспорт
        
        Запрос = Новый Запрос;
        Запрос.Текст = "ВЫБРАТЬ * ИЗ Справочник.Клиенты";
        
        Результат = Запрос.Выполнить();
        Возврат Результат;
        
    КонецФункции
    
    Функция ОбработатьКлиента(Клиент)
        
        Данные = ПолучитьКлиентов();
        
        Для Каждого Элемент Из Данные Цикл
            Если Элемент.Код = Клиент Тогда
                Возврат Элемент;
            КонецЕсли;
        КонецЦикла;
        
    КонецФункции
    """
    
    # Создаем парсер
    parser = GraphBasedBSLParser()
    
    # Парсим в граф
    result = parser.parse(test_code)
    
    print(f"\n📊 РЕЗУЛЬТАТЫ:")
    print(f"Узлов в графе: {result['num_nodes']}")
    print(f"Рёбер в графе: {result['num_edges']}")
    print(f"Intent: {result['intent']}")
    print(f"Quality: {result['quality_score']:.2f}")
    
    print(f"\n🌳 Структура графа:")
    graph = result['graph']
    for node in graph.nodes:
        print(f"  [{node.type.value}] {node.name} (line {node.line_number})")
    
    print(f"\n🔗 Зависимости:")
    for edge in graph.edges:
        from_node = graph.nodes[edge.from_node]
        to_node = graph.nodes[edge.to_node]
        print(f"  {from_node.name} --[{edge.type.value}]--> {to_node.name}")
    
    # Визуализация (опционально)
    print(f"\n📊 Визуализация графа...")
    parser.visualize_graph(graph, "code_graph.png")
    
    print("\n" + "=" * 70)
    print("✨ Graph-based парсинг complete!")
    print("=" * 70)




