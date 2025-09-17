# Plugin Architecture Framework
# Extensible plugin system for Anthias SaaS platform

import importlib
import inspect
import json
import os
import sys
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type, Callable
from pathlib import Path
from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)


# Base Plugin Interface
class BasePlugin(ABC):
    """Base plugin interface that all plugins must implement"""

    # Plugin metadata
    name: str = ""
    version: str = "1.0.0"
    description: str = ""
    author: str = ""
    author_email: str = ""
    requires: List[str] = []  # List of required dependencies
    min_anthias_version: str = "0.18.0"
    max_anthias_version: str = ""

    # Plugin configuration
    config_schema: Dict[str, Any] = {}
    default_config: Dict[str, Any] = {}

    def __init__(self, config: Dict[str, Any] = None):
        self.config = {**self.default_config, **(config or {})}
        self.logger = logging.getLogger(f"plugin.{self.name}")
        self._hooks = {}

    @abstractmethod
    def initialize(self) -> bool:
        """Initialize the plugin. Return True if successful."""
        pass

    @abstractmethod
    def shutdown(self) -> bool:
        """Shutdown the plugin. Return True if successful."""
        pass

    def get_info(self) -> Dict[str, Any]:
        """Get plugin information"""
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'author_email': self.author_email,
            'requires': self.requires,
            'min_anthias_version': self.min_anthias_version,
            'max_anthias_version': self.max_anthias_version,
            'config_schema': self.config_schema
        }

    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate plugin configuration. Return list of errors."""
        errors = []
        # Basic validation based on config_schema
        for key, schema in self.config_schema.items():
            if schema.get('required', False) and key not in config:
                errors.append(f"Required config key '{key}' is missing")

            if key in config:
                expected_type = schema.get('type')
                if expected_type and not isinstance(config[key], expected_type):
                    errors.append(f"Config key '{key}' should be of type {expected_type.__name__}")

        return errors

    def register_hook(self, hook_name: str, callback: Callable):
        """Register a hook callback"""
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        self._hooks[hook_name].append(callback)

    def execute_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Execute all callbacks for a hook"""
        results = []
        for callback in self._hooks.get(hook_name, []):
            try:
                result = callback(*args, **kwargs)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Hook '{hook_name}' callback failed: {str(e)}")
        return results


# Specific Plugin Types
class AssetProcessorPlugin(BasePlugin):
    """Plugin for processing assets (transcoding, optimization, etc.)"""

    @abstractmethod
    def can_process(self, asset: 'Asset') -> bool:
        """Check if this plugin can process the given asset"""
        pass

    @abstractmethod
    def process_asset(self, asset: 'Asset') -> Dict[str, Any]:
        """Process the asset. Return processing result."""
        pass

    def get_supported_mimetypes(self) -> List[str]:
        """Get list of supported MIME types"""
        return []


