# Configuration management

from pydantic import ConfigDict
from pydantic_settings import BaseSettings
import os
from dotenv import load_dotenv
import logger
from chromadb.config import APIVersion, RoutingMode
import chromadb.config
import chromadb


load_dotenv()

log = logger.logger

chromadb_client = chromadb.Client(
    settings=chromadb.config.Settings(
        environment="",
        chroma_api_impl="chromadb.api.rust.RustBindingsAPI",
        chroma_server_nofile=None,
        chroma_server_thread_pool_size=40,
        tenant_id="default",
        topic_namespace="default",
        chroma_server_host=None,
        chroma_server_headers=None,
        chroma_server_http_port=None,
        chroma_server_ssl_enabled=False,
        chroma_server_ssl_verify=None,
        chroma_server_api_default_path=APIVersion.V2,
        chroma_server_cors_allow_origins=[],
        chroma_http_keepalive_secs=40.0,
        chroma_http_max_connections=None,
        chroma_http_max_keepalive_connections=None,
        is_persistent=False,
        persist_directory="../vector_data",
        chroma_memory_limit_bytes=0,
        chroma_segment_cache_policy=None,
        allow_reset=False,
        chroma_auth_token_transport_header=None,
        chroma_client_auth_provider=None,
        chroma_client_auth_credentials=None,
        chroma_server_auth_ignore_paths={
            f"{APIVersion.V2}": ["GET"],
            f"{APIVersion.V2}/heartbeat": ["GET"],
            f"{APIVersion.V2}/version": ["GET"],
            f"{APIVersion.V1}": ["GET"],
            f"{APIVersion.V1}/heartbeat": ["GET"],
            f"{APIVersion.V1}/version": ["GET"],
        },
        chroma_overwrite_singleton_tenant_database_access_from_auth=False,
        chroma_server_authn_provider=None,
        chroma_server_authn_credentials=None,
        chroma_server_authn_credentials_file=None,
        chroma_server_authz_provider=None,
        chroma_server_authz_config=None,
        chroma_server_authz_config_file=None,
        chroma_product_telemetry_impl="chromadb.telemetry.product.posthog.Posthog",
        anonymized_telemetry=True,
        chroma_otel_collection_endpoint="",
        chroma_otel_service_name="chromadb",
        chroma_otel_collection_headers={},
        chroma_otel_granularity=None,
        migrations="apply",
        migrations_hash_algorithm="md5",
        chroma_segment_directory_impl="chromadb.segment.impl.distributed.segment_directory.RendezvousHashSegmentDirectory",
        chroma_segment_directory_routing_mode=RoutingMode.ID,
        chroma_memberlist_provider_impl="chromadb.segment.impl.distributed.segment_directory.CustomResourceMemberlistProvider",
        worker_memberlist_name="query-service-memberlist",
        chroma_coordinator_host="localhost",
        chroma_server_grpc_port=None,
        chroma_sysdb_impl="chromadb.db.impl.sqlite.SqliteDB",
        chroma_producer_impl="chromadb.db.impl.sqlite.SqliteDB",
        chroma_consumer_impl="chromadb.db.impl.sqlite.SqliteDB",
        chroma_segment_manager_impl=(
            "chromadb.segment.impl.manager.local.LocalSegmentManager"),
        chroma_executor_impl="chromadb.execution.executor.local.LocalExecutor",
        chroma_query_replication_factor=2,
        chroma_logservice_host="localhost",
        chroma_logservice_port=50052,
        chroma_quota_provider_impl=None,
        chroma_rate_limiting_provider_impl=None,
        chroma_quota_enforcer_impl=(
            "chromadb.quota.simple_quota_enforcer.SimpleQuotaEnforcer"),
        chroma_rate_limit_enforcer_impl=(
            "chromadb.rate_limit.simple_rate_limit.SimpleRateLimitEnforcer"),
        chroma_async_rate_limit_enforcer_impl=(
            "chromadb.rate_limit.simple_rate_limit.SimpleAsyncRateLimitEnforcer"),
        chroma_logservice_request_timeout_seconds=3,
        chroma_sysdb_request_timeout_seconds=3,
        chroma_query_request_timeout_seconds=60,
        chroma_db_impl=None,
        chroma_collection_assignment_policy_impl=(
            "chromadb.ingest.impl.simple_policy.SimpleAssignmentPolicy"),
    )
)


class Settings(BaseSettings):
    app_name: str = "AI Test Platform"
    llm_provider: str = "openai"
    use_local_llm: bool = True
    OPENAI_API_KEY: str | None = os.getenv("LLM_API_KEY")
    OPENAI_MODEL: str | None = os.getenv("OPENAI_MODEL")
    LOCAL_LLM_MODEL: str | None = os.getenv("LOCAL_LLM_MODEL")
    EMBED_MODEL: str | None = os.getenv("EMBED_MODEL")


settings = Settings()
