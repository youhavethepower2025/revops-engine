"""Cloudflare tools for Workers orchestration"""

from .workers import (
    ListWorkersTool,
    GetWorkerTool,
    DeployWorkerTool,
    DeleteWorkerTool,
    GetWorkerLogsTool,
)
from .d1 import (
    ListD1DatabasesTool,
    CreateD1DatabaseTool,
    QueryD1Tool,
)
from .kv import (
    ListKVNamespacesTool,
    CreateKVNamespaceTool,
    GetKVValueTool,
    SetKVValueTool,
    DeleteKVValueTool,
)
from .durable_objects import (
    ListDurableObjectNamespacesTool,
    GetDurableObjectNamespaceTool,
    ListDurableObjectsTool,
    GetDurableObjectTool,
)
from .workflows import (
    ListWorkflowsTool,
    GetWorkflowTool,
    CreateWorkflowTool,
    TriggerWorkflowTool,
    GetWorkflowExecutionTool,
)
from .r2 import (
    ListR2BucketsTool,
    CreateR2BucketTool,
    UploadR2ObjectTool,
    GetR2ObjectTool,
    DeleteR2ObjectTool,
)
from .vectorize import (
    ListVectorizeIndexesTool,
    CreateVectorizeIndexTool,
    UpsertVectorsTool,
    QueryVectorsTool,
)

__all__ = [
    # Workers
    "ListWorkersTool",
    "GetWorkerTool",
    "DeployWorkerTool",
    "DeleteWorkerTool",
    "GetWorkerLogsTool",
    # D1
    "ListD1DatabasesTool",
    "CreateD1DatabaseTool",
    "QueryD1Tool",
    # KV
    "ListKVNamespacesTool",
    "CreateKVNamespaceTool",
    "GetKVValueTool",
    "SetKVValueTool",
    "DeleteKVValueTool",
    # Durable Objects
    "ListDurableObjectNamespacesTool",
    "GetDurableObjectNamespaceTool",
    "ListDurableObjectsTool",
    "GetDurableObjectTool",
    # Workflows
    "ListWorkflowsTool",
    "GetWorkflowTool",
    "CreateWorkflowTool",
    "TriggerWorkflowTool",
    "GetWorkflowExecutionTool",
    # R2
    "ListR2BucketsTool",
    "CreateR2BucketTool",
    "UploadR2ObjectTool",
    "GetR2ObjectTool",
    "DeleteR2ObjectTool",
    # Vectorize
    "ListVectorizeIndexesTool",
    "CreateVectorizeIndexTool",
    "UpsertVectorsTool",
    "QueryVectorsTool",
]
