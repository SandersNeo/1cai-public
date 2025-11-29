# [NEXUS IDENTITY] ID: -7750000839409531302 | DATE: 2025-11-19

#!/usr/bin/env python3
"""
Test Kimi-Linear-48B для анализа больших конфигураций 1С
Проверка целесообразности использования модели с 200K контекстом
"""

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, List

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KimiLinear48BTest:
    """Тестер для Kimi-Linear-48B модели"""
    
    def __init__(
        self,
        model_name: str = "moonshotai/Kimi-Linear-48B-A3B-Instruct",
        use_4bit: bool = True
    ):
        """
        Инициализация тестера
        
        Args:
            model_name: Название модели на HuggingFace
            use_4bit: Использовать 4-bit quantization
        """
        self.model_name = model_name
        self.use_4bit = use_4bit
        
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        logger.info(f"Initializing KimiLinear48BTest")
        logger.info(f"  Model: {model_name}")
        logger.info(f"  Device: {self.device}")
        logger.info(f"  4-bit quantization: {use_4bit}")
    
    def load_model(self):
        """Загрузка модели Kimi-Linear-48B"""
        logger.info("Loading Kimi-Linear-48B model...")
        start_time = time.time()
        
        try:
            # Tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            
            # Model с quantization (если включен)
            if self.use_4bit:
                from transformers import BitsAndBytesConfig
                
                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_use_double_quant=True,
                )
                
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    quantization_config=bnb_config,
                    device_map="auto",
                    trust_remote_code=True
                )
            else:
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    device_map="auto",
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    trust_remote_code=True
                )
            
            load_time = time.time() - start_time
            
            logger.info(f"✓ Model loaded in {load_time:.2f}s")
            logger.info(f"  Model size: {self.model.num_parameters() / 1e9:.2f}B parameters")
            logger.info(f"  Max context: 200K tokens")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def load_1c_configuration(self, config_path: str) -> str:
        """
        Загрузка конфигурации 1С
        
        Args:
            config_path: Путь к директории с конфигурацией
        
        Returns:
            Объединенный код всей конфигурации
        """
        logger.info(f"Loading 1C configuration from: {config_path}")
        
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration not found: {config_path}")
        
        # Ищем все BSL файлы
        bsl_files = list(config_path.rglob("*.bsl"))
        logger.info(f"Found {len(bsl_files)} BSL files")
        
        # Загружаем код
        full_code = []
        total_lines = 0
        
        for bsl_file in bsl_files[:50]:  # Ограничим для теста первыми 50 файлами
            try:
                with open(bsl_file, 'r', encoding='utf-8-sig') as f:
                    content = f.read()
                    lines = len(content.split('\n'))
                    total_lines += lines
                    
                    full_code.append(f"// File: {bsl_file.name}")
                    full_code.append(content)
                    full_code.append("")
                    
            except Exception as e:
                logger.warning(f"Failed to read {bsl_file}: {e}")
        
        combined_code = "\n".join(full_code)
        
        logger.info(f"✓ Configuration loaded")
        logger.info(f"  Files: {len(bsl_files)}")
        logger.info(f"  Total lines: {total_lines}")
        logger.info(f"  Total chars: {len(combined_code)}")
        
        return combined_code
    
    def analyze_configuration(
        self,
        code: str,
        tasks: List[str],
        max_new_tokens: int = 2048
    ) -> Dict:
        """
        Анализ конфигурации с помощью Kimi-Linear-48B
        
        Args:
            code: Код конфигурации
            tasks: Список задач для анализа
            max_new_tokens: Максимальное количество новых токенов
        
        Returns:
            Dict с результатами анализа
        """
        logger.info("Analyzing configuration...")
        
        # Формируем промпт
        tasks_str = "\n".join(f"{i+1}. {task}" for i, task in enumerate(tasks))
        
        prompt = f"""Анализ конфигурации 1С:Предприятие

Код конфигурации:

{code}

Задачи для анализа:
{tasks_str}

Проведи детальный анализ и предоставь результаты по каждой задаче."""
        
        # Токенизация
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=200000  # Kimi поддерживает до 200K
        ).to(self.device)
        
        input_tokens = inputs['input_ids'].shape[1]
        logger.info(f"Input tokens: {input_tokens:,}")
        
        if input_tokens > 200000:
            logger.warning(f"⚠️ Input exceeds 200K tokens, truncating...")
        
        # Генерация
        logger.info("Generating analysis...")
        start_time = time.time()
        
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=0.7,
                do_sample=True,
                top_p=0.9,
            )
        
        generation_time = time.time() - start_time
        
        # Декодирование
        output_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Извлекаем только ответ (без промпта)
        response = output_text[len(prompt):].strip()
        
        output_tokens = outputs.shape[1] - input_tokens
        tokens_per_sec = output_tokens / generation_time if generation_time > 0 else 0
        
        logger.info(f"✓ Analysis complete")
        logger.info(f"  Generation time: {generation_time:.2f}s")
        logger.info(f"  Output tokens: {output_tokens}")
        logger.info(f"  Speed: {tokens_per_sec:.2f} tokens/s")
        
        return {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "generation_time": generation_time,
            "tokens_per_sec": tokens_per_sec,
            "response": response,
            "tasks": tasks,
        }
    
    def run_benchmark(self, config_path: str) -> Dict:
        """
        Полный бенчмарк модели на конфигурации 1С
        
        Args:
            config_path: Путь к конфигурации 1С
        
        Returns:
            Dict с результатами бенчмарка
        """
        logger.info("Running benchmark...")
        
        results = {
            "model": self.model_name,
            "device": self.device,
            "use_4bit": self.use_4bit,
            "config_path": config_path,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        
        # Загружаем конфигурацию
        try:
            code = self.load_1c_configuration(config_path)
            results["code_length"] = len(code)
            results["code_lines"] = len(code.split('\n'))
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            results["error"] = str(e)
            return results
        
        # Задачи для анализа (типичные для 1С)
        tasks = [
            "Найди все взаимосвязи между модулями",
            "Выяви циклические зависимости",
            "Найди дублирование кода",
            "Предложи оптимизации производительности",
            "Найди потенциальные проблемы безопасности",
        ]
        
        # Анализ
        try:
            analysis = self.analyze_configuration(code, tasks)
            results.update(analysis)
            results["status"] = "success"
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            results["error"] = str(e)
            results["status"] = "failed"
        
        return results
    
    def evaluate_viability(self, benchmark_results: Dict) -> Dict:
        """
        Оценка целесообразности использования Kimi-Linear-48B
        
        Args:
            benchmark_results: Результаты бенчмарка
        
        Returns:
            Dict с оценкой и рекомендациями
        """
        logger.info("Evaluating model viability...")
        
        evaluation = {
            "model": self.model_name,
            "verdict": "unknown",
            "scores": {},
            "pros": [],
            "cons": [],
            "recommendations": [],
        }
        
        if benchmark_results.get("status") != "success":
            evaluation["verdict"] = "failed"
            evaluation["recommendations"].append("Модель не смогла обработать конфигурацию")
            return evaluation
        
        # Критерии оценки
        
        # 1. Скорость генерации
        tokens_per_sec = benchmark_results.get("tokens_per_sec", 0)
        if tokens_per_sec > 10:
            evaluation["scores"]["speed"] = "excellent"
            evaluation["pros"].append(f"Быстрая генерация: {tokens_per_sec:.1f} tokens/s")
        elif tokens_per_sec > 5:
            evaluation["scores"]["speed"] = "good"
            evaluation["pros"].append(f"Приемлемая скорость: {tokens_per_sec:.1f} tokens/s")
        else:
            evaluation["scores"]["speed"] = "poor"
            evaluation["cons"].append(f"Медленная генерация: {tokens_per_sec:.1f} tokens/s")
        
        # 2. Размер контекста
        input_tokens = benchmark_results.get("input_tokens", 0)
        if input_tokens > 100000:
            evaluation["scores"]["context"] = "excellent"
            evaluation["pros"].append(f"Обработка огромных контекстов: {input_tokens:,} tokens")
        elif input_tokens > 50000:
            evaluation["scores"]["context"] = "good"
            evaluation["pros"].append(f"Обработка больших контекстов: {input_tokens:,} tokens")
        else:
            evaluation["scores"]["context"] = "average"
        
        # 3. Время генерации
        generation_time = benchmark_results.get("generation_time", 0)
        if generation_time < 30:
            evaluation["scores"]["latency"] = "excellent"
            evaluation["pros"].append(f"Низкая латентность: {generation_time:.1f}s")
        elif generation_time < 60:
            evaluation["scores"]["latency"] = "good"
        else:
            evaluation["scores"]["latency"] = "poor"
            evaluation["cons"].append(f"Высокая латентность: {generation_time:.1f}s")
        
        # 4. Качество ответа
        response_length = len(benchmark_results.get("response", ""))
        if response_length > 500:
            evaluation["scores"]["quality"] = "good"
            evaluation["pros"].append("Детальный ответ")
        elif response_length > 100:
            evaluation["scores"]["quality"] = "average"
        else:
            evaluation["scores"]["quality"] = "poor"
            evaluation["cons"].append("Краткий/неполный ответ")
        
        # Итоговая оценка
        scores_values = {
            "excellent": 3,
            "good": 2,
            "average": 1,
            "poor": 0,
        }
        
        total_score = sum(scores_values.get(v, 0) for v in evaluation["scores"].values())
        max_score = len(evaluation["scores"]) * 3
        
        score_percentage = (total_score / max_score * 100) if max_score > 0 else 0
        
        if score_percentage >= 75:
            evaluation["verdict"] = "recommended"
            evaluation["recommendations"].append("✅ РЕКОМЕНДУЕТСЯ для анализа больших конфигураций")
        elif score_percentage >= 50:
            evaluation["verdict"] = "conditional"
            evaluation["recommendations"].append("⚠️ УСЛОВНО РЕКОМЕНДУЕТСЯ - только для specific use cases")
        else:
            evaluation["verdict"] = "not_recommended"
            evaluation["recommendations"].append("❌ НЕ РЕКОМЕНДУЕТСЯ - используйте текущий стек")
        
        # Дополнительные рекомендации
        if self.device == "cpu":
            evaluation["recommendations"].append("💡 GPU значительно ускорит работу")
        
        if input_tokens < 50000:
            evaluation["recommendations"].append("💡 Для конфигураций <50K токенов Qwen-Coder достаточно")
        
        return evaluation


def main():
    """Главная функция"""
    
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║  Kimi-Linear-48B Test for 1C Configurations              ║
    ║  Тестирование на больших конфигурациях 1С                 ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    # Параметры
    CONFIG_PATH = os.getenv("CONFIG_PATH", "./1c_configurations/ERP")
    USE_4BIT = os.getenv("USE_4BIT", "true").lower() == "true"
    OUTPUT_FILE = os.getenv("OUTPUT_FILE", "./kimi_test_results.json")
    
    logger.info("Configuration:")
    logger.info(f"  CONFIG_PATH: {CONFIG_PATH}")
    logger.info(f"  USE_4BIT: {USE_4BIT}")
    logger.info(f"  OUTPUT_FILE: {OUTPUT_FILE}")
    
    # Проверка наличия конфигурации
    if not Path(CONFIG_PATH).exists():
        logger.error(f"Configuration path not found: {CONFIG_PATH}")
        logger.info("Please provide a valid 1C configuration path via CONFIG_PATH env variable")
        sys.exit(1)
    
    # Инициализация тестера
    tester = KimiLinear48BTest(use_4bit=USE_4BIT)
    
    # Загрузка модели
    try:
        tester.load_model()
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        logger.info("This may be due to:")
        logger.info("  - Model not available on HuggingFace")
        logger.info("  - Insufficient memory")
        logger.info("  - Missing dependencies")
        sys.exit(1)
    
    # Запуск бенчмарка
    logger.info("\n" + "="*60)
    logger.info("RUNNING BENCHMARK")
    logger.info("="*60 + "\n")
    
    benchmark_results = tester.run_benchmark(CONFIG_PATH)
    
    # Оценка целесообразности
    evaluation = tester.evaluate_viability(benchmark_results)
    
    # Объединяем результаты
    final_results = {
        "benchmark": benchmark_results,
        "evaluation": evaluation
    }
    
    # Сохраняем результаты
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(final_results, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n✓ Results saved to: {OUTPUT_FILE}")
    
    # Выводим итоги
    print("\n" + "="*60)
    print("EVALUATION RESULTS")
    print("="*60)
    print(f"\nModel: {evaluation['model']}")
    print(f"Verdict: {evaluation['verdict'].upper()}")
    print(f"\nScores:")
    for criterion, score in evaluation['scores'].items():
        print(f"  - {criterion}: {score}")
    
    print(f"\nPros:")
    for pro in evaluation['pros']:
        print(f"  ✅ {pro}")
    
    print(f"\nCons:")
    for con in evaluation['cons']:
        print(f"  ❌ {con}")
    
    print(f"\nRecommendations:")
    for rec in evaluation['recommendations']:
        print(f"  {rec}")
    
    print("="*60)
    
    # Exit code
    if evaluation['verdict'] in ['recommended', 'conditional']:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()





