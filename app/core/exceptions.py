class SQLFileIOError(Exception):
    """Generic exceptions when working with sql files for schemas, data, dumps"""

    pass


class InvalidSQLError(Exception):
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class EmptyFileError(Exception):
    def __init__(self):
        super().__init__("The loaded file is empty")


class SchemaError(Exception):
    """Base for all schema-related errors"""

    pass


class SchemaNotLoadedError(SchemaError):
    def __init__(self):
        super().__init__("Could not read the schema file")


class NoSchemaError(SchemaError):
    def __init__(self):
        super().__init__(
            "Could not read the schema file. Are you sure you uploaded one?"
        )
