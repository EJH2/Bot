from asyncqlio.orm.schema.column import Column
from asyncqlio.orm.schema.table import table_base
from asyncqlio.orm.schema.types import BigInt, Text, SmallInt

Table = table_base()


class Dynamic_Rules(Table):

    guild_id = Column(BigInt, primary_key=True)
    attrs = Column(Text)

    def __repr__(self):
        return f"<dynamic_rules(guild_id='{self.guild_id}', attrs='{self.attrs}')>"


class Messages(Table):

    guild_id = Column(BigInt)
    channel_id = Column(Text)
    message_id = Column(BigInt, primary_key=True)
    author = Column(Text)
    content = Column(Text)
    timestamp = Column(Text)

    def __repr__(self):
        return f"<messages(guild_id='{self.guild_id}', channel_id='{self.channel_id}', message_id='{self.message_id}'" \
               f", author='{self.author}', content='{self.content}', timestamp='{self.timestamp}')>"


class Schedule(Table):
    id = Column(SmallInt, autoincrement=True, primary_key=True)
    expires = Column(BigInt)
    event = Column(Text)
    extras = Column(Text)

    def __repr__(self):
        return f"<schedule(id='{self.id}', expires='{self.expires}', event='{self.event}', extras='{self.extras}')>"

    def __eq__(self, other):
        try:
            return self.id == other.id
        except AttributeError:
            return False
