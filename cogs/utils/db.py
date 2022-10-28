import asyncpg

class database:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    async def execute(self, query: str, *args) -> tuple:
        async with self.pool.acquire() as con:
            result = await con.execute(query, *args)
        return result
    
    async def fetch(self, query: str, *args) -> tuple:
        async with self.pool.acquire() as con:
            result = await con.fetch(query, *args)
        return result
    
    @staticmethod
    async def init(pool: asyncpg.Pool):
        """First time initialization of a database."""
        async with pool.acquire() as con:
            await con.execute("""
                CREATE TABLE IF NOT EXISTS tickets(
                id serial PRIMARY KEY,
                fromchannel BIGINT NOT NULL,
                frommessage BIGINT NOT NULL,
                firstmessage BIGINT,
                ownerid BIGINT NOT NULL,
                threadid BIGINT NOT NULL,
                created TIMESTAMP NOT NULL DEFAULT (current_timestamp AT TIME ZONE 'UTC'),
                statuscode SMALLINT NOT NULL DEFAULT 0,
                closed TIMESTAMP,
                closed_by BIGINT DEFAULT 0,
                serverid BIGINT NOT NULL
                )
            """) # This keeps track of all tickets

            await con.execute("""
                CREATE TABLE IF NOT EXISTS ticket_messages(
                channelid BIGINT NOT NULL,
                messageid BIGINT NOT NULL,
                threadprefix VARCHAR(4),
                rolestoping TEXT,
                deleted BOOL NOT NULL DEFAULT false
                )
            """) # This is so the bot can load the persistent view and listen for ticket creations

            # await con.execute("""
                # CREATE TABLE IF NOT EXISTS reactions(
                # messageid BIGINT,
                # button
                # )
            # """)


class ticket:
    """Simple wrapper class to represent a ticket in the database"""
    def __init__(self):
        pass