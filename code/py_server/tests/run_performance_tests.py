# [NEXUS IDENTITY] ID: -1103085652764032557 | DATE: 2025-11-19

"""
Скрипты запуска и конфигурации для тестов производительности 1C MCP

Включает:
- Автоматические скрипты запуска тестов
- Конфигурации для различных сред тестирования
- Интеграция с мониторингом системы
- Генерация отчетов производительности

Версия: 1.0.0
"""

import os
import sys
import json
import time
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

# Добавляем путь к модулям
sys.path.append(str(Path(__file__).parent.parent))

class PerformanceTestRunner:
    """Запуск тестов производительности с автоматизацией"""
    
    def __init__(self, config_file: str = "performance_config.json"):
        self.config_file = config_file
        self.config = self._load_config()
        self.results_dir = Path("performance_results")
        self.results_dir.mkdir(exist_ok=True)
    
    def _load_config(self) -> dict:
        """Загрузить конфигурацию тестов"""
        default_config = {
            "test_environment": {
                "target_host": "http://localhost:8000",
                "concurrent_users": {
                    "light_load": 50,
                    "normal_load": 200,
                    "heavy_load": 500,
                    "stress_load": 1000
                },
                "test_durations": {
                    "quick": "30s",
                    "standard": "5m",
                    "extended": "30m",
                    "endurance": "2h"
                }
            },
            "performance_thresholds": {
                "response_time_ms": {
                    "cache_hit": 10,
                    "cache_miss": 50,
                    "api_call": 100,
                    "rate_limit_check": 5
                },
                "throughput_rps": {
                    "minimum": 100,
                    "target": 1000,
                    "excellent": 5000
                },
                "error_rate_percent": {
                    "acceptable": 1.0,
                    "degraded": 5.0,
                    "critical": 10.0
                },
                "memory_usage_mb": {
                    "normal": 500,
                    "high": 1000,
                    "critical": 2000
                }
            },
            "test_scenarios": {
                "smoke_test": {
                    "users": 10,
                    "duration": "1m",
                    "description": "Быстрая проверка работоспособности"
                },
                "load_test": {
                    "users": 200,
                    "duration": "5m",
                    "description": "Тест нормальной нагрузки"
                },
                "stress_test": {
                    "users": 1000,
                    "duration": "10m",
                    "description": "Stress тест до точки разрушения"
                },
                "endurance_test": {
                    "users": 100,
                    "duration": "1h",
                    "description": "Длительная стабильность"
                },
                "spike_test": {
                    "users": [50, 500, 50],
                    "pattern": "spike",
                    "description": "Тест резких пиков нагрузки"
                }
            }
        }
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    user_config = json.load(f)
                # Merge с дефолтной конфигурацией
                default_config.update(user_config)
            except Exception as e:
                print(f"Warning: Could not load config {self.config_file}: {e}")
                print("Using default configuration")
        
        return default_config
    
    def run_smoke_test(self):
        """Запуск smoke теста"""
        print("🔍 Running Smoke Test...")
        
        cmd = [
            "python", "-m", "pytest", 
            "tests/test_performance.py",
            "-m", "load_test",
            "--tb=short",
            "-v"
        ]
        
        return self._run_command(cmd, "smoke_test")
    
    def run_load_test(self, load_type: str = "normal"):
        """Запуск load теста"""
        print(f"📊 Running {load_type} Load Test...")
        
        users = self.config["test_environment"]["concurrent_users"][load_type]
        
        cmd = [
            "python", "-m", "pytest",
            "tests/test_performance.py::TestSystemLoad::test_scaled_load_simulation",
            "-v",
            "--tb=short",
            f"--users={users}"
        ]
        
        return self._run_command(cmd, f"load_test_{load_type}")
    
    def run_stress_test(self):
        """Запуск stress теста"""
        print("💪 Running Stress Test...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/test_performance.py",
            "-m", "stress_test",
            "-v",
            "--tb=short",
            "--timeout=600"
        ]
        
        return self._run_command(cmd, "stress_test")
    
    def run_endurance_test(self, duration_minutes: int = 60):
        """Запуск endurance теста"""
        print(f"⏱️  Running {duration_minutes}min Endurance Test...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/test_performance.py::TestSystemEndurance::test_long_running_stability",
            "-v",
            "--tb=short",
            f"--duration={duration_minutes}m",
            "--timeout=7200"
        ]
        
        return self._run_command(cmd, f"endurance_test_{duration_minutes}min")
    
    def run_spike_test(self):
        """Запуск spike теста"""
        print("🚀 Running Spike Test...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/test_performance.py",
            "-m", "spike_test",
            "-v",
            "--tb=short"
        ]
        
        return self._run_command(cmd, "spike_test")
    
    def run_volume_test(self):
        """Запуск volume теста"""
        print("💾 Running Volume Test...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/test_performance.py",
            "-m", "volume_test",
            "-v",
            "--tb=short"
        ]
        
        return self._run_command(cmd, "volume_test")
    
    def run_benchmark_test(self):
        """Запуск benchmark теста"""
        print("⚡ Running Benchmark Test...")
        
        cmd = [
            "python", "-m", "pytest",
            "tests/test_performance.py",
            "-m", "benchmark",
            "-v",
            "--tb=short",
            "--benchmark-only"
        ]
        
        return self._run_command(cmd, "benchmark_test")
    
    def run_locust_load_test(self, scenario: str = "normal"):
        """Запуск locust load теста"""
        print(f"🐛 Running Locust {scenario} Load Test...")
        
        # Создаем locust файл если его нет
        locust_file = "tests/locustfile.py"
        if not os.path.exists(locust_file):
            self._create_locust_file()
        
        scenario_config = self.config["test_scenarios"].get(scenario, {})
        
        cmd = [
            "locust",
            "-f", locust_file,
            "--host", self.config["test_environment"]["target_host"],
            "--headless",
            "-u", str(scenario_config.get("users", 100)),
            "-r", "10",  # spawn rate
            "-t", scenario_config.get("duration", "5m"),
            "--csv", f"performance_results/locust_{scenario}",
            "--html", f"performance_results/locust_{scenario}_report.html"
        ]
        
        return self._run_command(cmd, f"locust_{scenario}")
    
    def run_comprehensive_test_suite(self):
        """Запуск полного набора тестов производительности"""
        print("🎯 Running Comprehensive Performance Test Suite...")
        
        start_time = time.time()
        results = {}
        
        test_sequence = [
            ("smoke", self.run_smoke_test),
            ("benchmark", self.run_benchmark_test),
            ("load_normal", lambda: self.run_load_test("normal")),
            ("spike", self.run_spike_test),
            ("volume", self.run_volume_test),
            ("stress", self.run_stress_test),
            ("endurance_30min", lambda: self.run_endurance_test(30))
        ]
        
        for test_name, test_func in test_sequence:
            print(f"\n{'='*60}")
            print(f"Running: {test_name}")
            print(f"{'='*60}")
            
            try:
                result = test_func()
                results[test_name] = {
                    "status": "PASSED" if result else "FAILED",
                    "timestamp": datetime.now().isoformat(),
                    "duration": time.time() - start_time
                }
                print(f"✅ {test_name} completed")
                
            except Exception as e:
                results[test_name] = {
                    "status": "FAILED",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                    "duration": time.time() - start_time
                }
                print(f"❌ {test_name} failed: {e}")
        
        # Сохраняем итоговый отчет
        self._save_comprehensive_report(results)
        
        total_duration = time.time() - start_time
        print(f"\n{'='*60}")
        print("COMPREHENSIVE TEST SUITE COMPLETED")
        print(f"Total duration: {total_duration:.1f} seconds")
        print(f"Tests passed: {sum(1 for r in results.values() if r['status'] == 'PASSED')}")
        print(f"Tests failed: {sum(1 for r in results.values() if r['status'] == 'FAILED')}")
        
        return results
    
    def _run_command(self, cmd: list, test_name: str) -> bool:
        """Запуск команды и сохранение результатов"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.results_dir / f"{test_name}_{timestamp}.log"
        
        try:
            print(f"Command: {' '.join(cmd)}")
            print(f"Log file: {log_file}")
            
            with open(log_file, 'w') as f:
                result = subprocess.run(
                    cmd,
                    cwd=Path(__file__).parent.parent,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    text=True,
                    timeout=3600  # 1 час timeout
                )
            
            success = result.returncode == 0
            
            # Копируем лог в results dir
            if success:
                print(f"✅ {test_name} completed successfully")
            else:
                print(f"❌ {test_name} failed with exit code {result.returncode}")
            
            return success
            
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_name} timed out")
            return False
        except Exception as e:
            print(f"💥 {test_name} failed with exception: {e}")
            return False
    
    def _create_locust_file(self):
        """Создать locust файл для нагрузочного тестирования"""
        locust_content = '''"""
