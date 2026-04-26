class SchemaError(Exception):
    """Base for all schema-related errors"""

    pass


class EmptySchemaError(SchemaError):
    def __init__(self):
        super().__init__("The loaded schema file is empty")


class InvalidSQLError(SchemaError):
    def __init__(self, detail: str):
        self.detail = detail
        super().__init__(detail)


class SchemaNotLoadedError(SchemaError):
    def __init__(self):
        super().__init__("Could not read the schema file")


class NoSchemaError(SchemaError):
    def __init__(self):
        super().__init__(
            "Could not read the schema file. Are you sure you uploaded one?"
        )
