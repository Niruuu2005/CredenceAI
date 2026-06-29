from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

class BaseVerticalPack(ABC):
    """
    Abstract Base Class for all pluggable Vertical Intelligence Packs.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}

    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the vertical pack dynamically.
        """
        self.config.update(config)

    @abstractmethod
    async def execute(self, query: str, db: Session, job_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute the vertical intelligence gathering and refining workflow.
        Returns a dictionary containing the extracted raw run data.
        """
        pass

    @abstractmethod
    def generate_report(self, run_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesize the collected run data into the final structured report.
        """
        pass
