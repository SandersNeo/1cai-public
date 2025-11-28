"""
Code DNA Engine - Genetic Representation and Evolution of Code

Represents code as "DNA" for evolutionary optimization:
- Code genome representation
- Fitness evaluation
- Genetic operators (mutation, crossover)
- Evolution cycles
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class GeneType(Enum):
    """Types of code genes"""
    FUNCTION = "function"
    CLASS = "class"
    MODULE = "module"
    STATEMENT = "statement"


@dataclass
class CodeGene:
    """Single gene in code DNA"""
    gene_type: GeneType
    code: str
    fitness: float = 0.0
    metadata: Dict[str, Any] = None


class CodeDNAEngine:
    """
    Code DNA Engine for evolutionary code optimization

    Features:
    - Convert code to genetic representation
    - Evaluate fitness based on metrics
    - Apply genetic operators
    - Evolve code toward target metrics
    """

    def __init__(self):
        self.logger = logging.getLogger("code_dna_engine")
        self.genome_db = {}  # In-memory genome database
        self.generation = 0

    def encode_code(self, code: str, language: str = "bsl") -> List[CodeGene]:
        """
        Encode code into DNA (genes)

        Args:
            code: Source code
            language: Programming language

        Returns:
            List of code genes
        """
        genes = []

        # Simple encoding: split by functions
        if language == "bsl":
            genes = self._encode_bsl(code)
        else:
            # Generic encoding by lines
            lines = code.split("\n")
            for line in lines:
                if line.strip():
                    gene = CodeGene(
                        gene_type=GeneType.STATEMENT,
                        code=line,
                        metadata={"line_number": len(genes) + 1}
                    )
                    genes.append(gene)

        self.logger.info(f"Encoded code into {len(genes)} genes")
        return genes

    def _encode_bsl(self, code: str) -> List[CodeGene]:
        """Encode BSL code into genes"""
        genes = []
        current_function = []
        in_function = False

        for line in code.split("\n"):
            stripped = line.strip()

            if stripped.startswith("Функция") or stripped.startswith("Процедура"):
                in_function = True
                current_function = [line]
            elif stripped.startswith("КонецФункции") or stripped.startswith("КонецПроцедуры"):
                current_function.append(line)
                gene = CodeGene(
                    gene_type=GeneType.FUNCTION,
                    code="\n".join(current_function),
                    metadata={"language": "bsl"}
                )
                genes.append(gene)
                current_function = []
                in_function = False
            elif in_function:
                current_function.append(line)
            elif stripped:
                # Standalone statement
                gene = CodeGene(
                    gene_type=GeneType.STATEMENT,
                    code=line,
                    metadata={"language": "bsl"}
                )
                genes.append(gene)

        return genes

    def evaluate_fitness(
        self,
        genes: List[CodeGene],
        target_metrics: Dict[str, Any]
    ) -> float:
        """
        Evaluate fitness of code genes

        Args:
            genes: Code genes
            target_metrics: Target metrics (complexity, performance, etc.)

        Returns:
            Fitness score (0.0 - 1.0)
        """
        total_fitness = 0.0

        for gene in genes:
            gene_fitness = self._evaluate_gene_fitness(gene, target_metrics)
            gene.fitness = gene_fitness
            total_fitness += gene_fitness

        avg_fitness = total_fitness / len(genes) if genes else 0.0

        self.logger.info(f"Average fitness: {avg_fitness:.2f}")
        return avg_fitness

    def _evaluate_gene_fitness(
        self,
        gene: CodeGene,
        target_metrics: Dict[str, Any]
    ) -> float:
        """Evaluate single gene fitness"""
        fitness = 1.0

        # Complexity check
        target_complexity = target_metrics.get("complexity", "medium")
        code_length = len(gene.code)

        if target_complexity == "low" and code_length > 100:
            fitness -= 0.3
        elif target_complexity == "high" and code_length < 50:
            fitness -= 0.2

        # Error handling check
        if target_metrics.get("error_handling", False):
            if "Попытка" not in gene.code and "Исключение" not in gene.code:
                fitness -= 0.2

        # Comments check
        if target_metrics.get("comments", False):
            if "//" not in gene.code:
                fitness -= 0.1

        return max(0.0, min(1.0, fitness))

    async def evolve_code(
        self,
        code: str,
        target_metrics: Dict[str, Any],
        generations: int = 5
    ) -> Dict[str, Any]:
        """
        Evolve code toward target metrics

        Args:
            code: Original code
            target_metrics: Target metrics
            generations: Number of evolution cycles

        Returns:
            Evolution results
        """
        # Encode original code
        genes = self.encode_code(code)
        original_fitness = self.evaluate_fitness(genes, target_metrics)

        best_genes = genes
        best_fitness = original_fitness

        # Evolution loop
        for gen in range(generations):
            self.generation = gen + 1

            # Apply genetic operators
            mutated_genes = self._mutate(best_genes, target_metrics)

            # Evaluate new fitness
            new_fitness = self.evaluate_fitness(mutated_genes, target_metrics)

            # Selection: keep better version
            if new_fitness > best_fitness:
                best_genes = mutated_genes
                best_fitness = new_fitness
                self.logger.info(
                    f"Gen {gen+1}: Improved fitness to {best_fitness:.2f}"
                )
            else:
                self.logger.info(
                    f"Gen {gen+1}: No improvement ({new_fitness:.2f})"
                )

        # Decode best genes back to code
        evolved_code = self._decode_genes(best_genes)

        return {
            "original_code": code,
            "evolved_code": evolved_code,
            "original_fitness": original_fitness,
            "final_fitness": best_fitness,
            "improvement": best_fitness - original_fitness,
            "generations": generations
        }

    def _mutate(
        self,
        genes: List[CodeGene],
        target_metrics: Dict[str, Any]
    ) -> List[CodeGene]:
        """Apply mutations to genes"""
        mutated = []

        for gene in genes:
            new_gene = CodeGene(
                gene_type=gene.gene_type,
                code=gene.code,
                fitness=gene.fitness,
                metadata=gene.metadata
            )

            # Add error handling if needed
            if target_metrics.get("error_handling", False):
                if "Попытка" not in new_gene.code:
                    new_gene.code = self._add_error_handling(new_gene.code)

            # Add comments if needed
            if target_metrics.get("comments", False):
                if "//" not in new_gene.code:
                    new_gene.code = self._add_comments(new_gene.code)

            mutated.append(new_gene)

        return mutated

    def _add_error_handling(self, code: str) -> str:
        """Add error handling to code"""
        if "Функция" in code or "Процедура" in code:
            lines = code.split("\n")
            # Wrap body in try-catch
            result = [lines[0]]  # Function declaration
            result.append("    Попытка")
            result.extend(["    " + line for line in lines[1:-1]])
            result.append("    Исключение")
            result.append("        ЗаписьЖурналаРегистрации(\"Ошибка\");")
            result.append("    КонецПопытки;")
            result.append(lines[-1])  # End function
            return "\n".join(result)
        return code

    def _add_comments(self, code: str) -> str:
        """Add comments to code"""
        if "Функция" in code or "Процедура" in code:
            lines = code.split("\n")
            result = ["// Автоматически сгенерированная функция"]
            result.extend(lines)
            return "\n".join(result)
        return "// " + code

    def _decode_genes(self, genes: List[CodeGene]) -> str:
        """Decode genes back to code"""
        code_parts = [gene.code for gene in genes]
        return "\n".join(code_parts)

    def save_genome(self, genome_id: str, genes: List[CodeGene]):
        """Save genome to database"""
        self.genome_db[genome_id] = genes
        self.logger.info("Saved genome %s", genome_id)

    def load_genome(self, genome_id: str) -> Optional[List[CodeGene]]:
        """Load genome from database"""
        return self.genome_db.get(genome_id)


# Singleton instance
_code_dna_engine: Optional[CodeDNAEngine] = None


def get_code_dna_engine() -> CodeDNAEngine:
    """Get or create Code DNA engine singleton"""
    global _code_dna_engine

    if _code_dna_engine is None:
        _code_dna_engine = CodeDNAEngine()

    return _code_dna_engine


__all__ = ["CodeGene", "GeneType", "CodeDNAEngine", "get_code_dna_engine"]
