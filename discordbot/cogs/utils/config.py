import yaml


# noinspection PyAttributeOutsideInit
class Config:
    """
    An easier way to load and save YAML.
    """

    def __init__(self, file):
        self.file = file
        self.load()

    def load(self):
        """
        Loads a bot_config file.
        """
        try:
            with open(self.file, "r") as file:
                self.db = yaml.safe_load(file)
        except FileNotFoundError:
            self.db = {}

    def save(self):
        """
        Saves a bot_config file.
        """
        with open(self.file, "w") as file:
            yaml.dump(self.db, file)

    def get(self, key, *args):
        """
        Gets an entry value.
        """
        if self.db.get(key, *args):
            return self.db.get(key, *args)
        else:
            self.db[key] = []
            return self.db.get(key, *args)

    def place(self, key, value):
        """
        Edits an entry value.
        """
        self.db[key] = value
        self.save()

    def remove(self, key, value):
        """
        Removes an entry value.
        """
        self.db.get(key).remove(value)
        self.save()

    def delete(self, key):
        """
        Delete an entry.
        """
        try:
            del self.db[key]
        except KeyError:
            pass
        self.save()

    def __contains__(self, item):
        return self.db.__contains__(item)

    def __len__(self):
        return self.db.__len__()

    def all(self):
        return self.db
