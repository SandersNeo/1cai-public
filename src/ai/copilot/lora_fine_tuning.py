"""
LoRA Fine-Tuning Pipeline
Обучение Qwen3-Coder на BSL с использованием LoRA
"""

import os
from pathlib import Path
from typing import Optional
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class LoRAFineTuner:
    """
    LoRA Fine-Tuning для BSL
    
    Обучает Qwen3-Coder понимать BSL лучше
    Используя LoRA (Low-Rank Adaptation) - эффективный метод
    """
    
    def __init__(
        self,
        base_model: str = "Qwen/Qwen2.5-Coder-7B-Instruct",
        output_dir: str = "models/qwen-bsl-lora"
    ):
        self.base_model = base_model
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check dependencies
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Проверка необходимых библиотек"""
        
        required = ['transformers', 'peft', 'torch', 'datasets']
        missing = []
        
        for lib in required:
            try:
                __import__(lib)
            except ImportError:
                missing.append(lib)
        
        if missing:
            logger.warning(
                "Missing dependencies",
                extra={"missing": missing}
            )
            logger.info("Install: pip install transformers peft torch datasets")
    
    async def fine_tune(
        self,
        dataset_path: str,
        epochs: int = 3,
        learning_rate: float = 2e-4,
        batch_size: int = 4
    ) -> dict:
        """
        Fine-tuning с LoRA
        
        Args:
            dataset_path: Путь к .jsonl dataset
            epochs: Количество эпох
            learning_rate: Learning rate
            batch_size: Batch size
        
        Returns:
            Training metrics
        """
        
        logger.info(
            "Starting LoRA fine-tuning",
            extra={"base_model": self.base_model}
        )
        
        try:
            from transformers import (
                AutoModelForCausalLM,
                AutoTokenizer,
                TrainingArguments,
                Trainer
            )
            from peft import LoraConfig, get_peft_model, TaskType
            from datasets import load_dataset
            import torch
            
            # 1. Load base model
            logger.info("Loading base model...")
            model = AutoModelForCausalLM.from_pretrained(
                self.base_model,
                torch_dtype=torch.float16,
                device_map="auto",
                trust_remote_code=True
            )
            
            tokenizer = AutoTokenizer.from_pretrained(
                self.base_model,
                trust_remote_code=True
            )
            
            # 2. Configure LoRA
            logger.info("Configuring LoRA...")
            lora_config = LoraConfig(
                r=16,                    # LoRA rank
                lora_alpha=32,           # Scaling factor
                target_modules=[         # Which layers to adapt
                    "q_proj",
                    "v_proj",
                    "k_proj",
                    "o_proj"
                ],
                lora_dropout=0.05,
                bias="none",
                task_type=TaskType.CAUSAL_LM
            )
            
            # 3. Apply LoRA to model
            model = get_peft_model(model, lora_config)
            model.print_trainable_parameters()
            
            # 4. Load dataset
            logger.info(
                "Loading dataset",
                extra={"dataset_path": dataset_path}
            )
            dataset = load_dataset('json', data_files=dataset_path)
            
            # 5. Tokenize
            def tokenize_function(examples):
                return tokenizer(
                    examples['text'],
                    truncation=True,
                    max_length=2048,
                    padding='max_length'
                )
            
            tokenized_dataset = dataset.map(
                tokenize_function,
                batched=True,
                remove_columns=dataset['train'].column_names
            )
            
            # 6. Training arguments
            training_args = TrainingArguments(
                output_dir=str(self.output_dir),
                num_train_epochs=epochs,
                per_device_train_batch_size=batch_size,
                gradient_accumulation_steps=4,
                learning_rate=learning_rate,
                fp16=True,
                logging_steps=10,
                save_steps=100,
                evaluation_strategy="steps",
                eval_steps=100,
                save_total_limit=3,
                load_best_model_at_end=True
            )
            
            # 7. Create Trainer
            trainer = Trainer(
                model=model,
                args=training_args,
                train_dataset=tokenized_dataset['train'],
                eval_dataset=tokenized_dataset.get('validation', tokenized_dataset['train'])
            )
            
            # 8. Train!
            logger.info("Starting training...")
            train_result = trainer.train()
            
            # 9. Save LoRA adapter
            logger.info(
                "Saving LoRA adapter",
                extra={"output_dir": str(self.output_dir)}
            )
            model.save_pretrained(self.output_dir)
            tokenizer.save_pretrained(self.output_dir)
            
            return {
                'status': 'success',
                'train_loss': train_result.training_loss,
                'steps': train_result.global_step,
                'model_path': str(self.output_dir)
            }
            
        except ImportError as e:
            logger.error(
                "Missing dependencies",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return {
                'status': 'error',
                'error': 'Missing dependencies. Install: pip install transformers peft torch datasets'
            }
        except Exception as e:
            logger.error(
                "Training failed",
                extra={
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                exc_info=True
            )
            return {
                'status': 'error',
                'error': str(e)
            }


# CLI usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        tuner = LoRAFineTuner()
        
        # Prepare dataset first
        from src.ai.copilot.bsl_dataset_preparer import BSLDatasetPreparer
        
        preparer = BSLDatasetPreparer()
        await preparer.prepare_dataset_from_db()
        dataset_path = preparer.save_dataset('jsonl')
        
        print(f"Dataset prepared: {dataset_path}")
        
        # Fine-tune
        print("\nStarting fine-tuning (this may take 2-4 hours on GPU)...")
        result = await tuner.fine_tune(dataset_path)
        
        if result['status'] == 'success':
            print(f"\n✅ Fine-tuning complete!")
            print(f"   Model saved to: {result['model_path']}")
            print(f"   Training loss: {result['train_loss']:.4f}")
        else:
            print(f"\n❌ Error: {result['error']}")
    
    asyncio.run(main())


