from asyncqlio.orm.schema.column import Column
from asyncqlio.orm.schema.table import table_base
from asyncqlio.orm.schema.types import BigInt, Text

Table = table_base()


class Dynamic_Rules(Table):
    __tablename__ = 'dynamic_rules'

    guild_id = Column(BigInt, primary_key=True)
    attrs = Column(Text)

    def __repr__(self):
        return "<dynamic_rules(guild_id='%s', attrs='%s')>" % (self.guild_id, self.attrs)


class Messages(Table):
    __tablename__ = 'messages'

    guild_id = Column(BigInt)
    channel_id = Column(Text)
    message_id = Column(BigInt, primary_key=True)
    author = Column(Text)
    content = Column(Text)
    timestamp = Column(Text)

    def __repr__(self):
        return "<messages(guild_id='%s', channel_id='%s', message_id='%s', author='%s', content='%s', " \
               "timestamp='%s')>" \
               % (self.guild_id, self.channel_id, self.message_id, self.author, self.content, self.timestamp)
