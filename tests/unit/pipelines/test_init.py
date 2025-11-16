"""Tests for pipelines package imports."""

from ingestion.pipelines import PipelineExecutor, PipelineFactory


class TestPipelinesInit:
    """Test pipelines __init__.py imports."""

    def test_pipeline_factory_import(self) -> None:
        """Test that PipelineFactory is importable."""
        assert PipelineFactory is not None
        assert hasattr(PipelineFactory, "__init__")

    def test_pipeline_executor_import(self) -> None:
        """Test that PipelineExecutor is importable."""
        assert PipelineExecutor is not None
        assert hasattr(PipelineExecutor, "__init__")

    def test_all_exports(self) -> None:
        """Test __all__ exports are correct."""
        from ingestion.pipelines import __all__

        assert "PipelineFactory" in __all__
        assert "PipelineExecutor" in __all__
        assert len(__all__) == 2
