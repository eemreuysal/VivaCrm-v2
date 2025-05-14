"""
Management command to view and manage cache.
"""
import time
import re
import redis
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.cache import cache, caches
from typing import Dict, List, Any, Optional, Set
from pprint import pprint


class Command(BaseCommand):
    help = 'View and manage Redis cache'
    
    def add_arguments(self, parser):
        # Add commands argument
        parser.add_argument(
            'command',
            choices=['stats', 'keys', 'get', 'delete', 'flush', 'clear_pattern'],
            help='Command to execute'
        )
        
        # Add key pattern argument
        parser.add_argument(
            '--pattern',
            dest='pattern',
            help='Key pattern for keys, get, delete, or clear_pattern commands'
        )
        
        # Add cache alias argument
        parser.add_argument(
            '--cache',
            dest='cache_alias',
            default='default',
            choices=settings.CACHES.keys(),
            help='Cache alias to use'
        )
        
        # Add count argument for keys command
        parser.add_argument(
            '--count',
            dest='count',
            type=int,
            default=20,
            help='Number of keys to return (for keys command)'
        )
        
        # Add key argument for get and delete commands
        parser.add_argument(
            '--key',
            dest='key',
            help='Specific key to get or delete'
        )
    
    def handle(self, *args, **options):
        command = options['command']
        cache_alias = options['cache_alias']
        
        # Get Redis client
        try:
            redis_client = self._get_redis_client(cache_alias)
        except Exception as e:
            raise CommandError(f"Error connecting to Redis: {str(e)}")
        
        # Execute the requested command
        if command == 'stats':
            self._stats_command(redis_client, cache_alias)
        elif command == 'keys':
            self._keys_command(redis_client, options.get('pattern'), options.get('count'))
        elif command == 'get':
            self._get_command(redis_client, options.get('key'))
        elif command == 'delete':
            self._delete_command(redis_client, options.get('key'))
        elif command == 'flush':
            self._flush_command(redis_client, cache_alias)
        elif command == 'clear_pattern':
            self._clear_pattern_command(redis_client, options.get('pattern'))
    
    def _get_redis_client(self, cache_alias):
        """
        Get a Redis client for the specified cache alias.
        """
        # Check if the cache backend is Redis
        if not settings.CACHES[cache_alias]['BACKEND'].endswith('.RedisCache'):
            raise CommandError(f"Cache backend for {cache_alias} is not Redis")
        
        # Get location
        location = settings.CACHES[cache_alias]['LOCATION']
        
        # Parse Redis URL
        pattern = r'redis://(?:(?P<username>.*):(?P<password>.*)@)?(?P<host>.*):(?P<port>\d+)(?:/(?P<db>\d+))?'
        match = re.match(pattern, location)
        
        if not match:
            raise CommandError(f"Invalid Redis URL: {location}")
        
        host = match.group('host') or 'localhost'
        port = int(match.group('port') or 6379)
        db = int(match.group('db') or 0)
        username = match.group('username')
        password = match.group('password')
        
        # Create Redis client
        return redis.Redis(
            host=host,
            port=port,
            db=db,
            username=username,
            password=password,
            decode_responses=True  # Decode responses to strings
        )
    
    def _stats_command(self, redis_client, cache_alias):
        """
        Display cache statistics.
        """
        # Get Redis info
        info = redis_client.info()
        
        # Extract relevant stats
        stats = {
            'used_memory_human': info.get('used_memory_human', 'N/A'),
            'used_memory_peak_human': info.get('used_memory_peak_human', 'N/A'),
            'total_connections_received': info.get('total_connections_received', 'N/A'),
            'total_commands_processed': info.get('total_commands_processed', 'N/A'),
            'keyspace_hits': info.get('keyspace_hits', 'N/A'),
            'keyspace_misses': info.get('keyspace_misses', 'N/A'),
            'uptime_in_days': info.get('uptime_in_days', 'N/A'),
            'db_size': redis_client.dbsize(),
        }
        
        # Calculate hit ratio
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)
        total = hits + misses
        hit_ratio = (hits / total * 100) if total > 0 else 0
        stats['hit_ratio'] = f"{hit_ratio:.2f}%"
        
        # Get expiring keys count
        prefix = settings.CACHES[cache_alias].get('OPTIONS', {}).get('KEY_PREFIX', '')
        expiring_keys = 0
        pattern = f"{prefix}*" if prefix else "*"
        
        for key in redis_client.scan_iter(match=pattern):
            ttl = redis_client.ttl(key)
            if ttl > 0:
                expiring_keys += 1
        
        stats['expiring_keys'] = expiring_keys
        
        # Display stats
        self.stdout.write(self.style.SUCCESS(f"Cache Statistics for '{cache_alias}':"))
        for key, value in stats.items():
            self.stdout.write(f"  {key}: {value}")
    
    def _keys_command(self, redis_client, pattern, count):
        """
        Display keys matching a pattern.
        """
        # Set default pattern if not provided
        if not pattern:
            pattern = "*"
        
        self.stdout.write(self.style.SUCCESS(f"Keys matching pattern '{pattern}':"))
        
        # Get keys matching pattern
        keys = []
        for key in redis_client.scan_iter(match=pattern, count=100):
            keys.append(key)
            if len(keys) >= count:
                break
        
        # Display keys with TTL
        for key in keys:
            ttl = redis_client.ttl(key)
            if ttl > 0:
                self.stdout.write(f"  {key} (TTL: {ttl}s)")
            elif ttl == -1:
                self.stdout.write(f"  {key} (No expiration)")
            else:
                self.stdout.write(f"  {key} (Expired)")
        
        self.stdout.write(f"Found {len(keys)} keys (limited to {count})")
    
    def _get_command(self, redis_client, key):
        """
        Get the value of a key.
        """
        if not key:
            raise CommandError("Key argument is required for get command")
        
        # Get the value
        value = redis_client.get(key)
        
        if value is None:
            self.stdout.write(self.style.WARNING(f"Key '{key}' not found"))
            return
        
        # Get TTL
        ttl = redis_client.ttl(key)
        ttl_str = f"TTL: {ttl}s" if ttl > 0 else "No expiration" if ttl == -1 else "Expired"
        
        # Display the value
        self.stdout.write(self.style.SUCCESS(f"Value for key '{key}' ({ttl_str}):"))
        self.stdout.write(value)
    
    def _delete_command(self, redis_client, key):
        """
        Delete a key.
        """
        if not key:
            raise CommandError("Key argument is required for delete command")
        
        # Delete the key
        deleted = redis_client.delete(key)
        
        if deleted:
            self.stdout.write(self.style.SUCCESS(f"Deleted key '{key}'"))
        else:
            self.stdout.write(self.style.WARNING(f"Key '{key}' not found"))
    
    def _flush_command(self, redis_client, cache_alias):
        """
        Flush all keys in the cache.
        """
        # Confirm action
        self.stdout.write(self.style.WARNING(
            f"This will delete ALL keys in the '{cache_alias}' cache!"
        ))
        confirm = input("Are you sure you want to continue? [y/N] ")
        
        if confirm.lower() != 'y':
            self.stdout.write(self.style.SUCCESS("Operation cancelled"))
            return
        
        # Flush the database
        redis_client.flushdb()
        self.stdout.write(self.style.SUCCESS(f"Flushed all keys in '{cache_alias}' cache"))
    
    def _clear_pattern_command(self, redis_client, pattern):
        """
        Delete all keys matching a pattern.
        """
        if not pattern:
            raise CommandError("Pattern argument is required for clear_pattern command")
        
        # Confirm action
        self.stdout.write(self.style.WARNING(
            f"This will delete all keys matching pattern '{pattern}'!"
        ))
        confirm = input("Are you sure you want to continue? [y/N] ")
        
        if confirm.lower() != 'y':
            self.stdout.write(self.style.SUCCESS("Operation cancelled"))
            return
        
        # Find and delete keys
        deleted_count = 0
        for key in redis_client.scan_iter(match=pattern):
            redis_client.delete(key)
            deleted_count += 1
        
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted_count} keys matching '{pattern}'"))