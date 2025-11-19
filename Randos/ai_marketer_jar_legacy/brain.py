#!/usr/bin/env python3
"""
AI MARKETER JAR - Core Brain System
Three-layer memory architecture with encrypted credential storage
"""

import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import base64
import hashlib


class MarketingBrain:
    """Core brain system with three-layer memory architecture"""
    
    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # Initialize encryption for L3
        self.cipher_suite = self._init_encryption()
        
        # Initialize all three memory layers
        self._init_l1_memory()  # Working memory (in-memory dict)
        self._init_l2_memory()  # Session memory (SQLite)
        self._init_l3_memory()  # Encrypted credentials (encrypted SQLite)
        
    def _init_encryption(self) -> Fernet:
        """Initialize encryption system for L3 memory"""
        # Generate or load encryption key
        key_file = self.data_dir / ".encryption_key"
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                key = f.read()
        else:
            # Generate a new key based on system entropy
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions
            os.chmod(key_file, 0o600)
            
        return Fernet(key)
    
    def _init_l1_memory(self):
        """Initialize L1 - Working Memory (temporary, in-memory)"""
        self.l1_memory = {
            'current_campaign': None,
            'active_workflows': [],
            'temp_data': {},
            'cache': {},
            'session_start': datetime.now().isoformat()
        }
        
    def _init_l2_memory(self):
        """Initialize L2 - Session Memory (campaign history, analytics)"""
        db_path = self.data_dir / "l2_session.db"
        self.l2_conn = sqlite3.connect(str(db_path))
        self.l2_conn.row_factory = sqlite3.Row
        
        cursor = self.l2_conn.cursor()
        
        # Campaign history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS campaigns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id TEXT UNIQUE NOT NULL,
                platform TEXT NOT NULL,
                campaign_name TEXT,
                status TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                metrics TEXT,
                settings TEXT
            )
        """)
        
        # Analytics data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                campaign_id TEXT,
                metric_type TEXT,
                value REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """)
        
        # Workflow history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS workflows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow_id TEXT UNIQUE NOT NULL,
                name TEXT,
                type TEXT,
                status TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                executed_at DATETIME,
                result TEXT
            )
        """)
        
        self.l2_conn.commit()
        
    def _init_l3_memory(self):
        """Initialize L3 - Encrypted Credential Storage"""
        db_path = self.data_dir / "l3_secure.db"
        self.l3_conn = sqlite3.connect(str(db_path))
        self.l3_conn.row_factory = sqlite3.Row
        
        # Set restrictive permissions on the database file
        os.chmod(db_path, 0o600)
        
        cursor = self.l3_conn.cursor()
        
        # Encrypted credentials table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service TEXT UNIQUE NOT NULL,
                encrypted_data TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_used DATETIME,
                checksum TEXT NOT NULL
            )
        """)
        
        # Access log for security auditing
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS access_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service TEXT,
                action TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN
            )
        """)
        
        self.l3_conn.commit()
    
    # L1 Memory Operations (Working Memory)
    def set_working_data(self, key: str, value: Any) -> None:
        """Store temporary data in L1 working memory"""
        self.l1_memory['temp_data'][key] = value
        
    def get_working_data(self, key: str) -> Any:
        """Retrieve data from L1 working memory"""
        return self.l1_memory['temp_data'].get(key)
    
    def clear_working_memory(self) -> None:
        """Clear L1 working memory (except session info)"""
        session_start = self.l1_memory['session_start']
        self._init_l1_memory()
        self.l1_memory['session_start'] = session_start
    
    # L2 Memory Operations (Session/Campaign History)
    def save_campaign(self, campaign_data: Dict) -> str:
        """Save campaign data to L2 session memory"""
        cursor = self.l2_conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO campaigns 
            (campaign_id, platform, campaign_name, status, metrics, settings, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            campaign_data['campaign_id'],
            campaign_data['platform'],
            campaign_data.get('campaign_name', ''),
            campaign_data.get('status', 'active'),
            json.dumps(campaign_data.get('metrics', {})),
            json.dumps(campaign_data.get('settings', {})),
            datetime.now().isoformat()
        ))
        
        self.l2_conn.commit()
        return campaign_data['campaign_id']
    
    def get_campaign_history(self, platform: Optional[str] = None, limit: int = 10) -> List[Dict]:
        """Retrieve campaign history from L2"""
        cursor = self.l2_conn.cursor()
        
        if platform:
            cursor.execute("""
                SELECT * FROM campaigns 
                WHERE platform = ?
                ORDER BY updated_at DESC
                LIMIT ?
            """, (platform, limit))
        else:
            cursor.execute("""
                SELECT * FROM campaigns 
                ORDER BY updated_at DESC
                LIMIT ?
            """, (limit,))
        
        campaigns = []
        for row in cursor.fetchall():
            campaign = dict(row)
            campaign['metrics'] = json.loads(campaign['metrics'])
            campaign['settings'] = json.loads(campaign['settings'])
            campaigns.append(campaign)
            
        return campaigns
    
    def save_analytics(self, campaign_id: str, metric_type: str, value: float, metadata: Dict = None) -> None:
        """Save analytics data to L2"""
        cursor = self.l2_conn.cursor()
        
        cursor.execute("""
            INSERT INTO analytics (campaign_id, metric_type, value, metadata)
            VALUES (?, ?, ?, ?)
        """, (
            campaign_id,
            metric_type,
            value,
            json.dumps(metadata or {})
        ))
        
        self.l2_conn.commit()
    
    # L3 Memory Operations (Encrypted Credentials)
    def store_credential(self, service: str, credentials: Dict) -> bool:
        """Store encrypted credentials in L3 memory"""
        try:
            # Serialize and encrypt the credentials
            cred_json = json.dumps(credentials)
            encrypted_data = self.cipher_suite.encrypt(cred_json.encode())
            
            # Create checksum for integrity verification
            checksum = hashlib.sha256(cred_json.encode()).hexdigest()
            
            cursor = self.l3_conn.cursor()
            
            # Store encrypted credentials
            cursor.execute("""
                INSERT OR REPLACE INTO credentials 
                (service, encrypted_data, checksum)
                VALUES (?, ?, ?)
            """, (service, encrypted_data.decode(), checksum))
            
            # Log the access
            cursor.execute("""
                INSERT INTO access_log (service, action, success)
                VALUES (?, 'store', 1)
            """, (service,))
            
            self.l3_conn.commit()
            return True
            
        except Exception as e:
            # Log failed access attempt
            cursor = self.l3_conn.cursor()
            cursor.execute("""
                INSERT INTO access_log (service, action, success)
                VALUES (?, 'store', 0)
            """, (service,))
            self.l3_conn.commit()
            return False
    
    def retrieve_credential(self, service: str) -> Optional[Dict]:
        """Retrieve and decrypt credentials from L3 memory"""
        try:
            cursor = self.l3_conn.cursor()
            
            # Fetch encrypted credentials
            cursor.execute("""
                SELECT encrypted_data, checksum FROM credentials
                WHERE service = ?
            """, (service,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # Decrypt the data
            encrypted_data = row['encrypted_data'].encode()
            decrypted_json = self.cipher_suite.decrypt(encrypted_data).decode()
            
            # Verify integrity
            checksum = hashlib.sha256(decrypted_json.encode()).hexdigest()
            if checksum != row['checksum']:
                raise ValueError("Credential integrity check failed")
            
            # Update last used timestamp
            cursor.execute("""
                UPDATE credentials 
                SET last_used = ?
                WHERE service = ?
            """, (datetime.now().isoformat(), service))
            
            # Log successful access
            cursor.execute("""
                INSERT INTO access_log (service, action, success)
                VALUES (?, 'retrieve', 1)
            """, (service,))
            
            self.l3_conn.commit()
            
            return json.loads(decrypted_json)
            
        except Exception as e:
            # Log failed access attempt
            cursor = self.l3_conn.cursor()
            cursor.execute("""
                INSERT INTO access_log (service, action, success)
                VALUES (?, 'retrieve', 0)
            """, (service,))
            self.l3_conn.commit()
            return None
    
    def list_stored_services(self) -> List[str]:
        """List services with stored credentials (without exposing the credentials)"""
        cursor = self.l3_conn.cursor()
        cursor.execute("""
            SELECT service, created_at, last_used 
            FROM credentials
            ORDER BY last_used DESC
        """)
        
        return [
            {
                'service': row['service'],
                'created_at': row['created_at'],
                'last_used': row['last_used']
            }
            for row in cursor.fetchall()
        ]
    
    def remove_credential(self, service: str) -> bool:
        """Remove credentials for a service"""
        try:
            cursor = self.l3_conn.cursor()
            
            cursor.execute("""
                DELETE FROM credentials WHERE service = ?
            """, (service,))
            
            # Log the removal
            cursor.execute("""
                INSERT INTO access_log (service, action, success)
                VALUES (?, 'remove', 1)
            """, (service,))
            
            self.l3_conn.commit()
            return True
            
        except Exception:
            return False
    
    def get_memory_stats(self) -> Dict:
        """Get statistics about all memory layers"""
        stats = {
            'l1_working': {
                'active_workflows': len(self.l1_memory['active_workflows']),
                'temp_data_keys': len(self.l1_memory['temp_data']),
                'session_start': self.l1_memory['session_start']
            },
            'l2_session': {},
            'l3_secure': {}
        }
        
        # L2 stats
        cursor = self.l2_conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM campaigns")
        stats['l2_session']['campaigns'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM analytics")
        stats['l2_session']['analytics_records'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM workflows")
        stats['l2_session']['workflows'] = cursor.fetchone()['count']
        
        # L3 stats (limited info for security)
        cursor = self.l3_conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM credentials")
        stats['l3_secure']['stored_services'] = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM access_log WHERE timestamp > ?",
                      ((datetime.now() - timedelta(days=1)).isoformat(),))
        stats['l3_secure']['access_attempts_24h'] = cursor.fetchone()['count']
        
        return stats
    
    def close(self):
        """Close all database connections"""
        self.l2_conn.close()
        self.l3_conn.close()