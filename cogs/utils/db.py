import asyncpg

class database:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    async def execute(self, query: str, *args) -> tuple:
        async with self.pool.acquire() as con:
            result = await con.execute(query, *args)
        return result
    
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
                statuscode SMALLINT,
                closed_by BIGINT
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


class ticket:
    """Simple wrapper class to represent a ticket in the database"""
    def __init__(self):
        pass