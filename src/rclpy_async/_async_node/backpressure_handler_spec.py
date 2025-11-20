from dataclasses import dataclass


@dataclass
class BackpressureHandlerSpec:
    """Specification for a backpressure handler"""

    max_queue_size: int = 0
    drop_oldest: bool = True
