"""Cloudflare Vectorize tools"""

from typing import Dict, Any, List
import logging
from ..base import BaseTool
from ...services.cloudflare import CloudflareService, CloudflareAPIError

logger = logging.getLogger(__name__)


class ListVectorizeIndexesTool(BaseTool):
    """List all Vectorize indexes"""
    
    name = "cloudflare_list_vectorize_indexes"
    description = "List all Vectorize indexes in your Cloudflare account"
    
    input_schema = {
        "type": "object",
        "properties": {},
        "required": []
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """List Vectorize indexes"""
        service = CloudflareService()
        try:
            indexes = await service.list_vectorize_indexes()
            return {
                "indexes": indexes,
                "count": len(indexes)
            }
        except CloudflareAPIError as e:
            return {"error": str(e)}


class CreateVectorizeIndexTool(BaseTool):
    """Create a new Vectorize index"""
    
    name = "cloudflare_create_vectorize_index"
    description = "Create a new Vectorize index"
    
    input_schema = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Name for the Vectorize index"
            },
            "dimensions": {
                "type": "integer",
                "description": "Number of dimensions for vectors"
            },
            "metric": {
                "type": "string",
                "description": "Distance metric (cosine, euclidean, dot-product)",
                "default": "cosine"
            }
        },
        "required": ["name", "dimensions"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Create Vectorize index"""
        service = CloudflareService()
        name = args["name"]
        dimensions = args["dimensions"]
        metric = args.get("metric", "cosine")
        
        try:
            result = await service.create_vectorize_index(name, dimensions, metric)
            return {
                "success": True,
                "index": result
            }
        except CloudflareAPIError as e:
            return {"error": str(e), "success": False}


class UpsertVectorsTool(BaseTool):
    """Upsert vectors into Vectorize index"""
    
    name = "cloudflare_upsert_vectors"
    description = "Insert or update vectors in a Vectorize index"
    
    input_schema = {
        "type": "object",
        "properties": {
            "index_name": {
                "type": "string",
                "description": "Vectorize index name"
            },
            "vectors": {
                "type": "array",
                "description": "Array of vector objects with id, values, and optional metadata",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "values": {"type": "array", "items": {"type": "number"}},
                        "metadata": {"type": "object"}
                    },
                    "required": ["id", "values"]
                }
            }
        },
        "required": ["index_name", "vectors"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Upsert vectors"""
        service = CloudflareService()
        index_name = args["index_name"]
        vectors = args["vectors"]
        
        try:
            result = await service.upsert_vectors(index_name, vectors)
            return {
                "success": True,
                "index": index_name,
                "count": len(vectors),
                "result": result
            }
        except CloudflareAPIError as e:
            return {"error": str(e), "success": False}


class QueryVectorsTool(BaseTool):
    """Query vectors in Vectorize index"""
    
    name = "cloudflare_query_vectors"
    description = "Query vectors in a Vectorize index (semantic search)"
    
    input_schema = {
        "type": "object",
        "properties": {
            "index_name": {
                "type": "string",
                "description": "Vectorize index name"
            },
            "vector": {
                "type": "array",
                "description": "Query vector (array of numbers)",
                "items": {"type": "number"}
            },
            "top_k": {
                "type": "integer",
                "description": "Number of results to return",
                "default": 10
            },
            "return_metadata": {
                "type": "boolean",
                "description": "Whether to return metadata with results",
                "default": True
            }
        },
        "required": ["index_name", "vector"]
    }
    
    async def execute(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Query vectors"""
        service = CloudflareService()
        index_name = args["index_name"]
        vector = args["vector"]
        top_k = args.get("top_k", 10)
        return_metadata = args.get("return_metadata", True)
        
        try:
            result = await service.query_vectors(
                index_name=index_name,
                vector=vector,
                top_k=top_k,
                return_metadata=return_metadata
            )
            return {
                "index": index_name,
                "results": result.get("matches", []),
                "count": len(result.get("matches", []))
            }
        except CloudflareAPIError as e:
            return {"error": str(e)}


