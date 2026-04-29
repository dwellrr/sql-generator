from app.core.schema_manager import schema_manager
from app.core.data_manager import DataManager
from app.core.dump_manager import DumpManager

data_manager = DataManager(schema_manager)
dump_manager = DumpManager(schema_manager)


def get_data_manager() -> DataManager:
    return data_manager


def get_dump_manager() -> DumpManager:
    return dump_manager
