from collections.abc import Iterable as _Iterable
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar
from typing import Optional as _Optional
from typing import Union as _Union

from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from google.protobuf.internal import containers as _containers

DESCRIPTOR: _descriptor.FileDescriptor

class QueryRequest(_message.Message):
    __slots__ = ("query", "context", "metadata", "user_id")

    class MetadataEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(
            self, key: _Optional[str] = ..., value: _Optional[str] = ...
        ) -> None: ...

    QUERY_FIELD_NUMBER: _ClassVar[int]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    METADATA_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    query: str
    context: str
    metadata: _containers.ScalarMap[str, str]
    user_id: str
    def __init__(
        self,
        query: _Optional[str] = ...,
        context: _Optional[str] = ...,
        metadata: _Optional[_Mapping[str, str]] = ...,
        user_id: _Optional[str] = ...,
    ) -> None: ...

class QueryResponse(_message.Message):
    __slots__ = ("response", "sources", "confidence", "model_used")
    RESPONSE_FIELD_NUMBER: _ClassVar[int]
    SOURCES_FIELD_NUMBER: _ClassVar[int]
    CONFIDENCE_FIELD_NUMBER: _ClassVar[int]
    MODEL_USED_FIELD_NUMBER: _ClassVar[int]
    response: str
    sources: _containers.RepeatedScalarFieldContainer[str]
    confidence: float
    model_used: str
    def __init__(
        self,
        response: _Optional[str] = ...,
        sources: _Optional[_Iterable[str]] = ...,
        confidence: _Optional[float] = ...,
        model_used: _Optional[str] = ...,
    ) -> None: ...

class QueryChunk(_message.Message):
    __slots__ = ("chunk", "is_final")
    CHUNK_FIELD_NUMBER: _ClassVar[int]
    IS_FINAL_FIELD_NUMBER: _ClassVar[int]
    chunk: str
    is_final: bool
    def __init__(self, chunk: _Optional[str] = ..., is_final: bool = ...) -> None: ...

class ScreenFrame(_message.Message):
    __slots__ = ("image_data", "window_title", "timestamp", "width", "height")
    IMAGE_DATA_FIELD_NUMBER: _ClassVar[int]
    WINDOW_TITLE_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    WIDTH_FIELD_NUMBER: _ClassVar[int]
    HEIGHT_FIELD_NUMBER: _ClassVar[int]
    image_data: bytes
    window_title: str
    timestamp: int
    width: int
    height: int
    def __init__(
        self,
        image_data: _Optional[bytes] = ...,
        window_title: _Optional[str] = ...,
        timestamp: _Optional[int] = ...,
        width: _Optional[int] = ...,
        height: _Optional[int] = ...,
    ) -> None: ...

class ContextAnalysis(_message.Message):
    __slots__ = ("detected_context", "suggestions", "active_1c_object", "ui_elements")

    class UiElementsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(
            self, key: _Optional[str] = ..., value: _Optional[str] = ...
        ) -> None: ...

    DETECTED_CONTEXT_FIELD_NUMBER: _ClassVar[int]
    SUGGESTIONS_FIELD_NUMBER: _ClassVar[int]
    ACTIVE_1C_OBJECT_FIELD_NUMBER: _ClassVar[int]
    UI_ELEMENTS_FIELD_NUMBER: _ClassVar[int]
    detected_context: str
    suggestions: _containers.RepeatedScalarFieldContainer[str]
    active_1c_object: str
    ui_elements: _containers.ScalarMap[str, str]
    def __init__(
        self,
        detected_context: _Optional[str] = ...,
        suggestions: _Optional[_Iterable[str]] = ...,
        active_1c_object: _Optional[str] = ...,
        ui_elements: _Optional[_Mapping[str, str]] = ...,
    ) -> None: ...

