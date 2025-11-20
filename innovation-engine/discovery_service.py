# [NEXUS IDENTITY] ID: 3407863370305533255 | DATE: 2025-11-19

"""
Discovery Service - Automatic discovery of new 1C projects and technologies
Stage 5: Continuous Innovation Engine
"""

import os
import logging
import asyncio
import aiohttp
from typing import List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

try:
    from github import Github
    GITHUB_AVAILABLE = True
except ImportError:
    logger.warning("PyGithub not installed. Run: pip install PyGithub")
    GITHUB_AVAILABLE = False


class GitHubMonitor:
    """Monitors GitHub for new 1C-related projects"""
    
    def __init__(self, token: str = None):
        if not GITHUB_AVAILABLE:
            raise ImportError("PyGithub not available")
        
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            logger.warning("GITHUB_TOKEN not set, rate limits will be low")
        
        self.client = Github(self.token) if self.token else Github()
    
    async def search_projects(self, since_days: int = 7) -> List[Dict[str, Any]]:
        """Search for new 1C projects"""
        
        since_date = datetime.now() - timedelta(days=since_days)
        
        queries = [
            "1C language:1c-enterprise",
            "BSL language:1c-enterprise",
            "EDT 1C stars:>10",
            "1С автоматизация",
            "BSL-Language-Server",
            "1C plugin",
            "1C parser",
            "Neo4j 1C",
            "MCP 1C"
        ]
        
        results = []
        
        for query in queries:
            try:
                repos = self.client.search_repositories(
                    query=f"{query} created:>{since_date.isoformat()}",
                    sort='stars',
                    order='desc'
                )
                
                for repo in repos[:10]:  # Top 10 per query
                    try:
                        project_info = {
                            'name': repo.name,
                            'full_name': repo.full_name,
                            'url': repo.html_url,
                            'description': repo.description,
                            'stars': repo.stargazers_count,
                            'forks': repo.forks_count,
                            'language': repo.language,
                            'topics': repo.get_topics(),
                            'last_commit': repo.updated_at.isoformat(),
                            'license': repo.license.name if repo.license else None,
                            'readme_url': f"{repo.html_url}/blob/main/README.md",
                            'discovered_at': datetime.now().isoformat(),
                            'source': 'github'
                        }
                        
                        # Try to fetch README
                        try:
                            readme = repo.get_readme()
                            project_info['readme'] = readme.decoded_content.decode('utf-8')[:5000]
                        except:
                            project_info['readme'] = None
                        
                        results.append(project_info)
                        
                    except Exception as e:
                        logger.warning(f"Error processing repo {repo.name}: {e}")
                        continue
                
            except Exception as e:
                logger.error(f"Error searching query '{query}': {e}")
                continue
        
        # Deduplicate by URL
        unique_results = {p['url']: p for p in results}.values()
        
        logger.info(f"Discovered {len(unique_results)} unique projects")
        
        return list(unique_results)


class OpenYellowCrawler:
    """Crawls OpenYellow.org for 1C projects"""
    
    BASE_URL = "https://openyellow.org"
    
    async def search_projects(self, since_days: int = 7) -> List[Dict[str, Any]]:
        """Search OpenYellow for new projects"""
        
        # Note: OpenYellow doesn't have public API
        # Would need to parse HTML or wait for API
        
        logger.info("OpenYellow crawler not yet implemented (no public API)")
        return []


class InfostartParser:
    """Parses Infostart.ru for new articles and projects"""
    
    RSS_URL = "https://infostart.ru/rss/journal/"
    
    async def search_articles(self, since_days: int = 7) -> List[Dict[str, Any]]:
        """Parse RSS feed for new articles"""
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.RSS_URL) as response:
                    if response.status == 200:
                        # TODO: Parse RSS XML
                        # For now, return empty
                        logger.info("Infostart RSS parser not yet fully implemented")
                        return []
                    else:
                        logger.error(f"Failed to fetch RSS: {response.status}")
                        return []
        except Exception as e:
            logger.error(f"Error fetching Infostart RSS: {e}")
            return []


class DiscoveryService:
    """Main discovery service that coordinates all monitors"""
    
    def __init__(self):
        self.monitors = []
        
        # Initialize monitors
        try:
            github_monitor = GitHubMonitor()
            self.monitors.append(('GitHub', github_monitor))
        except Exception as e:
            logger.warning(f"GitHub monitor not available: {e}")
        
        try:
            openyellow_crawler = OpenYellowCrawler()
            self.monitors.append(('OpenYellow', openyellow_crawler))
        except Exception as e:
            logger.warning(f"OpenYellow crawler not available: {e}")
        
        try:
            infostart_parser = InfostartParser()
            self.monitors.append(('Infostart', infostart_parser))
        except Exception as e:
            logger.warning(f"Infostart parser not available: {e}")
    
    async def discover_new_projects(self, since_days: int = 7) -> List[Dict[str, Any]]:
        """Run discovery across all monitors"""
        
        logger.info(f"="*60)
        logger.info(f"Running discovery (last {since_days} days)")
        logger.info(f"="*60)
        
        all_projects = []
        
        # Run all monitors in parallel
        tasks = []
        for name, monitor in self.monitors:
            if hasattr(monitor, 'search_projects'):
                tasks.append(monitor.search_projects(since_days))
            elif hasattr(monitor, 'search_articles'):
                tasks.append(monitor.search_articles(since_days))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    all_projects.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"Monitor error: {result}")
        
        logger.info(f"\nTotal projects discovered: {len(all_projects)}")
        
        return all_projects


async def main():
    """Test discovery service"""
    service = DiscoveryService()
    projects = await service.discover_new_projects(since_days=7)
    
    print(f"\nDiscovered {len(projects)} projects:")
    for p in projects[:5]:
        print(f"  - {p['name']}: {p['stars']} stars ({p['source']})")


if __name__ == "__main__":
    asyncio.run(main())







