#!/usr/bin/env python3
"""
Database initialization script for Agentic Deployment Platform.

This script sets up the PostgreSQL database with required tables for
conversation logging and agent memory storage.
"""

import os
import sys
import asyncio
import asyncpg
from typing import Optional


class DatabaseInitializer:
    """Handles database initialization and table creation."""

    def __init__(self):
        """Initialize with environment variables or defaults."""
        self.host = os.getenv('DB_HOST', 'localhost')
        self.port = os.getenv('DB_PORT', '5432')
        self.user = os.getenv('DB_USER', 'postgres')
        self.password = os.getenv('DB_PASSWORD', 'postgres')
        self.database = os.getenv('DB_NAME', 'agentic_platform')
        
    async def connect_to_postgres(self) -> asyncpg.Connection:
        """Connect to PostgreSQL server (not specific database)."""
        try:
            conn = await asyncpg.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database='postgres'  # Connect to default postgres db first
            )
            print(f"✓ Connected to PostgreSQL server at {self.host}:{self.port}")
            return conn
        except Exception as e:
            print(f"✗ Failed to connect to PostgreSQL: {e}")
            sys.exit(1)

    async def connect_to_database(self) -> asyncpg.Connection:
        """Connect to the specific application database."""
        try:
            conn = await asyncpg.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database
            )
            print(f"✓ Connected to database '{self.database}'")
            return conn
        except Exception as e:
            print(f"✗ Failed to connect to database '{self.database}': {e}")
            raise

    async def database_exists(self, conn: asyncpg.Connection) -> bool:
        """Check if the application database exists."""
        result = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1",
            self.database
        )
        return result is not None

    async def create_database(self, conn: asyncpg.Connection) -> None:
        """Create the application database."""
        try:
            await conn.execute(f'CREATE DATABASE "{self.database}"')
            print(f"✓ Created database '{self.database}'")
        except Exception as e:
            print(f"✗ Failed to create database '{self.database}': {e}")
            raise

    async def create_conversations_table(self, conn: asyncpg.Connection) -> None:
        """Create the conversations table for storing all conversation turns."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS conversations (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(255) NOT NULL,
            turn_id INTEGER NOT NULL,
            agent_id VARCHAR(255) NOT NULL,
            customer_id VARCHAR(255) NOT NULL,
            speaker VARCHAR(10) NOT NULL CHECK (speaker IN ('user', 'agent')),
            message_text TEXT NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            
            -- Ensure unique turn IDs within a session
            UNIQUE(session_id, turn_id)
        );
        """
        
        # Create indexes for better query performance
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_conversations_session ON conversations(session_id);",
            "CREATE INDEX IF NOT EXISTS idx_conversations_agent_customer ON conversations(agent_id, customer_id);",
            "CREATE INDEX IF NOT EXISTS idx_conversations_timestamp ON conversations(timestamp);"
        ]
        
        try:
            await conn.execute(create_table_sql)
            print("✓ Created conversations table")
            
            for index_sql in indexes_sql:
                await conn.execute(index_sql)
            print("✓ Created conversations table indexes")
            
        except Exception as e:
            print(f"✗ Failed to create conversations table: {e}")
            raise

    async def create_agent_memory_table(self, conn: asyncpg.Connection) -> None:
        """Create the agent_memory table for storing agent long-term memory."""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS agent_memory (
            id SERIAL PRIMARY KEY,
            agent_id VARCHAR(255) NOT NULL,
            customer_id VARCHAR(255) NOT NULL,
            memory_key VARCHAR(255) NOT NULL,
            memory_value TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            
            -- Ensure uniqueness per agent-customer-key combination
            UNIQUE(agent_id, customer_id, memory_key)
        );
        """
        
        # Create indexes and trigger for updated_at
        additional_sql = [
            "CREATE INDEX IF NOT EXISTS idx_agent_memory_agent_customer ON agent_memory(agent_id, customer_id);",
            """
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql';
            """,
            """
            CREATE TRIGGER update_agent_memory_updated_at 
            BEFORE UPDATE ON agent_memory 
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            """
        ]
        
        try:
            await conn.execute(create_table_sql)
            print("✓ Created agent_memory table")
            
            for sql in additional_sql:
                await conn.execute(sql)
            print("✓ Created agent_memory table indexes and triggers")
            
        except Exception as e:
            print(f"✗ Failed to create agent_memory table: {e}")
            raise

    async def initialize_database(self) -> None:
        """Main method to initialize the complete database setup."""
        print("🚀 Starting database initialization...")
        print(f"Database: {self.database} at {self.host}:{self.port}")
        
        # Connect to PostgreSQL server
        postgres_conn = await self.connect_to_postgres()
        
        try:
            # Check if database exists, create if not
            if not await self.database_exists(postgres_conn):
                print(f"Database '{self.database}' does not exist. Creating...")
                await self.create_database(postgres_conn)
            else:
                print(f"✓ Database '{self.database}' already exists")
        finally:
            await postgres_conn.close()
        
        # Connect to application database and create tables
        app_conn = await self.connect_to_database()
        
        try:
            await self.create_conversations_table(app_conn)
            await self.create_agent_memory_table(app_conn)
            
            print("\n🎉 Database initialization completed successfully!")
            print("\nTables created:")
            print("  • conversations - stores all conversation turns")
            print("  • agent_memory - stores agent long-term memory")
            
        finally:
            await app_conn.close()


async def main():
    """Main entry point for the script."""
    print("=" * 60)
    print("  Agentic Deployment Platform - Database Initializer")
    print("=" * 60)
    
    initializer = DatabaseInitializer()
    
    try:
        await initializer.initialize_database()
    except Exception as e:
        print(f"\n💥 Database initialization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())