class CodeSearchRequest(_message.Message):
    __slots__ = ("query", "language", "max_results", "file_filters")
    QUERY_FIELD_NUMBER: _ClassVar[int]
    LANGUAGE_FIELD_NUMBER: _ClassVar[int]
    MAX_RESULTS_FIELD_NUMBER: _ClassVar[int]
    FILE_FILTERS_FIELD_NUMBER: _ClassVar[int]
    query: str
    language: str
    max_results: int
    file_filters: _containers.RepeatedScalarFieldContainer[str]
    def __init__(
        self,
        query: _Optional[str] = ...,
        language: _Optional[str] = ...,
        max_results: _Optional[int] = ...,
        file_filters: _Optional[_Iterable[str]] = ...,
    ) -> None: ...

class CodeSearchResponse(_message.Message):
    __slots__ = ("results", "total_found")
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_FOUND_FIELD_NUMBER: _ClassVar[int]
    results: _containers.RepeatedCompositeFieldContainer[CodeResult]
    total_found: int
    def __init__(
        self,
        results: _Optional[_Iterable[_Union[CodeResult, _Mapping]]] = ...,
        total_found: _Optional[int] = ...,
    ) -> None: ...

class CodeResult(_message.Message):
    __slots__ = (
        "file_path",
        "code_snippet",
        "line_number",
        "relevance_score",
        "object_type",
    )
    FILE_PATH_FIELD_NUMBER: _ClassVar[int]
    CODE_SNIPPET_FIELD_NUMBER: _ClassVar[int]
    LINE_NUMBER_FIELD_NUMBER: _ClassVar[int]
    RELEVANCE_SCORE_FIELD_NUMBER: _ClassVar[int]
    OBJECT_TYPE_FIELD_NUMBER: _ClassVar[int]
    file_path: str
    code_snippet: str
    line_number: int
    relevance_score: float
    object_type: str
    def __init__(
        self,
        file_path: _Optional[str] = ...,
        code_snippet: _Optional[str] = ...,
        line_number: _Optional[int] = ...,
        relevance_score: _Optional[float] = ...,
        object_type: _Optional[str] = ...,
    ) -> None: ...

class DependencyRequest(_message.Message):
    __slots__ = ("module_name", "depth")
    MODULE_NAME_FIELD_NUMBER: _ClassVar[int]
    DEPTH_FIELD_NUMBER: _ClassVar[int]
    module_name: str
    depth: int
    def __init__(
        self, module_name: _Optional[str] = ..., depth: _Optional[int] = ...
    ) -> None: ...

class DependencyResponse(_message.Message):
    __slots__ = ("dependencies",)
    DEPENDENCIES_FIELD_NUMBER: _ClassVar[int]
    dependencies: _containers.RepeatedCompositeFieldContainer[Dependency]
    def __init__(
        self, dependencies: _Optional[_Iterable[_Union[Dependency, _Mapping]]] = ...
    ) -> None: ...

class Dependency(_message.Message):
    __slots__ = ("from_module", "to_module", "dependency_type")
    FROM_MODULE_FIELD_NUMBER: _ClassVar[int]
    TO_MODULE_FIELD_NUMBER: _ClassVar[int]
    DEPENDENCY_TYPE_FIELD_NUMBER: _ClassVar[int]
    from_module: str
    to_module: str
    dependency_type: str
    def __init__(
        self,
        from_module: _Optional[str] = ...,
        to_module: _Optional[str] = ...,
        dependency_type: _Optional[str] = ...,
    ) -> None: ...

class MetadataRequest(_message.Message):
    __slots__ = ("object_name", "object_type")
    OBJECT_NAME_FIELD_NUMBER: _ClassVar[int]
    OBJECT_TYPE_FIELD_NUMBER: _ClassVar[int]
    object_name: str
    object_type: str
    def __init__(
        self, object_name: _Optional[str] = ..., object_type: _Optional[str] = ...
    ) -> None: ...

