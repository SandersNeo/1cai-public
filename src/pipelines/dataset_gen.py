import asyncio
import logging
import os
from typing import List, Dict, Any

from src.services.configuration_knowledge_base import get_knowledge_base
from src.ai.copilot.bsl_dataset_preparer import BSLDatasetPreparer
from src.utils.structured_logging import StructuredLogger

logger = StructuredLogger(__name__).logger

class DatasetPipeline:
    """
    Pipeline for generating AI datasets from live 1C configurations.
    Flow: OData -> KnowledgeBase -> Synthetic Generation -> JSONL
    """

    def __init__(self):
        self.kb = get_knowledge_base()
        self.preparer = BSLDatasetPreparer()

    async def run(self, config_name: str = "erp"):
        """
        Executes the pipeline.
        """
        logger.info(f"Starting Dataset Pipeline for {config_name}...")

        # 1. Sync with Live 1C (if configured)
        odata_url = os.getenv("ONEC_ODATA_URL")
        if odata_url:
            logger.info("Syncing with live 1C server...")
            try:
                await self.kb.sync_from_live_server(config_name, odata_url)
            except Exception as e:
                logger.error(f"Sync failed, proceeding with cached data: {e}")
        else:
            logger.warning("ONEC_ODATA_URL not set, using cached knowledge base.")

        # 2. Get Metadata from Knowledge Base
        config_info = self.kb.get_configuration_info(config_name)
        if not config_info:
            logger.error(f"Configuration {config_name} not found in Knowledge Base.")
            return

        # 3. Generate Synthetic Examples based on Metadata
        # Since OData doesn't give us full source code, we generate 
        # "correct" code examples based on the object structure we found.
        
        generated_count = 0
        
        # 3.1 Generate Query Examples for Catalogs
        # (In a real scenario, we would parse actual modules if available)
        catalogs = ["Товары", "Контрагенты", "Сотрудники"] # Mock if empty
        
        # Try to find real catalogs in KB if populated
        if "metadata_objects" in config_info and "Catalog" in config_info["metadata_objects"]:
             catalogs = [obj["name"] for obj in config_info["metadata_objects"]["Catalog"]]

        for catalog in catalogs:
            self._generate_catalog_query_example(catalog)
            self._generate_object_creation_example(catalog)
            generated_count += 2

        # 4. Save Dataset
        jsonl_path = self.preparer.save_dataset("jsonl")
        logger.info(f"Pipeline completed. Generated {generated_count} examples. Saved to {jsonl_path}")

    def _generate_catalog_query_example(self, catalog_name: str):
        """Generates a training example for querying a catalog."""
        instruction = f"Напиши запрос для выбора всех элементов справочника {catalog_name}"
        code = f"""
Запрос = Новый Запрос;
Запрос.Текст = 
    "ВЫБРАТЬ
    |	Т.Ссылка КАК Ссылка,
    |	Т.Код КАК Код,
    |	Т.Наименование КАК Наименование
    |ИЗ
    |	Справочник.{catalog_name} КАК Т
    |ГДЕ
    |	НЕ Т.ПометкаУдаления";

Результат = Запрос.Выполнить();
"""
        self.preparer.prepare_single_sample(code, instruction)

    def _generate_object_creation_example(self, catalog_name: str):
        """Generates a training example for creating a catalog item."""
        instruction = f"Создай новый элемент справочника {catalog_name} программно"
        code = f"""
НовыйЭлемент = Справочники.{catalog_name}.СоздатьЭлемент();
НовыйЭлемент.Наименование = "Новый элемент";
НовыйЭлемент.Записать();
"""
        self.preparer.prepare_single_sample(code, instruction)

if __name__ == "__main__":
    pipeline = DatasetPipeline()
    asyncio.run(pipeline.run())