class AuthenticationPlugin(BasePlugin):
    """Plugin for external authentication providers"""

    @abstractmethod
    def authenticate(self, credentials: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Authenticate user with external provider"""
        pass

    @abstractmethod
    def get_user_info(self, external_user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information from external provider"""
        pass


class StoragePlugin(BasePlugin):
    """Plugin for external storage providers"""

    @abstractmethod
    def upload_file(self, file_path: str, destination: str) -> str:
        """Upload file to external storage"""
        pass

    @abstractmethod
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download file from external storage"""
        pass

    @abstractmethod
    def delete_file(self, remote_path: str) -> bool:
        """Delete file from external storage"""
        pass

    @abstractmethod
    def get_file_url(self, remote_path: str, expires_in: int = 3600) -> str:
        """Get public URL for file"""
        pass


class NotificationPlugin(BasePlugin):
    """Plugin for sending notifications"""

    @abstractmethod
    def send_notification(self, recipient: str, message: str, **kwargs) -> bool:
        """Send notification to recipient"""
        pass

    def get_supported_channels(self) -> List[str]:
        """Get supported notification channels"""
        return []


class AnalyticsPlugin(BasePlugin):
    """Plugin for analytics and reporting"""

    @abstractmethod
    def track_event(self, event_name: str, properties: Dict[str, Any]) -> bool:
        """Track analytics event"""
        pass

    @abstractmethod
    def get_dashboard_data(self, tenant_id: str, date_range: Dict) -> Dict[str, Any]:
        """Get dashboard analytics data"""
        pass


# Plugin Registry
class PluginRegistry:
    """Central registry for managing plugins"""

    def __init__(self):
        self._plugins: Dict[str, BasePlugin] = {}
        self._plugin_types: Dict[str, List[str]] = {}
        self._active_plugins: Dict[str, bool] = {}
        self._plugin_configs: Dict[str, Dict] = {}

    def register_plugin(self, plugin_class: Type[BasePlugin], config: Dict = None) -> bool:
        """Register a plugin class"""
        try:
            # Validate plugin class
            if not issubclass(plugin_class, BasePlugin):
                raise ValueError("Plugin must inherit from BasePlugin")

            # Check if plugin already registered
            if plugin_class.name in self._plugins:
                logger.warning(f"Plugin '{plugin_class.name}' already registered")
                return False

            # Validate configuration
            plugin_instance = plugin_class(config)
            config_errors = plugin_instance.validate_config(plugin_instance.config)
            if config_errors:
                raise ValueError(f"Plugin config validation failed: {config_errors}")

            # Register plugin
            self._plugins[plugin_class.name] = plugin_instance
            self._plugin_configs[plugin_class.name] = config or {}
            self._active_plugins[plugin_class.name] = False

            # Track plugin types
            plugin_type = self._get_plugin_type(plugin_class)
            if plugin_type not in self._plugin_types:
                self._plugin_types[plugin_type] = []
            self._plugin_types[plugin_type].append(plugin_class.name)

            logger.info(f"Registered plugin: {plugin_class.name} v{plugin_class.version}")
            return True

        except Exception as e:
            logger.error(f"Failed to register plugin {plugin_class.name}: {str(e)}")
            return False

    def unregister_plugin(self, plugin_name: str) -> bool:
        """Unregister a plugin"""
        if plugin_name not in self._plugins:
            return False

        try:
            # Deactivate if active
            if self._active_plugins.get(plugin_name):
                self.deactivate_plugin(plugin_name)

            # Remove from registry
            del self._plugins[plugin_name]
            del self._plugin_configs[plugin_name]
            del self._active_plugins[plugin_name]

            # Remove from type tracking
            for plugin_type, plugins in self._plugin_types.items():
                if plugin_name in plugins:
                    plugins.remove(plugin_name)

            logger.info(f"Unregistered plugin: {plugin_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to unregister plugin {plugin_name}: {str(e)}")
            return False

    def activate_plugin(self, plugin_name: str) -> bool:
        """Activate a plugin"""
        if plugin_name not in self._plugins:
            logger.error(f"Plugin '{plugin_name}' not found")
            return False

        if self._active_plugins.get(plugin_name):
            logger.warning(f"Plugin '{plugin_name}' already active")
            return True

        try:
            plugin = self._plugins[plugin_name]

            # Check dependencies
            if not self._check_dependencies(plugin):
                logger.error(f"Plugin '{plugin_name}' dependencies not met")
                return False

            # Initialize plugin
            if plugin.initialize():
                self._active_plugins[plugin_name] = True
                logger.info(f"Activated plugin: {plugin_name}")

                # Store activation state
                self._store_plugin_state(plugin_name, True)
                return True
            else:
                logger.error(f"Plugin '{plugin_name}' initialization failed")
                return False

        except Exception as e:
            logger.error(f"Failed to activate plugin {plugin_name}: {str(e)}")
            return False

    def deactivate_plugin(self, plugin_name: str) -> bool:
        """Deactivate a plugin"""
        if plugin_name not in self._plugins:
            return False

        if not self._active_plugins.get(plugin_name):
            return True

        try:
            plugin = self._plugins[plugin_name]

            # Shutdown plugin
            if plugin.shutdown():
                self._active_plugins[plugin_name] = False
                logger.info(f"Deactivated plugin: {plugin_name}")

                # Store deactivation state
                self._store_plugin_state(plugin_name, False)
                return True
            else:
                logger.error(f"Plugin '{plugin_name}' shutdown failed")
                return False

        except Exception as e:
            logger.error(f"Failed to deactivate plugin {plugin_name}: {str(e)}")
            return False

    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """Get plugin instance"""
        return self._plugins.get(plugin_name)

    def get_active_plugins(self, plugin_type: Type[BasePlugin] = None) -> List[BasePlugin]:
        """Get all active plugins, optionally filtered by type"""
        active_plugins = []

        for plugin_name, is_active in self._active_plugins.items():
            if is_active:
                plugin = self._plugins[plugin_name]
                if plugin_type is None or isinstance(plugin, plugin_type):
                    active_plugins.append(plugin)

        return active_plugins

    def get_plugins_by_type(self, plugin_type: str) -> List[str]:
        """Get plugin names by type"""
        return self._plugin_types.get(plugin_type, [])

    def list_plugins(self) -> Dict[str, Dict]:
        """List all registered plugins with their status"""
        result = {}
        for plugin_name, plugin in self._plugins.items():
            result[plugin_name] = {
                **plugin.get_info(),
                'active': self._active_plugins.get(plugin_name, False),
                'config': self._plugin_configs.get(plugin_name, {})
            }
        return result

    def _get_plugin_type(self, plugin_class: Type[BasePlugin]) -> str:
        """Determine plugin type from class inheritance"""
        if issubclass(plugin_class, AssetProcessorPlugin):
            return 'asset_processor'
        elif issubclass(plugin_class, AuthenticationPlugin):
            return 'authentication'
        elif issubclass(plugin_class, StoragePlugin):
            return 'storage'
        elif issubclass(plugin_class, NotificationPlugin):
            return 'notification'
        elif issubclass(plugin_class, AnalyticsPlugin):
            return 'analytics'
        else:
            return 'generic'

    def _check_dependencies(self, plugin: BasePlugin) -> bool:
        """Check if plugin dependencies are met"""
        for dependency in plugin.requires:
            try:
                importlib.import_module(dependency)
            except ImportError:
                logger.error(f"Missing dependency: {dependency}")
                return False
        return True

    def _store_plugin_state(self, plugin_name: str, is_active: bool):
        """Store plugin activation state"""
        cache_key = f"plugin_state_{plugin_name}"
        cache.set(cache_key, is_active, timeout=None)  # No expiry


# Plugin Manager
class PluginManager:
    """High-level plugin management"""

    def __init__(self):
        self.registry = PluginRegistry()
        self._hooks: Dict[str, List[Callable]] = {}

    def load_plugins_from_directory(self, directory: str) -> Dict[str, bool]:
        """Load plugins from a directory"""
        results = {}
        plugin_dir = Path(directory)

        if not plugin_dir.exists():
            logger.warning(f"Plugin directory does not exist: {directory}")
            return results

        for plugin_file in plugin_dir.glob("*.py"):
            if plugin_file.name.startswith("__"):
                continue

            try:
                # Import module
                spec = importlib.util.spec_from_file_location(
                    plugin_file.stem, plugin_file
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Find plugin classes
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, BasePlugin) and
                        obj != BasePlugin and
                        hasattr(obj, 'name') and
                        obj.name):

                        # Load plugin config
                        config_file = plugin_dir / f"{plugin_file.stem}.json"
                        config = {}
                        if config_file.exists():
                            with open(config_file) as f:
                                config = json.load(f)

                        # Register plugin
                        success = self.registry.register_plugin(obj, config)
                        results[obj.name] = success

            except Exception as e:
                logger.error(f"Failed to load plugin from {plugin_file}: {str(e)}")
                results[plugin_file.stem] = False

        return results

    def install_plugin_from_package(self, package_path: str) -> bool:
        """Install plugin from package (zip file or directory)"""
        # Implementation for installing plugins from packages
        # This would handle plugin validation, dependency checking, etc.
        pass

    def register_hook(self, hook_name: str, callback: Callable, priority: int = 0):
        """Register a system hook"""
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []

        self._hooks[hook_name].append({
            'callback': callback,
            'priority': priority
        })

        # Sort by priority (higher priority first)
        self._hooks[hook_name].sort(key=lambda x: x['priority'], reverse=True)

    def execute_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """Execute system hook and plugin hooks"""
        results = []

        # Execute system hooks first
        for hook_info in self._hooks.get(hook_name, []):
            try:
                result = hook_info['callback'](*args, **kwargs)
                results.append(result)
            except Exception as e:
                logger.error(f"System hook '{hook_name}' failed: {str(e)}")

        # Execute plugin hooks
        for plugin in self.registry.get_active_plugins():
            try:
                plugin_results = plugin.execute_hook(hook_name, *args, **kwargs)
                results.extend(plugin_results)
            except Exception as e:
                logger.error(f"Plugin hook '{hook_name}' failed for {plugin.name}: {str(e)}")

        return results

    def get_plugins_for_asset(self, asset: 'Asset') -> List[AssetProcessorPlugin]:
        """Get plugins that can process a specific asset"""
        processors = []
        for plugin in self.registry.get_active_plugins(AssetProcessorPlugin):
            if plugin.can_process(asset):
                processors.append(plugin)
        return processors


# Plugin Configuration Model
class PluginConfiguration(models.Model):
    """Model for storing plugin configurations"""
    plugin_name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=False)
    config = models.JSONField(default=dict)
    installed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    installed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'plugin_configurations'


# Example Plugins
class SlackNotificationPlugin(NotificationPlugin):
    """Example Slack notification plugin"""

    name = "slack_notifications"
    version = "1.0.0"
    description = "Send notifications via Slack"
    author = "Anthias Team"

    config_schema = {
        'webhook_url': {'type': str, 'required': True},
        'default_channel': {'type': str, 'required': False}
    }

    default_config = {
        'default_channel': '#general'
    }

    def initialize(self) -> bool:
        """Initialize Slack plugin"""
        if not self.config.get('webhook_url'):
            self.logger.error("Slack webhook URL not configured")
            return False

        self.logger.info("Slack notification plugin initialized")
        return True

    def shutdown(self) -> bool:
        """Shutdown Slack plugin"""
        self.logger.info("Slack notification plugin shutdown")
        return True

    def send_notification(self, recipient: str, message: str, **kwargs) -> bool:
        """Send Slack notification"""
        import requests

        try:
            channel = kwargs.get('channel', self.config['default_channel'])
            payload = {
                'text': message,
                'channel': channel,
                'username': kwargs.get('username', 'Anthias')
            }

            response = requests.post(
                self.config['webhook_url'],
                json=payload,
                timeout=10
            )

            return response.status_code == 200

        except Exception as e:
            self.logger.error(f"Failed to send Slack notification: {str(e)}")
            return False

    def get_supported_channels(self) -> List[str]:
        return ['slack']


class S3StoragePlugin(StoragePlugin):
    """Example S3 storage plugin"""

    name = "s3_storage"
    version = "1.0.0"
    description = "Store files in Amazon S3"
    author = "Anthias Team"
    requires = ['boto3']

    config_schema = {
        'bucket_name': {'type': str, 'required': True},
        'access_key': {'type': str, 'required': True},
        'secret_key': {'type': str, 'required': True},
        'region': {'type': str, 'required': False}
    }

    default_config = {
        'region': 'us-east-1'
    }

    def initialize(self) -> bool:
        """Initialize S3 plugin"""
        try:
            import boto3
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.config['access_key'],
                aws_secret_access_key=self.config['secret_key'],
                region_name=self.config['region']
            )

            # Test connection
            self.s3_client.head_bucket(Bucket=self.config['bucket_name'])
            self.logger.info("S3 storage plugin initialized")
            return True

        except Exception as e:
            self.logger.error(f"S3 plugin initialization failed: {str(e)}")
            return False

    def shutdown(self) -> bool:
        """Shutdown S3 plugin"""
        self.s3_client = None
        return True

    def upload_file(self, file_path: str, destination: str) -> str:
        """Upload file to S3"""
        try:
            self.s3_client.upload_file(
                file_path,
                self.config['bucket_name'],
                destination
            )
            return f"s3://{self.config['bucket_name']}/{destination}"

        except Exception as e:
            self.logger.error(f"S3 upload failed: {str(e)}")
            raise

    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download file from S3"""
        try:
            self.s3_client.download_file(
                self.config['bucket_name'],
                remote_path,
                local_path
            )
            return True

        except Exception as e:
            self.logger.error(f"S3 download failed: {str(e)}")
            return False

    def delete_file(self, remote_path: str) -> bool:
        """Delete file from S3"""
        try:
            self.s3_client.delete_object(
                Bucket=self.config['bucket_name'],
                Key=remote_path
            )
            return True

        except Exception as e:
            self.logger.error(f"S3 delete failed: {str(e)}")
            return False

    def get_file_url(self, remote_path: str, expires_in: int = 3600) -> str:
        """Get presigned URL for S3 file"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.config['bucket_name'],
                    'Key': remote_path
                },
                ExpiresIn=expires_in
            )
            return url

        except Exception as e:
            self.logger.error(f"S3 URL generation failed: {str(e)}")
            raise


# Plugin Management API Views
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class PluginManagementView(APIView):
    """API for managing plugins"""

    def __init__(self):
        super().__init__()
        self.plugin_manager = PluginManager()

    def get(self, request):
        """List all plugins"""
        plugins = self.plugin_manager.registry.list_plugins()
        return Response(plugins)

    def post(self, request):
        """Install or activate plugin"""
        action = request.data.get('action')
        plugin_name = request.data.get('plugin_name')

        if action == 'activate':
            success = self.plugin_manager.registry.activate_plugin(plugin_name)
            return Response({
                'success': success,
                'message': f"Plugin {plugin_name} {'activated' if success else 'activation failed'}"
            })

        elif action == 'deactivate':
            success = self.plugin_manager.registry.deactivate_plugin(plugin_name)
            return Response({
                'success': success,
                'message': f"Plugin {plugin_name} {'deactivated' if success else 'deactivation failed'}"
            })

        return Response(
            {'error': 'Invalid action'},
            status=status.HTTP_400_BAD_REQUEST
        )


# Global plugin manager instance
plugin_manager = PluginManager()

# Django integration
def load_plugins_at_startup():
    """Load plugins during Django startup"""
    plugins_dir = getattr(settings, 'PLUGINS_DIRECTORY', 'plugins')
    plugin_manager.load_plugins_from_directory(plugins_dir)

    # Auto-activate plugins that were previously active
    for plugin_name in plugin_manager.registry._plugins.keys():
        cache_key = f"plugin_state_{plugin_name}"
        was_active = cache.get(cache_key, False)
        if was_active:
            plugin_manager.registry.activate_plugin(plugin_name)


# Hook definitions for core system
CORE_HOOKS = [
    'asset_created',
    'asset_updated',
    'asset_deleted',
    'user_logged_in',
    'user_logged_out',
    'subscription_created',
    'subscription_updated',
    'qr_content_accessed',
    'file_uploaded',
    'file_deleted'
]