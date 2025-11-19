"""Cloudflare API client service"""

import httpx
from typing import Dict, Any, List, Optional
import logging
from ..config import get_settings

logger = logging.getLogger(__name__)


class CloudflareAPIError(Exception):
    """Cloudflare API error"""
    pass


class CloudflareService:
    """Service for interacting with Cloudflare API"""
    
    BASE_URL = "https://api.cloudflare.com/client/v4"
    
    def __init__(self):
        self.settings = get_settings()
        self.api_token = self.settings.cloudflare_api_token
        self.account_id = self.settings.cloudflare_account_id
        
        if not self.api_token:
            logger.warning("Cloudflare API token not configured")
        if not self.account_id:
            logger.warning("Cloudflare account ID not configured")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get API request headers"""
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make API request to Cloudflare"""
        if not self.api_token:
            raise CloudflareAPIError("Cloudflare API token not configured")
        
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                    params=params
                )
                response.raise_for_status()
                result = response.json()
                
                # Cloudflare API wraps responses in a result object
                if not result.get("success", False):
                    errors = result.get("errors", [])
                    error_msg = "; ".join([e.get("message", "Unknown error") for e in errors])
                    raise CloudflareAPIError(f"Cloudflare API error: {error_msg}")
                
                return result.get("result", result)
            
            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                if status_code == 429:
                    # Rate limiting - extract retry-after if available
                    retry_after = e.response.headers.get("Retry-After", "unknown")
                    error_msg = f"Rate limit exceeded. Retry after: {retry_after} seconds"
                    logger.warning(f"Cloudflare rate limit: {error_msg}")
                else:
                    error_msg = f"HTTP {status_code}: {e.response.text}"
                    logger.error(f"Cloudflare API error: {error_msg}")
                raise CloudflareAPIError(error_msg)
            except Exception as e:
                logger.exception(f"Unexpected error calling Cloudflare API: {e}")
                raise CloudflareAPIError(f"Unexpected error: {str(e)}")
    
    # ========================================================================
    # Workers API
    # ========================================================================
    
    async def list_workers(self) -> List[Dict[str, Any]]:
        """List all Workers in the account"""
        endpoint = f"/accounts/{self.account_id}/workers/scripts"
        result = await self._request("GET", endpoint)
        return result if isinstance(result, list) else []
    
    async def get_worker(self, script_name: str) -> Dict[str, Any]:
        """Get Worker details"""
        endpoint = f"/accounts/{self.account_id}/workers/scripts/{script_name}"
        return await self._request("GET", endpoint)
    
    async def deploy_worker(
        self,
        script_name: str,
        script_content: str,
        bindings: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Deploy or update a Worker"""
        endpoint = f"/accounts/{self.account_id}/workers/scripts/{script_name}"
        
        # Cloudflare Workers API uses multipart/form-data
        # We need to construct this manually or use files parameter
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers()
        
        # Remove Content-Type to let httpx set multipart boundary
        headers.pop("Content-Type", None)
        
        # Prepare multipart form data
        files = {
            "script": (script_name, script_content.encode('utf-8'), "application/javascript")
        }
        
        data = {}
        if bindings:
            # Bindings need to be in metadata
            import json
            data["metadata"] = json.dumps({"bindings": bindings})
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.put(
                    url=url,
                    headers=headers,
                    files=files,
                    data=data
                )
                response.raise_for_status()
                result = response.json()
                
                if not result.get("success", False):
                    errors = result.get("errors", [])
                    error_msg = "; ".join([e.get("message", "Unknown error") for e in errors])
                    raise CloudflareAPIError(f"Cloudflare API error: {error_msg}")
                
                return result.get("result", result)
            except httpx.HTTPStatusError as e:
                error_msg = f"HTTP {e.response.status_code}: {e.response.text}"
                raise CloudflareAPIError(error_msg)
    
    async def delete_worker(self, script_name: str) -> Dict[str, Any]:
        """Delete a Worker"""
        endpoint = f"/accounts/{self.account_id}/workers/scripts/{script_name}"
        return await self._request("DELETE", endpoint)
    
    async def get_worker_routes(self, script_name: str) -> List[Dict[str, Any]]:
        """Get routes for a Worker"""
        endpoint = f"/accounts/{self.account_id}/workers/scripts/{script_name}/routes"
        result = await self._request("GET", endpoint)
        return result if isinstance(result, list) else []
    
    async def get_worker_logs(
        self,
        script_name: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get Worker logs (requires Workers Analytics Engine)"""
        # Note: Real-time logs require tailing via wrangler or Workers Analytics Engine
        # This is a placeholder for the API endpoint
        endpoint = f"/accounts/{self.account_id}/workers/scripts/{script_name}/logs"
        params = {}
        if start_time:
            params["start"] = start_time
        if end_time:
            params["end"] = end_time
        
        try:
            result = await self._request("GET", endpoint, params=params)
            return result if isinstance(result, list) else []
        except CloudflareAPIError:
            # Logs might not be available via API, return empty
            logger.warning(f"Logs not available for {script_name} (may require Workers Analytics Engine)")
            return []
    
    # ========================================================================
    # D1 Database API
    # ========================================================================
    
    async def list_d1_databases(self) -> List[Dict[str, Any]]:
        """List all D1 databases"""
        endpoint = f"/accounts/{self.account_id}/d1/database"
        result = await self._request("GET", endpoint)
        return result if isinstance(result, list) else []
    
    async def create_d1_database(self, name: str) -> Dict[str, Any]:
        """Create a new D1 database"""
        endpoint = f"/accounts/{self.account_id}/d1/database"
        data = {"name": name}
        return await self._request("POST", endpoint, data=data)
    
    async def query_d1(
        self,
        database_id: str,
        query: str,
        params: Optional[List[Any]] = None
    ) -> Dict[str, Any]:
        """Execute a SQL query on D1 database"""
        endpoint = f"/accounts/{self.account_id}/d1/database/{database_id}/query"
        data = {"sql": query}
        if params:
            data["params"] = params
        return await self._request("POST", endpoint, data=data)
    
    # ========================================================================
    # KV Storage API
    # ========================================================================
    
    async def list_kv_namespaces(self) -> List[Dict[str, Any]]:
        """List all KV namespaces"""
        endpoint = f"/accounts/{self.account_id}/storage/kv/namespaces"
        result = await self._request("GET", endpoint)
        return result if isinstance(result, list) else []
    
    async def create_kv_namespace(self, title: str) -> Dict[str, Any]:
        """Create a new KV namespace"""
        endpoint = f"/accounts/{self.account_id}/storage/kv/namespaces"
        data = {"title": title}
        return await self._request("POST", endpoint, data=data)
    
    async def get_kv_value(
        self,
        namespace_id: str,
        key: str
    ) -> Optional[str]:
        """Get value from KV storage"""
        endpoint = f"/accounts/{self.account_id}/storage/kv/namespaces/{namespace_id}/values/{key}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    url=f"{self.BASE_URL}{endpoint}",
                    headers=self._get_headers()
                )
                if response.status_code == 404:
                    return None
                response.raise_for_status()
                return response.text
        except httpx.HTTPStatusError:
            return None
    
    async def put_kv_value(
        self,
        namespace_id: str,
        key: str,
        value: str
    ) -> Dict[str, Any]:
        """Put value into KV storage"""
        endpoint = f"/accounts/{self.account_id}/storage/kv/namespaces/{namespace_id}/values/{key}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.put(
                url=f"{self.BASE_URL}{endpoint}",
                headers=self._get_headers(),
                content=value
            )
            response.raise_for_status()
            return {"success": True}
    
    async def delete_kv_value(
        self,
        namespace_id: str,
        key: str
    ) -> Dict[str, Any]:
        """Delete value from KV storage"""
        endpoint = f"/accounts/{self.account_id}/storage/kv/namespaces/{namespace_id}/values/{key}"
        return await self._request("DELETE", endpoint)
    
    # ========================================================================
    # Durable Objects API
    # ========================================================================
    
    async def list_durable_object_namespaces(self) -> List[Dict[str, Any]]:
        """List all Durable Object namespaces"""
        endpoint = f"/accounts/{self.account_id}/workers/durable_objects/namespaces"
        result = await self._request("GET", endpoint)
        return result if isinstance(result, list) else []
    
    async def get_durable_object_namespace(self, namespace_id: str) -> Dict[str, Any]:
        """Get Durable Object namespace details"""
        # List all and find the one we want
        namespaces = await self.list_durable_object_namespaces()
        for ns in namespaces:
            if ns.get("id") == namespace_id or ns.get("namespace_id") == namespace_id:
                return ns
        raise CloudflareAPIError(f"Namespace {namespace_id} not found")
    
    async def list_durable_objects(
        self,
        namespace_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List Durable Objects in a namespace"""
        endpoint = f"/accounts/{self.account_id}/workers/durable_objects/namespaces/{namespace_id}/objects"
        params = {"limit": limit} if limit else {}
        result = await self._request("GET", endpoint, params=params)
        return result if isinstance(result, list) else []
    
    async def get_durable_object(
        self,
        namespace_id: str,
        object_id: str
    ) -> Dict[str, Any]:
        """Get Durable Object details"""
        # List objects and find the one we want
        objects = await self.list_durable_objects(namespace_id)
        for obj in objects:
            if obj.get("id") == object_id:
                return obj
        raise CloudflareAPIError(f"Durable Object {object_id} not found in namespace {namespace_id}")
    
    async def list_durable_object_classes(self) -> List[Dict[str, Any]]:
        """List Durable Object classes (via Workers API)"""
        # Durable Objects are defined in Workers, so we list workers with DO bindings
        workers = await self.list_workers()
        do_classes = []
        
        for worker in workers:
            try:
                worker_details = await self.get_worker(worker.get("id", worker.get("name", "")))
                bindings = worker_details.get("bindings", [])
                for binding in bindings:
                    if binding.get("type") == "durable_object_namespace":
                        do_classes.append({
                            "worker": worker.get("name", worker.get("id")),
                            "class_name": binding.get("class_name"),
                            "namespace": binding.get("namespace_id")
                        })
            except Exception:
                # Skip workers we can't access
                continue
        
        return do_classes
    
    # ========================================================================
    # Pages API
    # ========================================================================
    
    async def list_pages_projects(self) -> List[Dict[str, Any]]:
        """List all Pages projects"""
        endpoint = f"/accounts/{self.account_id}/pages/projects"
        result = await self._request("GET", endpoint)
        return result if isinstance(result, list) else []
    
    async def get_pages_project(self, project_name: str) -> Dict[str, Any]:
        """Get Pages project details"""
        endpoint = f"/accounts/{self.account_id}/pages/projects/{project_name}"
        return await self._request("GET", endpoint)
    
    # ========================================================================
    # Workflows API
    # ========================================================================
    
    async def list_workflows(self) -> List[Dict[str, Any]]:
        """List all Workflows"""
        endpoint = f"/accounts/{self.account_id}/workflows"
        try:
            result = await self._request("GET", endpoint)
            return result if isinstance(result, list) else []
        except CloudflareAPIError:
            # Workflows might not be available in all accounts
            logger.warning("Workflows API not available (may require Workers Paid plan)")
            return []
    
    async def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Get Workflow details"""
        endpoint = f"/accounts/{self.account_id}/workflows/{workflow_id}"
        return await self._request("GET", endpoint)
    
    async def create_workflow(
        self,
        name: str,
        definition: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new Workflow"""
        endpoint = f"/accounts/{self.account_id}/workflows"
        data = {
            "name": name,
            "definition": definition
        }
        return await self._request("POST", endpoint, data=data)
    
    async def trigger_workflow(
        self,
        workflow_id: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Trigger a Workflow execution"""
        endpoint = f"/accounts/{self.account_id}/workflows/{workflow_id}/executions"
        data = {"input": input_data}
        return await self._request("POST", endpoint, data=data)
    
    async def get_workflow_execution(
        self,
        workflow_id: str,
        execution_id: str
    ) -> Dict[str, Any]:
        """Get Workflow execution status"""
        endpoint = f"/accounts/{self.account_id}/workflows/{workflow_id}/executions/{execution_id}"
        return await self._request("GET", endpoint)
    
    # ========================================================================
    # R2 Storage API
    # ========================================================================
    
    async def list_r2_buckets(self) -> List[Dict[str, Any]]:
        """List all R2 buckets"""
        endpoint = f"/accounts/{self.account_id}/r2/buckets"
        try:
            result = await self._request("GET", endpoint)
            return result if isinstance(result, list) else []
        except CloudflareAPIError:
            # R2 might not be available in all accounts
            logger.warning("R2 API not available (may require R2 subscription)")
            return []
    
    async def create_r2_bucket(
        self,
        name: str,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new R2 bucket"""
        endpoint = f"/accounts/{self.account_id}/r2/buckets"
        data = {"name": name}
        if location:
            data["location"] = location
        return await self._request("POST", endpoint, data=data)
    
    async def upload_r2_object(
        self,
        bucket_name: str,
        object_key: str,
        content: str,
        content_type: str = "text/plain"
    ) -> Dict[str, Any]:
        """Upload object to R2 bucket"""
        # R2 uses S3-compatible API, but we'll use Cloudflare's direct API
        endpoint = f"/accounts/{self.account_id}/r2/buckets/{bucket_name}/objects/{object_key}"
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers()
        headers["Content-Type"] = content_type
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.put(
                url=url,
                headers=headers,
                content=content.encode('utf-8') if isinstance(content, str) else content
            )
            response.raise_for_status()
            return {"success": True}
    
    async def get_r2_object(
        self,
        bucket_name: str,
        object_key: str
    ) -> Dict[str, Any]:
        """Get object from R2 bucket"""
        endpoint = f"/accounts/{self.account_id}/r2/buckets/{bucket_name}/objects/{object_key}"
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers()
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url=url, headers=headers)
            response.raise_for_status()
            return {
                "content": response.text,
                "content_type": response.headers.get("Content-Type", "application/octet-stream"),
                "size": len(response.content)
            }
    
    async def delete_r2_object(
        self,
        bucket_name: str,
        object_key: str
    ) -> Dict[str, Any]:
        """Delete object from R2 bucket"""
        endpoint = f"/accounts/{self.account_id}/r2/buckets/{bucket_name}/objects/{object_key}"
        return await self._request("DELETE", endpoint)
    
    # ========================================================================
    # Vectorize API
    # ========================================================================
    
    async def list_vectorize_indexes(self) -> List[Dict[str, Any]]:
        """List all Vectorize indexes"""
        endpoint = f"/accounts/{self.account_id}/vectorize/indexes"
        try:
            result = await self._request("GET", endpoint)
            return result if isinstance(result, list) else []
        except CloudflareAPIError:
            # Vectorize might not be available in all accounts
            logger.warning("Vectorize API not available (may require Workers Paid plan)")
            return []
    
    async def create_vectorize_index(
        self,
        name: str,
        dimensions: int,
        metric: str = "cosine"
    ) -> Dict[str, Any]:
        """Create a new Vectorize index"""
        endpoint = f"/accounts/{self.account_id}/vectorize/indexes"
        data = {
            "name": name,
            "dimensions": dimensions,
            "metric": metric
        }
        return await self._request("POST", endpoint, data=data)
    
    async def upsert_vectors(
        self,
        index_name: str,
        vectors: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Upsert vectors into Vectorize index"""
        endpoint = f"/accounts/{self.account_id}/vectorize/indexes/{index_name}/insert"
        data = {"vectors": vectors}
        return await self._request("POST", endpoint, data=data)
    
    async def query_vectors(
        self,
        index_name: str,
        vector: List[float],
        top_k: int = 10,
        return_metadata: bool = True
    ) -> Dict[str, Any]:
        """Query vectors in Vectorize index"""
        endpoint = f"/accounts/{self.account_id}/vectorize/indexes/{index_name}/query"
        data = {
            "vector": vector,
            "topK": top_k,
            "returnMetadata": return_metadata
        }
        return await self._request("POST", endpoint, data=data)
    
    # ========================================================================
    # Account Info
    # ========================================================================
    
    async def get_account_info(self) -> Dict[str, Any]:
        """Get account information"""
        endpoint = f"/accounts/{self.account_id}"
        return await self._request("GET", endpoint)

