"""Prometheus metrics registry."""

from prometheus_client import Counter, Gauge


class MetricsRegistry:
    """Metrics registry for analytics service."""

    def __init__(self) -> None:
        """Initialize metrics."""
        # Counter for processed events
        self.events_processed_total = Counter(
            "analytics_events_processed_total",
            "Total number of events processed",
            ["event_type"],
        )

        # Counter for failed events
        self.events_failed_total = Counter(
            "analytics_events_failed_total",
            "Total number of events failed",
            ["event_type"],
        )

        # Gauge for consumer lag
        self.consumer_lag = Gauge(
            "analytics_consumer_lag",
            "Kafka consumer lag",
            ["topic", "partition"],
        )
