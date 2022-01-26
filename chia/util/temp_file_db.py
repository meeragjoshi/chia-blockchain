from pathlib import Path
from chia.util.db_factory import create_database
import tempfile
import logging
log = logging.getLogger(__name__)

class TempFileDatabase:
    def __init__(self):
        log.error('temp file db used')
        self.db_path = Path(tempfile.NamedTemporaryFile().name)
        if self.db_path.exists():
            self.db_path.unlink()
        self.connection = create_database(str(self.db_path))
    
    async def disconnect(self):
        await self.connection.disconnect()
        self.db_path.unlink()