from app.managers.dump_manager import dump_manager


class DumpService:
    def get_dump(self) -> str:
        return dump_manager.generate_from_db()


dump_service = DumpService()