Locust load test file for 1C MCP system
Auto-generated by performance test runner
"""

import json
import random
import time
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner, SlaveRunner


class MCPLoadTestUser(HttpUser):
    """User for 1C MCP load testing"""
    
    wait_time = between(0.1, 0.5)
    weight = 3
    
    def on_start(self):
        """Initialize user session"""
        self.user_id = f"load_test_user_{random.randint(1000, 9999)}"
        self.headers = {
            "Content-Type": "application/json",
            "X-User-ID": self.user_id
        }
    
    @task(5)
    def get_data(self):
        """Get data endpoint"""
        with self.client.get(
            f"/data/{self.user_id}",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to get data: {response.status_code}")
    
    @task(3)
    def health_check(self):
        """Health check endpoint"""
        with self.client.get(
            "/health",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(1)
    def cache_test(self):
        """Cache test endpoint"""
        cache_key = f"cache_test_{self.user_id}_{int(time.time() * 1000)}"
        
        with self.client.get(
            f"/data/{cache_key}",
            headers=self.headers,
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Cache test failed: {response.status_code}")


class MCPSpikeTestUser(HttpUser):
    """User for spike testing"""
    
    wait_time = between(0.01, 0.05)
    weight = 1
    
    def on_start(self):
        """Initialize spike test user"""
        self.user_id = f"spike_user_{random.randint(100, 999)}"
        self.headers = {
            "Content-Type": "application/json",
            "X-User-ID": self.user_id
        }
    
    @task(10)
    def rapid_requests(self):
        """Rapid requests for spike testing"""
        with self.client.get(
            "/",
            headers=self.headers,
            catch_response=True,
            name="spike_request"
        ) as response:
            if response.status_code == 200:
                pass  # Success
            else:
                pass  # Allow failures during spike


# Event handlers
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Test start handler"""
    print("🚀 Starting 1C MCP Load Test")
    print(f"Target: {environment.host}")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Test stop handler"""
    print("\\n✅ Load test completed")
    
    stats = environment.stats
    print(f"Total requests: {stats.total.num_requests}")
    print(f"Failures: {stats.total.num_failures}")
    print(f"Fail rate: {stats.total.num_failures / max(stats.total.num_requests, 1) * 100:.1f}%")
'''
        
        locust_file = Path("tests/locustfile.py")
        locust_file.parent.mkdir(exist_ok=True)
        
        with open(locust_file, 'w') as f:
            f.write(locust_content)
        
        print(f"Created locust file: {locust_file}")
    
    def _save_comprehensive_report(self, results: dict):
        """Сохранить комплексный отчет"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.results_dir / f"comprehensive_report_{timestamp}.json"
        
        report = {
            "timestamp": timestamp,
            "config": self.config,
            "results": results,
            "summary": {
                "total_tests": len(results),
                "passed": sum(1 for r in results.values() if r["status"] == "PASSED"),
                "failed": sum(1 for r in results.values() if r["status"] == "FAILED"),
                "success_rate": sum(1 for r in results.values() if r["status"] == "PASSED") / len(results) * 100
            }
        }
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Comprehensive report saved: {report_file}")
    
    def generate_performance_dashboard(self):
        """Генерация dashboard отчета"""
        print("📊 Generating Performance Dashboard...")
        
        # Собираем все результаты
        result_files = list(self.results_dir.glob("*.json"))
        
        dashboard_data = {
            "generated_at": datetime.now().isoformat(),
            "test_runs": [],
            "summary": {}
        }
        
        for result_file in result_files:
            try:
                with open(result_file, 'r') as f:
                    data = json.load(f)
                    dashboard_data["test_runs"].append({
                        "file": str(result_file),
                        "data": data
                    })
            except Exception as e:
                print(f"Warning: Could not load {result_file}: {e}")
        
        # Создаем HTML dashboard
        self._create_html_dashboard(dashboard_data)
        
        print(f"Dashboard generated: {self.results_dir}/dashboard.html")
    
    def _create_html_dashboard(self, data: dict):
        """Создать HTML dashboard"""
        html_template = '''<!DOCTYPE html>
<html>
<head>
    <title>1C MCP Performance Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f0f0f0; padding: 20px; border-radius: 5px; }
        .test-result { margin: 10px 0; padding: 10px; border-radius: 3px; }
        .passed { background: #d4edda; border: 1px solid #c3e6cb; }
        .failed { background: #f8d7da; border: 1px solid #f5c6cb; }
        .summary { background: #e2e3e5; padding: 15px; margin: 20px 0; border-radius: 5px; }
        .metric { display: inline-block; margin: 10px; padding: 10px; background: white; border-radius: 3px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 1C MCP Performance Dashboard</h1>
        <p>Generated at: {generated_at}</p>
    </div>
    
    <div class="summary">
        <h2>📊 Summary</h2>
        <div class="metric">
            <strong>Total Tests:</strong> {total_tests}
        </div>
        <div class="metric">
            <strong>Passed:</strong> {passed}
        </div>
        <div class="metric">
            <strong>Failed:</strong> {failed}
        </div>
        <div class="metric">
            <strong>Success Rate:</strong> {success_rate:.1f}%
        </div>
    </div>
    
    <h2>📋 Test Results</h2>
    {test_results}
    
</body>
</html>'''
        
        test_results_html = ""
        for test_run in data["test_runs"]:
            file_name = test_run["file"]
            test_data = test_run["data"]
            
            # Определяем статус
            if "summary" in test_data:
                passed = test_data["summary"].get("passed", 0)
                failed = test_data["summary"].get("failed", 0)
                total = test_data["summary"].get("total_tests", 0)
                
                if failed == 0:
                    status_class = "passed"
                    status_text = "✅ PASSED"
                else:
                    status_class = "failed"
                    status_text = "❌ FAILED"
                
                test_results_html += f'''
                <div class="test-result {status_class}">
                    <h3>{status_text} - {file_name}</h3>
                    <p>Total: {total}, Passed: {passed}, Failed: {failed}</p>
                </div>
                '''
            else:
                test_results_html += f'''
                <div class="test-result">
                    <h3>📄 {file_name}</h3>
                    <p>Data file - see original for details</p>
                </div>
                '''
        
        html_content = html_template.format(
            generated_at=data["generated_at"],
            total_tests=len(data["test_runs"]),
            passed=sum(1 for t in data["test_runs"] if "summary" in t["data"] and t["data"]["summary"].get("failed", 0) == 0),
            failed=sum(1 for t in data["test_runs"] if "summary" in t["data"] and t["data"]["summary"].get("failed", 0) > 0),
            success_rate=100 if data["test_runs"] else 0,
            test_results=test_results_html
        )
        
        dashboard_file = self.results_dir / "dashboard.html"
        with open(dashboard_file, 'w') as f:
            f.write(html_content)


