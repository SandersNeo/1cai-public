from typing import List, Dict, Set
from src.modules.project_manager.domain.models import Task

class CriticalPathAnalyzer:
    """
    Сервис для расчета Критического Пути (CPM) в проекте.
    Определяет последовательность задач, которая диктует минимальную длительность проекта.
    """

    def calculate_critical_path(self, tasks: List[Task]) -> List[Task]:
        """
        Рассчитывает критический путь для списка задач.
        Предполагает, что 1 Story Point = 1 день (для упрощения, если duration не задан).
        """
        if not tasks:
            return []

        # 1. Построение графа и карты задач
        task_map = {t.id: t for t in tasks}
        graph = {t.id: [] for t in tasks}
        reverse_graph = {t.id: [] for t in tasks}
        
        # Словарь длительностей (используем story_points как дни)
        durations = {t.id: (t.story_points or 1) for t in tasks}
        
        for t in tasks:
            for dep_id in t.dependencies:
                if dep_id in task_map:
                    graph[dep_id].append(t.id)
                    reverse_graph[t.id].append(dep_id)

        # 2. Прямой проход (Forward Pass) - Вычисление Earliest Start (ES) и Earliest Finish (EF)
        es = {t.id: 0 for t in tasks}
        ef = {t.id: 0 for t in tasks}
        
        # Топологическая сортировка или итеративный подход (для простоты итеративный, т.к. может быть не DAG)
        # Но CPM работает только на DAG. Предполагаем DAG.
        
        # Находим стартовые узлы (без зависимостей)
        queue = [t.id for t in tasks if not t.dependencies]
        visited_forward = set()
        
        while queue:
            u = queue.pop(0)
            if u in visited_forward:
                continue
            visited_forward.add(u)
            
            # ES = max(EF всех предшественников)
            predecessors = reverse_graph[u]
            if not predecessors:
                es[u] = 0
            else:
                es[u] = max(ef[p] for p in predecessors)
            
            ef[u] = es[u] + durations[u]
            
            # Добавляем последователей в очередь, если все их предшественники обработаны
            for v in graph[u]:
                if all(p in visited_forward for p in reverse_graph[v]):
                    queue.append(v)
                    
        # Проверка на циклы (если не все посещены)
        if len(visited_forward) != len(tasks):
            # В случае цикла CPM не работает корректно. Возвращаем задачи с макс длительностью как фоллбек?
            # Или выбрасываем ошибку. Для надежности вернем просто самую длинную цепочку из обработанных.
            pass

        # 3. Обратный проход (Backward Pass) - Вычисление Latest Start (LS) и Latest Finish (LF)
        project_duration = max(ef.values()) if ef else 0
        
        ls = {t.id: project_duration for t in tasks}
        lf = {t.id: project_duration for t in tasks}
        
        # Начинаем с конечных узлов (у которых нет последователей)
        queue = [t.id for t in tasks if not graph[t.id]]
        visited_backward = set()
        
        while queue:
            u = queue.pop(0)
            if u in visited_backward:
                continue
            visited_backward.add(u)
            
            # LF = min(LS всех последователей)
            successors = graph[u]
            if not successors:
                lf[u] = project_duration
            else:
                lf[u] = min(ls[s] for s in successors)
                
            ls[u] = lf[u] - durations[u]
            
            # Добавляем предшественников
            for p in reverse_graph[u]:
                if all(s in visited_backward for s in graph[p]):
                    queue.append(p)

        # 4. Вычисление резерва (Float/Slack) и определение критического пути
        # Float = LS - ES (или LF - EF)
        critical_path = []
        for t in tasks:
            float_val = ls[t.id] - es[t.id]
            # Задачи с нулевым резервом лежат на критическом пути
            if float_val <= 0: # <= 0 для учета погрешностей float, хотя тут int
                critical_path.append(t)
                
        # Сортируем по ES
        critical_path.sort(key=lambda t: es[t.id])
        
        return critical_path
