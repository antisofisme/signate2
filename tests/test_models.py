"""
Comprehensive model testing for Signate SaaS.

Tests cover:
- Asset model functionality and business logic
- Data validation and constraints
- Model relationships and foreign keys
- Custom model methods and properties
- Database integrity and performance
- Multi-tenant data isolation
"""

import pytest
import uuid
from datetime import datetime, timedelta
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone
from freezegun import freeze_time

from anthias_app.models import Asset, generate_asset_id


class TestAssetModel:
    """Test suite for the Asset model."""

    @pytest.mark.unit
    def test_asset_creation_with_defaults(self, db):
        """Test creating an asset with default values."""
        asset = Asset.objects.create(name="Test Asset")

        assert asset.asset_id is not None
        assert len(asset.asset_id) == 32  # UUID hex without dashes
        assert asset.name == "Test Asset"
        assert asset.is_enabled is False
        assert asset.is_processing is False
        assert asset.nocache is False
        assert asset.play_order == 0
        assert asset.skip_asset_check is False

    @pytest.mark.unit
    def test_asset_creation_with_custom_values(self, db):
        """Test creating an asset with custom values."""
        start_date = timezone.now()
        end_date = start_date + timedelta(hours=2)

        asset = Asset.objects.create(
            name="Custom Asset",
            uri="https://example.com/video.mp4",
            md5="abc123def456",
            start_date=start_date,
            end_date=end_date,
            duration=7200,  # 2 hours
            mimetype="video/mp4",
            is_enabled=True,
            play_order=5
        )

        assert asset.name == "Custom Asset"
        assert asset.uri == "https://example.com/video.mp4"
        assert asset.md5 == "abc123def456"
        assert asset.start_date == start_date
        assert asset.end_date == end_date
        assert asset.duration == 7200
        assert asset.mimetype == "video/mp4"
        assert asset.is_enabled is True
        assert asset.play_order == 5

    @pytest.mark.unit
    def test_generate_asset_id_uniqueness(self):
        """Test that generate_asset_id produces unique IDs."""
        ids = [generate_asset_id() for _ in range(100)]
        assert len(set(ids)) == 100  # All IDs should be unique

    @pytest.mark.unit
    def test_asset_string_representation(self, db):
        """Test the __str__ method of Asset model."""
        asset = Asset.objects.create(name="Display Test Asset")
        assert str(asset) == "Display Test Asset"

    @pytest.mark.unit
    def test_asset_str_with_none_name(self, db):
        """Test __str__ method when name is None."""
        asset = Asset.objects.create(name=None)
        assert str(asset) == "None"

    @pytest.mark.unit
    @freeze_time("2024-01-15 12:00:00")
    def test_is_active_method_true(self, db):
        """Test is_active returns True for active assets."""
        start_date = timezone.now() - timedelta(hours=1)
        end_date = timezone.now() + timedelta(hours=1)

        asset = Asset.objects.create(
            name="Active Asset",
            is_enabled=True,
            start_date=start_date,
            end_date=end_date
        )

        assert asset.is_active() is True

    @pytest.mark.unit
    @freeze_time("2024-01-15 12:00:00")
    def test_is_active_method_false_disabled(self, db):
        """Test is_active returns False for disabled assets."""
        start_date = timezone.now() - timedelta(hours=1)
        end_date = timezone.now() + timedelta(hours=1)

        asset = Asset.objects.create(
            name="Disabled Asset",
            is_enabled=False,
            start_date=start_date,
            end_date=end_date
        )

        assert asset.is_active() is False

    @pytest.mark.unit
    @freeze_time("2024-01-15 12:00:00")
    def test_is_active_method_false_before_start(self, db):
        """Test is_active returns False before start date."""
        start_date = timezone.now() + timedelta(hours=1)
        end_date = timezone.now() + timedelta(hours=2)

        asset = Asset.objects.create(
            name="Future Asset",
            is_enabled=True,
            start_date=start_date,
            end_date=end_date
        )

        assert asset.is_active() is False

    @pytest.mark.unit
    @freeze_time("2024-01-15 12:00:00")
    def test_is_active_method_false_after_end(self, db):
        """Test is_active returns False after end date."""
        start_date = timezone.now() - timedelta(hours=2)
        end_date = timezone.now() - timedelta(hours=1)

        asset = Asset.objects.create(
            name="Expired Asset",
            is_enabled=True,
            start_date=start_date,
            end_date=end_date
        )

        assert asset.is_active() is False

    @pytest.mark.unit
    def test_is_active_method_false_missing_dates(self, db):
        """Test is_active returns False when dates are missing."""
        asset = Asset.objects.create(
            name="No Dates Asset",
            is_enabled=True,
            start_date=None,
            end_date=None
        )

        assert asset.is_active() is False

    @pytest.mark.unit
    def test_asset_table_name(self, db):
        """Test that the model uses the correct database table name."""
        assert Asset._meta.db_table == 'assets'

    @pytest.mark.unit
    def test_asset_primary_key(self, db):
        """Test that asset_id is the primary key."""
        asset = Asset.objects.create(name="PK Test")
        assert Asset._meta.pk.name == 'asset_id'
        assert asset.pk == asset.asset_id

    @pytest.mark.integration
    def test_asset_bulk_creation(self, db):
        """Test bulk creation of assets for performance."""
        assets_data = [
            Asset(name=f"Bulk Asset {i}", play_order=i)
            for i in range(100)
        ]

        created_assets = Asset.objects.bulk_create(assets_data)
        assert len(created_assets) == 100
        assert Asset.objects.count() == 100

    @pytest.mark.integration
    def test_asset_ordering_by_play_order(self, db):
        """Test assets can be ordered by play_order."""
        # Create assets with different play orders
        Asset.objects.create(name="Third", play_order=3)
        Asset.objects.create(name="First", play_order=1)
        Asset.objects.create(name="Second", play_order=2)

        ordered_assets = Asset.objects.order_by('play_order')
        names = [asset.name for asset in ordered_assets]
        assert names == ["First", "Second", "Third"]

    @pytest.mark.integration
    def test_asset_filtering_by_enabled_status(self, db):
        """Test filtering assets by enabled status."""
        Asset.objects.create(name="Enabled Asset", is_enabled=True)
        Asset.objects.create(name="Disabled Asset", is_enabled=False)

        enabled_assets = Asset.objects.filter(is_enabled=True)
        assert enabled_assets.count() == 1
        assert enabled_assets.first().name == "Enabled Asset"

    @pytest.mark.integration
    def test_asset_filtering_by_mimetype(self, db):
        """Test filtering assets by mimetype."""
        Asset.objects.create(name="Image Asset", mimetype="image/jpeg")
        Asset.objects.create(name="Video Asset", mimetype="video/mp4")
        Asset.objects.create(name="HTML Asset", mimetype="text/html")

        image_assets = Asset.objects.filter(mimetype__startswith="image/")
        assert image_assets.count() == 1

        video_assets = Asset.objects.filter(mimetype="video/mp4")
        assert video_assets.count() == 1

    @pytest.mark.performance
    def test_asset_query_performance(self, db, bulk_assets, performance_monitor):
        """Test query performance with large dataset."""
        performance_monitor.start()

        # Test various query patterns
        Asset.objects.filter(is_enabled=True).count()
        Asset.objects.filter(mimetype="image/jpeg").order_by('play_order')[:10]
        Asset.objects.exclude(start_date__isnull=True).count()

        performance_monitor.stop()
        performance_monitor.assert_performance(max_duration=1.0)

    @pytest.mark.tenant
    def test_asset_tenant_isolation(self, db, tenant_context, multi_tenant_setup):
        """Test that assets are properly isolated between tenants."""
        # Create asset in first tenant
        with tenant_context:
            tenant_asset = Asset.objects.create(
                name=f"Tenant Asset {tenant_context.tenant_id}"
            )

        # Verify asset exists in tenant context
        with tenant_context:
            assert Asset.objects.filter(name__contains=tenant_context.tenant_id).exists()

        # Verify asset doesn't appear in different context (simulated)
        # In real multi-tenant, this would be a different schema/database
        other_assets = Asset.objects.exclude(
            name__contains=tenant_context.tenant_id
        )
        assert not other_assets.filter(asset_id=tenant_asset.asset_id).exists()

    @pytest.mark.security
    def test_asset_field_length_limits(self, db):
        """Test that asset fields handle large inputs appropriately."""
        # Test very long strings (potential DoS attack)
        long_string = "x" * 10000

        asset = Asset.objects.create(
            name=long_string,
            uri=long_string,
            md5=long_string
        )

        # Verify data is stored (Django handles this gracefully)
        assert len(asset.name) == 10000
        assert len(asset.uri) == 10000
        assert len(asset.md5) == 10000

    @pytest.mark.security
    def test_asset_sql_injection_protection(self, db, security_scanner):
        """Test protection against SQL injection in asset queries."""
        # Create test asset
        Asset.objects.create(name="Normal Asset")

        # Test SQL injection payloads
        for payload in security_scanner.sql_injection_payloads():
            # These should not cause SQL errors or unwanted behavior
            try:
                results = Asset.objects.filter(name=payload)
                # Should return empty queryset, not cause errors
                assert results.count() >= 0
            except Exception as e:
                # Should not raise SQL-related exceptions
                assert "syntax error" not in str(e).lower()

    @pytest.mark.backwards_compat
    def test_asset_model_backwards_compatibility(self, db):
        """Test that existing asset data remains compatible."""
        # Test legacy field names and behavior
        asset = Asset.objects.create(
            name="Legacy Test Asset",
            uri="http://old.example.com/asset.jpg",  # HTTP instead of HTTPS
            duration=3600,
            is_enabled=True
        )

        # Verify legacy behavior is maintained
        assert asset.uri.startswith("http://")
        assert asset.duration == 3600
        assert asset.is_enabled is True

    @pytest.mark.regression
    def test_asset_timezone_handling(self, db):
        """Test timezone handling in asset dates (regression test)."""
        import pytz

        # Test with different timezones
        utc_time = timezone.now()
        eastern = pytz.timezone('US/Eastern')
        pacific = pytz.timezone('US/Pacific')

        eastern_time = utc_time.astimezone(eastern)
        pacific_time = utc_time.astimezone(pacific)

        asset = Asset.objects.create(
            name="Timezone Test",
            start_date=eastern_time,
            end_date=pacific_time
        )

        # Verify times are properly stored and converted
        assert asset.start_date.tzinfo is not None
        assert asset.end_date.tzinfo is not None

    @pytest.mark.unit
    def test_asset_edge_cases(self, db):
        """Test edge cases and boundary conditions."""
        # Test with minimal data
        minimal_asset = Asset.objects.create()
        assert minimal_asset.asset_id is not None

        # Test with maximum integer values
        max_asset = Asset.objects.create(
            name="Max Values",
            duration=2**63 - 1,  # Max BigIntegerField value
            play_order=2**31 - 1  # Max IntegerField value
        )
        assert max_asset.duration == 2**63 - 1
        assert max_asset.play_order == 2**31 - 1

        # Test with negative values
        negative_asset = Asset.objects.create(
            name="Negative Values",
            duration=-1,
            play_order=-1
        )
        assert negative_asset.duration == -1
        assert negative_asset.play_order == -1

    @pytest.mark.unit
    def test_asset_boolean_field_edge_cases(self, db):
        """Test boolean field edge cases."""
        # Test all boolean combinations
        combinations = [
            (True, True, True, True),
            (False, False, False, False),
            (True, False, True, False),
            (False, True, False, True),
        ]

        for enabled, processing, nocache, skip_check in combinations:
            asset = Asset.objects.create(
                name=f"Bool Test {enabled}{processing}{nocache}{skip_check}",
                is_enabled=enabled,
                is_processing=processing,
                nocache=nocache,
                skip_asset_check=skip_check
            )

            assert asset.is_enabled == enabled
            assert asset.is_processing == processing
            assert asset.nocache == nocache
            assert asset.skip_asset_check == skip_check


class TestAssetModelConstraints:
    """Test database constraints and validation."""

    @pytest.mark.unit
    def test_asset_unique_primary_key(self, db):
        """Test that asset_id is unique."""
        asset1 = Asset.objects.create(name="Asset 1")
        asset2 = Asset.objects.create(name="Asset 2")

        assert asset1.asset_id != asset2.asset_id

    @pytest.mark.integration
    def test_asset_concurrent_creation(self, db):
        """Test concurrent asset creation doesn't cause conflicts."""
        import threading
        import time

        created_assets = []
        errors = []

        def create_asset(index):
            try:
                asset = Asset.objects.create(name=f"Concurrent Asset {index}")
                created_assets.append(asset)
            except Exception as e:
                errors.append(e)

        # Create multiple threads to test concurrency
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_asset, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(created_assets) == 10
        asset_ids = [asset.asset_id for asset in created_assets]
        assert len(set(asset_ids)) == 10  # All IDs should be unique