class MetadataResponse(_message.Message):
    __slots__ = ("object_name", "object_type", "properties", "methods")

    class PropertiesEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(
            self, key: _Optional[str] = ..., value: _Optional[str] = ...
        ) -> None: ...

    OBJECT_NAME_FIELD_NUMBER: _ClassVar[int]
    OBJECT_TYPE_FIELD_NUMBER: _ClassVar[int]
    PROPERTIES_FIELD_NUMBER: _ClassVar[int]
    METHODS_FIELD_NUMBER: _ClassVar[int]
    object_name: str
    object_type: str
    properties: _containers.ScalarMap[str, str]
    methods: _containers.RepeatedScalarFieldContainer[str]
    def __init__(
        self,
        object_name: _Optional[str] = ...,
        object_type: _Optional[str] = ...,
        properties: _Optional[_Mapping[str, str]] = ...,
        methods: _Optional[_Iterable[str]] = ...,
    ) -> None: ...

class ScenarioRequest(_message.Message):
    __slots__ = ("current_context", "user_role")
    CURRENT_CONTEXT_FIELD_NUMBER: _ClassVar[int]
    USER_ROLE_FIELD_NUMBER: _ClassVar[int]
    current_context: str
    user_role: str
    def __init__(
        self, current_context: _Optional[str] = ..., user_role: _Optional[str] = ...
    ) -> None: ...

class ScenarioResponse(_message.Message):
    __slots__ = ("scenarios",)
    SCENARIOS_FIELD_NUMBER: _ClassVar[int]
    scenarios: _containers.RepeatedCompositeFieldContainer[Scenario]
    def __init__(
        self, scenarios: _Optional[_Iterable[_Union[Scenario, _Mapping]]] = ...
    ) -> None: ...

class Scenario(_message.Message):
    __slots__ = ("id", "name", "description", "relevance", "required_params")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    RELEVANCE_FIELD_NUMBER: _ClassVar[int]
    REQUIRED_PARAMS_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    description: str
    relevance: float
    required_params: _containers.RepeatedScalarFieldContainer[str]
    def __init__(
        self,
        id: _Optional[str] = ...,
        name: _Optional[str] = ...,
        description: _Optional[str] = ...,
        relevance: _Optional[float] = ...,
        required_params: _Optional[_Iterable[str]] = ...,
    ) -> None: ...

class ExecuteRequest(_message.Message):
    __slots__ = ("scenario_id", "params")

    class ParamsEntry(_message.Message):
        __slots__ = ("key", "value")
        KEY_FIELD_NUMBER: _ClassVar[int]
        VALUE_FIELD_NUMBER: _ClassVar[int]
        key: str
        value: str
        def __init__(
            self, key: _Optional[str] = ..., value: _Optional[str] = ...
        ) -> None: ...

    SCENARIO_ID_FIELD_NUMBER: _ClassVar[int]
    PARAMS_FIELD_NUMBER: _ClassVar[int]
    scenario_id: str
    params: _containers.ScalarMap[str, str]
    def __init__(
        self,
        scenario_id: _Optional[str] = ...,
        params: _Optional[_Mapping[str, str]] = ...,
    ) -> None: ...

class ExecutionStatus(_message.Message):
    __slots__ = (
        "stage",
        "progress",
        "message",
        "is_complete",
        "has_error",
        "error_message",
    )
    STAGE_FIELD_NUMBER: _ClassVar[int]
    PROGRESS_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    IS_COMPLETE_FIELD_NUMBER: _ClassVar[int]
    HAS_ERROR_FIELD_NUMBER: _ClassVar[int]
    ERROR_MESSAGE_FIELD_NUMBER: _ClassVar[int]
    stage: str
    progress: float
    message: str
    is_complete: bool
    has_error: bool
    error_message: str
    def __init__(
        self,
        stage: _Optional[str] = ...,
        progress: _Optional[float] = ...,
        message: _Optional[str] = ...,
        is_complete: bool = ...,
        has_error: bool = ...,
        error_message: _Optional[str] = ...,
    ) -> None: ...
