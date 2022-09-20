import asyncpg

class database:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    async def execute(self, query: str):
        async with self.pool.acquire() as con:
            await con.execute(query)
    
    @staticmethod
    async def init(pool: asyncpg.Pool):
        async with pool.acquire() as con:
            await con.execute("""
                CREATE TABLE IF NOT EXISTS tickets(
                id serial PRIMARY KEY,
                fromchannel BIGINT,
                ownerid BIGINT,
                threadid BIGINT,
                created TIMESTAMP NOT NULL DEFAULT (current_timestamp AT TIME ZONE 'UTC'),
                statuscode SMALLINT
                )
            """) # This keeps track of all tickets

            await con.execute("""
                CREATE TABLE IF NOT EXISTS ticket_messages(
                channelid BIGINT,
                messageid BIGINT
                )
            """) # This is so the bot can load the persistent view and listen for ticket creations

            # await con.execute("""
                # CREATE TABLE IF NOT EXISTS reactions(
                # messageid BIGINT,
                # button
                # )
            # """)