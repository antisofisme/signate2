"""
Performance Optimization Package

AI-powered performance optimization recommendations for digital signage systems.
Analyzes usage patterns, device performance, and system metrics to provide
actionable optimization insights.
"""

from .recommendation_engine import (
    PerformanceRecommendationEngine, OptimizationAnalyzer,
    CostOptimizationEngine, ContentOptimizationEngine
)
from .models import (
    OptimizationRecommendation, PerformanceInsight, OptimizationRule,
    OptimizationExecution, BenchmarkData
)
from .analyzers import (
    DevicePerformanceAnalyzer, ContentUsageAnalyzer, SystemResourceAnalyzer,
    UserBehaviorAnalyzer, CostAnalyzer
)

__all__ = [
    # Engines
    'PerformanceRecommendationEngine', 'OptimizationAnalyzer',
    'CostOptimizationEngine', 'ContentOptimizationEngine',

    # Models
    'OptimizationRecommendation', 'PerformanceInsight', 'OptimizationRule',
    'OptimizationExecution', 'BenchmarkData',

    # Analyzers
    'DevicePerformanceAnalyzer', 'ContentUsageAnalyzer', 'SystemResourceAnalyzer',
    'UserBehaviorAnalyzer', 'CostAnalyzer'
]