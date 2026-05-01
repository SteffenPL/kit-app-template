try:
    from .extension import CellSimulationExtension
except ModuleNotFoundError as exc:
    if exc.name != "omni":
        raise
    CellSimulationExtension = None

__all__ = ["CellSimulationExtension"]
