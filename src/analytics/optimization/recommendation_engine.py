"""
Performance Recommendation Engine

AI-powered recommendation system that analyzes system performance,
usage patterns, and provides actionable optimization insights.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Avg, Count, Sum, Max, Min
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)


@dataclass
class Recommendation:
    """Performance optimization recommendation."""
    id: str
    type: str
    category: str
    title: str
    description: str
    impact_level: str  # low, medium, high, critical
    estimated_improvement: float  # percentage
    implementation_effort: str  # low, medium, high
    priority_score: float
    estimated_cost_savings: float
    affected_components: List[str]
    action_items: List[str]
    metadata: Dict[str, Any]
    confidence_score: float


@dataclass
class PerformanceMetrics:
    """System performance metrics for analysis."""
    cpu_utilization: float
    memory_utilization: float
    network_throughput: float
    storage_usage: float
    response_time: float
    error_rate: float
    availability: float
    device_count: int
    active_content_count: int


class PerformanceRecommendationEngine:
    """
    Main recommendation engine that coordinates all optimization analyzers
    and generates comprehensive performance recommendations.
    """

    def __init__(self):
        self.analyzers = {}
        self.recommendation_rules = {}
        self.ml_models = {}
        self._load_analyzers()
        self._load_rules()
        self._initialize_ml_models()

    def _load_analyzers(self):
        """Load and initialize all performance analyzers."""
        from .analyzers import (
            DevicePerformanceAnalyzer, ContentUsageAnalyzer,
            SystemResourceAnalyzer, UserBehaviorAnalyzer, CostAnalyzer
        )

        self.analyzers = {
            'device_performance': DevicePerformanceAnalyzer(),
            'content_usage': ContentUsageAnalyzer(),
            'system_resources': SystemResourceAnalyzer(),
            'user_behavior': UserBehaviorAnalyzer(),
            'cost_optimization': CostAnalyzer()
        }

    def _load_rules(self):
        """Load optimization rules and thresholds."""
        self.recommendation_rules = {
            'cpu_threshold': {
                'warning': 70.0,
                'critical': 85.0,
                'recommendations': [
                    'scale_resources',
                    'optimize_content',
                    'load_balancing'
                ]
            },
            'memory_threshold': {
                'warning': 75.0,
                'critical': 90.0,
                'recommendations': [
                    'increase_memory',
                    'optimize_content_cache',
                    'memory_cleanup'
                ]
            },
            'device_offline_rate': {
                'warning': 5.0,  # 5% devices offline
                'critical': 10.0,
                'recommendations': [
                    'network_optimization',
                    'device_health_check',
                    'failover_setup'
                ]
            },
            'content_load_time': {
                'warning': 3000,  # 3 seconds
                'critical': 5000,  # 5 seconds
                'recommendations': [
                    'content_optimization',
                    'cdn_implementation',
                    'caching_strategy'
                ]
            },
            'cost_efficiency': {
                'warning': 60.0,  # Below 60% efficiency
                'critical': 40.0,
                'recommendations': [
                    'resource_rightsizing',
                    'usage_optimization',
                    'scheduling_optimization'
                ]
            }
        }

    def _initialize_ml_models(self):
        """Initialize machine learning models for advanced analysis."""
        self.ml_models = {
            'anomaly_detector': IsolationForest(contamination=0.1, random_state=42),
            'performance_predictor': None,  # Would be trained model
            'clustering_model': KMeans(n_clusters=5, random_state=42),
            'scaler': StandardScaler()
        }

    async def generate_recommendations(
        self,
        tenant_id: str,
        analysis_period: timedelta = timedelta(days=7)
    ) -> List[Recommendation]:
        """
        Generate comprehensive optimization recommendations for a tenant.
        """
        logger.info(f"Generating recommendations for tenant {tenant_id}")

        try:
            # Collect data from all analyzers
            analysis_data = await self._collect_analysis_data(tenant_id, analysis_period)

            # Run analysis
            recommendations = []

            # Device performance recommendations
            device_recs = await self._analyze_device_performance(
                tenant_id, analysis_data['device_data']
            )
            recommendations.extend(device_recs)

            # System resource recommendations
            resource_recs = await self._analyze_system_resources(
                tenant_id, analysis_data['resource_data']
            )
            recommendations.extend(resource_recs)

            # Content optimization recommendations
            content_recs = await self._analyze_content_usage(
                tenant_id, analysis_data['content_data']
            )
            recommendations.extend(content_recs)

            # Cost optimization recommendations
            cost_recs = await self._analyze_cost_optimization(
                tenant_id, analysis_data['billing_data']
            )
            recommendations.extend(cost_recs)

            # User behavior recommendations
            behavior_recs = await self._analyze_user_behavior(
                tenant_id, analysis_data['user_data']
            )
            recommendations.extend(behavior_recs)

            # ML-based anomaly detection
            anomaly_recs = await self._detect_anomalies(
                tenant_id, analysis_data
            )
            recommendations.extend(anomaly_recs)

            # Priority scoring and ranking
            recommendations = self._rank_recommendations(recommendations)

            # Save recommendations to database
            await self._save_recommendations(tenant_id, recommendations)

            logger.info(f"Generated {len(recommendations)} recommendations for tenant {tenant_id}")
            return recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations for tenant {tenant_id}: {e}")
            return []

    async def _collect_analysis_data(
        self,
        tenant_id: str,
        period: timedelta
    ) -> Dict[str, Any]:
        """Collect data from all analyzers for comprehensive analysis."""
        from ..models import (
            Device, DeviceMetrics, DeviceHealth, ContentView, ContentPerformance,
            SystemMetrics, ResourceUsage, UserActivity, BillingMetrics
        )

        end_time = timezone.now()
        start_time = end_time - period

        # Device data
        device_data = await self._get_device_analytics_data(tenant_id, start_time, end_time)

        # Resource data
        resource_data = await self._get_resource_analytics_data(tenant_id, start_time, end_time)

        # Content data
        content_data = await self._get_content_analytics_data(tenant_id, start_time, end_time)

        # User data
        user_data = await self._get_user_analytics_data(tenant_id, start_time, end_time)

        # Billing data
        billing_data = await self._get_billing_analytics_data(tenant_id, start_time, end_time)

        return {
            'device_data': device_data,
            'resource_data': resource_data,
            'content_data': content_data,
            'user_data': user_data,
            'billing_data': billing_data,
            'period': period,
            'start_time': start_time,
            'end_time': end_time
        }

    async def _analyze_device_performance(
        self,
        tenant_id: str,
        device_data: Dict[str, Any]
    ) -> List[Recommendation]:
        """Analyze device performance and generate recommendations."""
        recommendations = []

        try:
            # High CPU usage devices
            high_cpu_devices = device_data.get('high_cpu_devices', [])
            if high_cpu_devices:
                recommendations.append(Recommendation(
                    id=f"device_cpu_{tenant_id}_{timezone.now().timestamp()}",
                    type="performance",
                    category="device_optimization",
                    title="High CPU Usage Detected",
                    description=f"{len(high_cpu_devices)} devices showing consistently high CPU usage (>80%)",
                    impact_level="high",
                    estimated_improvement=15.0,
                    implementation_effort="medium",
                    priority_score=0.8,
                    estimated_cost_savings=500.0,
                    affected_components=[d['name'] for d in high_cpu_devices[:5]],
                    action_items=[
                        "Review content complexity on affected devices",
                        "Consider hardware upgrades for critical devices",
                        "Implement content caching strategies",
                        "Schedule content updates during off-peak hours"
                    ],
                    metadata={
                        'affected_device_count': len(high_cpu_devices),
                        'average_cpu_usage': device_data.get('avg_cpu_usage', 0),
                        'analysis_type': 'device_performance'
                    },
                    confidence_score=0.85
                ))

            # Frequent device disconnections
            unreliable_devices = device_data.get('unreliable_devices', [])
            if unreliable_devices:
                recommendations.append(Recommendation(
                    id=f"device_reliability_{tenant_id}_{timezone.now().timestamp()}",
                    type="reliability",
                    category="network_optimization",
                    title="Device Connectivity Issues",
                    description=f"{len(unreliable_devices)} devices experiencing frequent disconnections",
                    impact_level="medium",
                    estimated_improvement=20.0,
                    implementation_effort="high",
                    priority_score=0.7,
                    estimated_cost_savings=1000.0,
                    affected_components=[d['name'] for d in unreliable_devices[:5]],
                    action_items=[
                        "Check network infrastructure at affected locations",
                        "Implement device health monitoring",
                        "Configure automatic reconnection",
                        "Consider backup connectivity options"
                    ],
                    metadata={
                        'affected_device_count': len(unreliable_devices),
                        'avg_uptime': device_data.get('avg_uptime', 0),
                        'analysis_type': 'device_reliability'
                    },
                    confidence_score=0.75
                ))

            # Low device utilization
            underutilized_devices = device_data.get('underutilized_devices', [])
            if underutilized_devices:
                recommendations.append(Recommendation(
                    id=f"device_utilization_{tenant_id}_{timezone.now().timestamp()}",
                    type="efficiency",
                    category="resource_optimization",
                    title="Underutilized Devices",
                    description=f"{len(underutilized_devices)} devices showing low utilization rates",
                    impact_level="medium",
                    estimated_improvement=25.0,
                    implementation_effort="low",
                    priority_score=0.6,
                    estimated_cost_savings=2000.0,
                    affected_components=[d['name'] for d in underutilized_devices[:5]],
                    action_items=[
                        "Review content scheduling for underutilized devices",
                        "Consider consolidating content to fewer devices",
                        "Implement dynamic content allocation",
                        "Evaluate device deployment strategy"
                    ],
                    metadata={
                        'affected_device_count': len(underutilized_devices),
                        'avg_utilization': device_data.get('avg_utilization', 0),
                        'analysis_type': 'device_utilization'
                    },
                    confidence_score=0.7
                ))

        except Exception as e:
            logger.error(f"Error analyzing device performance: {e}")

        return recommendations

    async def _analyze_system_resources(
        self,
        tenant_id: str,
        resource_data: Dict[str, Any]
    ) -> List[Recommendation]:
        """Analyze system resource usage and generate recommendations."""
        recommendations = []

        try:
            # High memory usage
            if resource_data.get('avg_memory_usage', 0) > 80:
                recommendations.append(Recommendation(
                    id=f"memory_usage_{tenant_id}_{timezone.now().timestamp()}",
                    type="performance",
                    category="resource_optimization",
                    title="High Memory Usage",
                    description="System memory usage consistently above 80%",
                    impact_level="high",
                    estimated_improvement=30.0,
                    implementation_effort="medium",
                    priority_score=0.85,
                    estimated_cost_savings=1500.0,
                    affected_components=["Application Server", "Database", "Cache"],
                    action_items=[
                        "Increase system memory allocation",
                        "Optimize database queries",
                        "Implement better caching strategies",
                        "Review memory-intensive processes"
                    ],
                    metadata={
                        'current_memory_usage': resource_data.get('avg_memory_usage', 0),
                        'peak_memory_usage': resource_data.get('peak_memory_usage', 0),
                        'analysis_type': 'memory_optimization'
                    },
                    confidence_score=0.9
                ))

            # Storage optimization
            if resource_data.get('storage_usage_percentage', 0) > 75:
                recommendations.append(Recommendation(
                    id=f"storage_optimization_{tenant_id}_{timezone.now().timestamp()}",
                    type="capacity",
                    category="storage_optimization",
                    title="Storage Capacity Warning",
                    description="Storage usage above 75% capacity",
                    impact_level="medium",
                    estimated_improvement=20.0,
                    implementation_effort="low",
                    priority_score=0.65,
                    estimated_cost_savings=800.0,
                    affected_components=["Content Storage", "Database", "Logs"],
                    action_items=[
                        "Implement automated cleanup of old content",
                        "Compress stored media files",
                        "Archive historical analytics data",
                        "Set up storage monitoring alerts"
                    ],
                    metadata={
                        'current_storage_usage': resource_data.get('storage_usage_percentage', 0),
                        'storage_growth_rate': resource_data.get('storage_growth_rate', 0),
                        'analysis_type': 'storage_optimization'
                    },
                    confidence_score=0.8
                ))

        except Exception as e:
            logger.error(f"Error analyzing system resources: {e}")

        return recommendations

    async def _analyze_content_usage(
        self,
        tenant_id: str,
        content_data: Dict[str, Any]
    ) -> List[Recommendation]:
        """Analyze content usage patterns and generate optimization recommendations."""
        recommendations = []

        try:
            # Unused content
            unused_content = content_data.get('unused_content', [])
            if unused_content:
                storage_savings = sum(c.get('size_mb', 0) for c in unused_content)
                recommendations.append(Recommendation(
                    id=f"content_cleanup_{tenant_id}_{timezone.now().timestamp()}",
                    type="efficiency",
                    category="content_optimization",
                    title="Unused Content Cleanup",
                    description=f"{len(unused_content)} content items haven't been used in 30+ days",
                    impact_level="low",
                    estimated_improvement=10.0,
                    implementation_effort="low",
                    priority_score=0.4,
                    estimated_cost_savings=storage_savings * 0.1,  # Estimate storage cost
                    affected_components=["Content Library", "Storage"],
                    action_items=[
                        "Review and archive unused content",
                        "Implement content lifecycle management",
                        "Set up automated cleanup policies",
                        "Notify content owners of unused items"
                    ],
                    metadata={
                        'unused_content_count': len(unused_content),
                        'storage_savings_mb': storage_savings,
                        'analysis_type': 'content_cleanup'
                    },
                    confidence_score=0.9
                ))

            # Popular content optimization
            popular_content = content_data.get('popular_content', [])
            if popular_content:
                recommendations.append(Recommendation(
                    id=f"content_caching_{tenant_id}_{timezone.now().timestamp()}",
                    type="performance",
                    category="content_optimization",
                    title="Content Caching Optimization",
                    description=f"{len(popular_content)} highly accessed content items should be cached",
                    impact_level="medium",
                    estimated_improvement=35.0,
                    implementation_effort="medium",
                    priority_score=0.7,
                    estimated_cost_savings=1200.0,
                    affected_components=["Content Delivery", "Cache", "Network"],
                    action_items=[
                        "Implement edge caching for popular content",
                        "Pre-load frequently accessed content",
                        "Optimize content delivery network",
                        "Set up content compression"
                    ],
                    metadata={
                        'popular_content_count': len(popular_content),
                        'avg_load_time_ms': content_data.get('avg_load_time', 0),
                        'analysis_type': 'content_caching'
                    },
                    confidence_score=0.85
                ))

        except Exception as e:
            logger.error(f"Error analyzing content usage: {e}")

        return recommendations

    async def _analyze_cost_optimization(
        self,
        tenant_id: str,
        billing_data: Dict[str, Any]
    ) -> List[Recommendation]:
        """Analyze cost patterns and generate optimization recommendations."""
        recommendations = []

        try:
            # High cost per device
            cost_per_device = billing_data.get('cost_per_device', 0)
            industry_average = 50.0  # Example industry average

            if cost_per_device > industry_average * 1.2:
                recommendations.append(Recommendation(
                    id=f"cost_efficiency_{tenant_id}_{timezone.now().timestamp()}",
                    type="cost",
                    category="cost_optimization",
                    title="High Cost Per Device",
                    description=f"Cost per device (${cost_per_device:.2f}) is {((cost_per_device/industry_average - 1) * 100):.1f}% above industry average",
                    impact_level="high",
                    estimated_improvement=25.0,
                    implementation_effort="medium",
                    priority_score=0.8,
                    estimated_cost_savings=(cost_per_device - industry_average) * billing_data.get('device_count', 1),
                    affected_components=["Resource Allocation", "Usage Optimization"],
                    action_items=[
                        "Review resource allocation per device",
                        "Optimize content delivery costs",
                        "Implement usage-based scaling",
                        "Negotiate better rates with service providers"
                    ],
                    metadata={
                        'current_cost_per_device': cost_per_device,
                        'industry_average': industry_average,
                        'total_devices': billing_data.get('device_count', 0),
                        'analysis_type': 'cost_efficiency'
                    },
                    confidence_score=0.8
                ))

        except Exception as e:
            logger.error(f"Error analyzing cost optimization: {e}")

        return recommendations

    async def _analyze_user_behavior(
        self,
        tenant_id: str,
        user_data: Dict[str, Any]
    ) -> List[Recommendation]:
        """Analyze user behavior and generate optimization recommendations."""
        recommendations = []

        try:
            # Low engagement content
            low_engagement = user_data.get('low_engagement_content', [])
            if low_engagement:
                recommendations.append(Recommendation(
                    id=f"content_engagement_{tenant_id}_{timezone.now().timestamp()}",
                    type="engagement",
                    category="content_optimization",
                    title="Low Content Engagement",
                    description=f"{len(low_engagement)} content items showing low engagement rates",
                    impact_level="medium",
                    estimated_improvement=40.0,
                    implementation_effort="low",
                    priority_score=0.6,
                    estimated_cost_savings=800.0,
                    affected_components=["Content Strategy", "User Experience"],
                    action_items=[
                        "Review and refresh low-performing content",
                        "A/B test different content variations",
                        "Optimize content placement and timing",
                        "Gather user feedback on content preferences"
                    ],
                    metadata={
                        'low_engagement_count': len(low_engagement),
                        'avg_engagement_rate': user_data.get('avg_engagement_rate', 0),
                        'analysis_type': 'content_engagement'
                    },
                    confidence_score=0.75
                ))

        except Exception as e:
            logger.error(f"Error analyzing user behavior: {e}")

        return recommendations

    async def _detect_anomalies(
        self,
        tenant_id: str,
        analysis_data: Dict[str, Any]
    ) -> List[Recommendation]:
        """Use ML to detect performance anomalies and generate recommendations."""
        recommendations = []

        try:
            # Prepare data for anomaly detection
            features = self._prepare_ml_features(analysis_data)

            if len(features) > 10:  # Need sufficient data
                # Detect anomalies
                anomalies = self.ml_models['anomaly_detector'].fit_predict(features)
                anomaly_indices = np.where(anomalies == -1)[0]

                if len(anomaly_indices) > 0:
                    recommendations.append(Recommendation(
                        id=f"anomaly_detection_{tenant_id}_{timezone.now().timestamp()}",
                        type="anomaly",
                        category="system_monitoring",
                        title="Performance Anomalies Detected",
                        description=f"AI detected {len(anomaly_indices)} unusual performance patterns",
                        impact_level="medium",
                        estimated_improvement=20.0,
                        implementation_effort="high",
                        priority_score=0.65,
                        estimated_cost_savings=1000.0,
                        affected_components=["System Performance", "Monitoring"],
                        action_items=[
                            "Investigate unusual performance patterns",
                            "Review system configuration changes",
                            "Check for potential security issues",
                            "Implement enhanced monitoring"
                        ],
                        metadata={
                            'anomaly_count': len(anomaly_indices),
                            'confidence_score': 0.7,
                            'analysis_type': 'ml_anomaly_detection'
                        },
                        confidence_score=0.7
                    ))

        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")

        return recommendations

    def _prepare_ml_features(self, analysis_data: Dict[str, Any]) -> np.ndarray:
        """Prepare features for ML analysis."""
        try:
            # Extract numerical features from analysis data
            features = []

            device_data = analysis_data.get('device_data', {})
            resource_data = analysis_data.get('resource_data', {})
            content_data = analysis_data.get('content_data', {})

            # Device features
            features.extend([
                device_data.get('avg_cpu_usage', 0),
                device_data.get('avg_memory_usage', 0),
                device_data.get('avg_uptime', 0),
                device_data.get('device_count', 0),
                device_data.get('online_device_percentage', 0)
            ])

            # Resource features
            features.extend([
                resource_data.get('avg_memory_usage', 0),
                resource_data.get('storage_usage_percentage', 0),
                resource_data.get('network_throughput', 0),
                resource_data.get('response_time_ms', 0)
            ])

            # Content features
            features.extend([
                content_data.get('avg_load_time', 0),
                content_data.get('content_count', 0),
                content_data.get('avg_engagement_rate', 0),
                content_data.get('error_rate', 0)
            ])

            return np.array(features).reshape(1, -1)

        except Exception as e:
            logger.error(f"Error preparing ML features: {e}")
            return np.array([]).reshape(0, 0)

    def _rank_recommendations(self, recommendations: List[Recommendation]) -> List[Recommendation]:
        """Rank recommendations by priority score and impact."""
        try:
            # Sort by priority score (descending) and impact level
            impact_weights = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}

            def sort_key(rec):
                impact_weight = impact_weights.get(rec.impact_level, 1)
                return (rec.priority_score * impact_weight, rec.estimated_improvement)

            return sorted(recommendations, key=sort_key, reverse=True)

        except Exception as e:
            logger.error(f"Error ranking recommendations: {e}")
            return recommendations

    async def _save_recommendations(
        self,
        tenant_id: str,
        recommendations: List[Recommendation]
    ):
        """Save recommendations to database."""
        try:
            from ..models.optimization_models import OptimizationRecommendation

            for rec in recommendations:
                OptimizationRecommendation.objects.create(
                    tenant_id=tenant_id,
                    recommendation_id=rec.id,
                    type=rec.type,
                    category=rec.category,
                    title=rec.title,
                    description=rec.description,
                    impact_level=rec.impact_level,
                    estimated_improvement=rec.estimated_improvement,
                    implementation_effort=rec.implementation_effort,
                    priority_score=rec.priority_score,
                    estimated_cost_savings=rec.estimated_cost_savings,
                    affected_components=rec.affected_components,
                    action_items=rec.action_items,
                    metadata=rec.metadata,
                    confidence_score=rec.confidence_score,
                    status='pending'
                )

        except Exception as e:
            logger.error(f"Error saving recommendations: {e}")

    # Helper methods for data collection
    async def _get_device_analytics_data(self, tenant_id: str, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get device analytics data for the specified period."""
        # This would implement actual database queries
        return {
            'high_cpu_devices': [],
            'unreliable_devices': [],
            'underutilized_devices': [],
            'avg_cpu_usage': 65.0,
            'avg_uptime': 95.5,
            'avg_utilization': 78.0
        }

    async def _get_resource_analytics_data(self, tenant_id: str, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get resource analytics data for the specified period."""
        return {
            'avg_memory_usage': 75.0,
            'peak_memory_usage': 92.0,
            'storage_usage_percentage': 68.0,
            'storage_growth_rate': 5.2,
            'network_throughput': 150.0,
            'response_time_ms': 250
        }

    async def _get_content_analytics_data(self, tenant_id: str, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get content analytics data for the specified period."""
        return {
            'unused_content': [],
            'popular_content': [],
            'avg_load_time': 1500,
            'content_count': 245,
            'avg_engagement_rate': 72.5,
            'error_rate': 2.1
        }

    async def _get_user_analytics_data(self, tenant_id: str, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get user analytics data for the specified period."""
        return {
            'low_engagement_content': [],
            'avg_engagement_rate': 68.5,
            'user_activity_patterns': {}
        }

    async def _get_billing_analytics_data(self, tenant_id: str, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get billing analytics data for the specified period."""
        return {
            'cost_per_device': 45.50,
            'device_count': 25,
            'total_cost': 1137.50,
            'cost_trend': 'increasing'
        }