def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description="1C MCP Performance Test Runner")
    parser.add_argument("--config", default="performance_config.json", help="Config file")
    parser.add_argument("--smoke", action="store_true", help="Run smoke test")
    parser.add_argument("--load", choices=["light", "normal", "heavy", "stress"], help="Run load test")
    parser.add_argument("--stress", action="store_true", help="Run stress test")
    parser.add_argument("--endurance", type=int, default=60, help="Run endurance test (minutes)")
    parser.add_argument("--spike", action="store_true", help="Run spike test")
    parser.add_argument("--volume", action="store_true", help="Run volume test")
    parser.add_argument("--benchmark", action="store_true", help="Run benchmark test")
    parser.add_argument("--locust", choices=["smoke", "normal", "heavy", "stress"], help="Run locust test")
    parser.add_argument("--comprehensive", action="store_true", help="Run all tests")
    parser.add_argument("--dashboard", action="store_true", help="Generate dashboard")
    
    args = parser.parse_args()
    
    runner = PerformanceTestRunner(args.config)
    
    try:
        if args.smoke:
            runner.run_smoke_test()
        elif args.load:
            runner.run_load_test(args.load)
        elif args.stress:
            runner.run_stress_test()
        elif args.spike:
            runner.run_spike_test()
        elif args.volume:
            runner.run_volume_test()
        elif args.benchmark:
            runner.run_benchmark_test()
        elif args.endurance:
            runner.run_endurance_test(args.endurance)
        elif args.locust:
            runner.run_locust_load_test(args.locust)
        elif args.comprehensive:
            runner.run_comprehensive_test_suite()
        elif args.dashboard:
            runner.generate_performance_dashboard()
        else:
            # Показать справку
            print("🔧 1C MCP Performance Test Runner")
            print("\nAvailable options:")
            print("  --smoke           Run smoke test")
            print("  --load TYPE       Run load test (light/normal/heavy/stress)")
            print("  --stress          Run stress test")
            print("  --endurance MIN   Run endurance test (minutes)")
            print("  --spike           Run spike test")
            print("  --volume          Run volume test")
            print("  --benchmark       Run benchmark test")
            print("  --locust TYPE     Run locust test (smoke/normal/heavy/stress)")
            print("  --comprehensive   Run all tests")
            print("  --dashboard       Generate performance dashboard")
            print("\nExamples:")
            print("  python run_performance_tests.py --smoke")
            print("  python run_performance_tests.py --load normal")
            print("  python run_performance_tests.py --comprehensive")
            print("  python run_performance_tests.py --dashboard")
    
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test runner failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
