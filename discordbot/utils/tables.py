from asyncqlio.orm.schema import column, table, types

Table = table.table_base()


class Dynamic_Rules(Table):
    guild_id = column.Column(types.BigInt, primary_key=True)
    attrs = column.Column(types.Text)

    def __repr__(self):
        return f"<dynamic_rules(guild_id='{self.guild_id}', attrs='{self.attrs}')>"


class Messages(Table):
    guild_id = column.Column(types.BigInt)
    channel_id = column.Column(types.Text)
    message_id = column.Column(types.BigInt, primary_key=True)
    author = column.Column(types.Text)
    content = column.Column(types.Text)
    timestamp = column.Column(types.Timestamp)

    def __repr__(self):
        return f"<messages(guild_id='{self.guild_id}', channel_id='{self.channel_id}', message_id='{self.message_id}'" \
               f", author='{self.author}', content='{self.content}', timestamp='{self.timestamp}')>"


class Schedule(Table):
    id = column.Column(types.BigSerial, primary_key=True)
    expires = column.Column(types.Timestamp)
    event = column.Column(types.Text)
    extras = column.Column(types.Text)

    def __repr__(self):
        return f"<schedule(id='{self.id}', expires='{self.expires}', event='{self.event}', extras='{self.extras}')>"

    def __eq__(self, other):
        try:
            return self.id == other.id
        except AttributeError:
            return False


class Ignored(Table):
    object_id = column.Column(types.BigInt, primary_key=True)
    reason = column.Column(types.Text)
    type = column.Column(types.Text)

    def __repr__(self):
        return f"<ignored(object_id='{self.object_id}', reason='{self.reason}', type='{self.type}')>"
