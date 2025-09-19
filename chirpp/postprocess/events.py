

class SchemaError(Exception):
    pass

class Event:
    """
    This is the event code class, it will have context awere search and full text search
    """

    def __init__(self, name, keywords, rules=None, contex_aware=True, description=None,):
        """
        create a contex aware event class, this will be filling up the
        :param keywords:
        :param rules:
        """
        self.name = name
        self.description = description
        self.keywords = keywords
        self.contex_aware = contex_aware
        if self.contex_aware:
            if self.verify_schema(rules) and rules is not None:
                self.rules = rules
            elif rules is None:
                raise ValueError("rules cannot be None for context aware labels")
            else:
                raise SchemaError("rules do not match the proper medspacy schema")

    def to_db(self):
        pass

    def from_db(self):
        pass

    def search(self, start, end):
        pass

    def update_notes(self):
        pass

    def status(self):
        pass

    def toggle(self):
        """
        if in the database toggle active/inactive
        :return: the result of the toggle, error if not in the database
        """
        pass

    def verify_schema(self, schema):
        """
        verify the json schema of the context rules
        :return:
        """
        pass
