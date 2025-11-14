"""
BSL Dataset Preparer
Подготовка dataset для fine-tuning на BSL
"""

import os
import json
from typing import List, Dict
from pathlib import Path
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger


class BSLDatasetPreparer:
    """
    Подготовка датасета для обучения модели на BSL
    
    Sources:
    1. GitHub (public 1C projects)
    2. ИТС examples
    3. Internal projects (if available)
    """
    
    def __init__(self, output_dir: str = "datasets/bsl"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.examples = []
    
    async def prepare_dataset_from_db(self):
        """
        Подготовка dataset из PostgreSQL
        
        Извлекаем:
        - Функции и процедуры
        - С документацией
        - С примерами использования
        """
        
        # TODO: Connect to PostgreSQL
        # For now - create sample dataset
        
        self.examples = [
            {
                'instruction': 'Создай функцию для расчета НДС',
                'input': 'Параметры: Сумма (число), СтавкаНДС (число, по умолчанию 20)',
                'output': '''
// Рассчитывает НДС от суммы
//
// Параметры:
//   Сумма - Число - Сумма без НДС
//   СтавкаНДС - Число - Ставка НДС в процентах (по умолчанию 20)
//
// Возвращаемое значение:
//   Число - Сумма НДС
//
Функция РассчитатьНДС(Сумма, СтавкаНДС = 20) Экспорт
    
    Если НЕ ЗначениеЗаполнено(Сумма) Тогда
        Возврат 0;
    КонецЕсли;
    
    СуммаНДС = Сумма * СтавкаНДС / 100;
    
    Возврат Окр(СуммаНДС, 2);
    
КонецФункции
'''
            },
            {
                'instruction': 'Напиши функцию для проверки ИНН',
                'input': 'Проверка контрольной суммы для 10 и 12 символов',
                'output': '''
// Проверяет корректность ИНН
//
// Параметры:
//   ИНН - Строка - ИНН для проверки
//
// Возвращаемое значение:
//   Булево - Истина если ИНН корректный
//
Функция ПроверитьИНН(ИНН) Экспорт
    
    Если НЕ ЗначениеЗаполнено(ИНН) Тогда
        Возврат Ложь;
    КонецЕсли;
    
    Длина = СтрДлина(ИНН);
    
    Если Длина <> 10 И Длина <> 12 Тогда
        Возврат Ложь;
    КонецЕсли;
    
    // Проверка что все символы - цифры
    Для Индекс = 1 По Длина Цикл
        Символ = Сред(ИНН, Индекс, 1);
        Если НЕ (Символ >= "0" И Символ <= "9") Тогда
            Возврат Ложь;
        КонецЕсли;
    КонецЦикла;
    
    // Проверка контрольных сумм
    // Упрощенная версия - в production полная проверка
    
    Возврат Истина;
    
КонецФункции
'''
            },
            {
                'instruction': 'Создай процедуру для записи в журнал регистрации',
                'input': 'Уровень, событие, комментарий',
                'output': '''
Процедура ЗаписатьВЖурнал(Уровень, Событие, Комментарий) Экспорт
    
    ЗаписьЖурналаРегистрации(
        Событие,
        Уровень,
        ,
        ,
        Комментарий
    );
    
КонецПроцедуры
'''
            }
        ]
        
        logger.info(
            "Prepared examples",
            extra={"examples_count": len(self.examples)}
        )
    
    def prepare_single_sample(self, code: str, description: str) -> Dict[str, str]:
        """
        Формирует единственную запись датасета в формате instruction/input/output.
        """
        entry = {
            "instruction": description.strip(),
            "input": code.strip(),
            "output": code.strip(),
        }
        self.examples.append(entry)
        return entry
    
    def save_dataset(self, format: str = 'jsonl'):
        """
        Сохранение dataset
        
        Formats:
        - jsonl: для fine-tuning (Hugging Face format)
        - json: для общего использования
        """
        
        if format == 'jsonl':
            output_file = self.output_dir / "bsl_train.jsonl"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                for example in self.examples:
                    # Hugging Face format
                    line = json.dumps({
                        'text': f"### Instruction:\n{example['instruction']}\n\n### Input:\n{example['input']}\n\n### Response:\n{example['output']}"
                    }, ensure_ascii=False)
                    f.write(line + '\n')
            
            logger.info(
                "Dataset saved",
                extra={"output_file": str(output_file), "format": "jsonl"}
            )
        
        else:
            output_file = self.output_dir / "bsl_train.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.examples, f, ensure_ascii=False, indent=2)
            
            logger.info(
                "Dataset saved",
                extra={"output_file": str(output_file), "format": "json"}
            )
        
        return str(output_file)


# CLI usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        preparer = BSLDatasetPreparer()
        await preparer.prepare_dataset_from_db()
        
        # Save in both formats
        preparer.save_dataset('jsonl')
        preparer.save_dataset('json')
        
        print(f"Dataset готов! {len(preparer.examples)} examples")
    
    asyncio.run(main())


