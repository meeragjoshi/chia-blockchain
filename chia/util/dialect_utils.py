from enum import Enum
from typing import List

from databases import Database
import pymysql

class SqlDialect(Enum):
    SQLITE = 'sqlite'
    POSTGRES = 'postgresql'
    MYSQL = 'mysql'

data_type_map = {
    'blob' : {
        SqlDialect.SQLITE: 'blob',
        SqlDialect.POSTGRES: 'bytea',
        SqlDialect.MYSQL: 'longblob',
    },
    'tinyint': {
        SqlDialect.SQLITE: 'tinyint',
        SqlDialect.POSTGRES: 'smallint',
        SqlDialect.MYSQL: 'smallint'
    },
    'text-as-index': {
        SqlDialect.SQLITE: 'text',
        SqlDialect.POSTGRES: 'text',
        SqlDialect.MYSQL: 'varchar(255)'
    },
    'blob-as-index': {
        SqlDialect.SQLITE: 'blob',
        SqlDialect.POSTGRES: 'bytea',
        SqlDialect.MYSQL: 'varbinary(255)',
    },
}
def data_type(data_type: str, dialect: str):
    return data_type_map[data_type][SqlDialect(dialect)]

clause_map = {
    'AUTOINCREMENT': {
        SqlDialect.SQLITE: 'AUTOINCREMENT',
        SqlDialect.POSTGRES: 'GENERATED BY DEFAULT AS IDENTITY',
        SqlDialect.MYSQL: 'AUTO_INCREMENT'
    },
    'INDEXED BY': {
        SqlDialect.SQLITE: 'INDEXED BY',
        SqlDialect.POSTGRES: '', # postgres does not allow index hinting
        SqlDialect.MYSQL: 'USE INDEX'
    },
}
def clause(clause: str, dialect: str):
    return clause_map[clause][SqlDialect(dialect)]

def indexed_by(index: str, dialect:str):
    if SqlDialect(dialect) == SqlDialect.SQLITE:
        return f"INDEXED BY {index}"

    elif SqlDialect(dialect) == SqlDialect.POSTGRES:
        return ""

    elif SqlDialect(dialect) == SqlDialect.MYSQL:
        return f"USE INDEX ({index})"

    else:
        raise Exception("Invalid or unsupported sql dialect")

def reserved_word(word: str, dialect: str):
    if SqlDialect(dialect) == SqlDialect.SQLITE or SqlDialect(dialect) == SqlDialect.POSTGRES:
        return f"\"{word}\""
    elif SqlDialect(dialect) == SqlDialect.MYSQL:
        return f"`{word}`"



def upsert_query(table_name: str, primary_key_columns: List[str], columns: List[str], dialect: str):
    query_param_columns = map(lambda v: ':' + v, columns)
    
    if SqlDialect(dialect) == SqlDialect.SQLITE:
        return f"INSERT OR REPLACE INTO {table_name} VALUES({', '.join(query_param_columns)})"

    elif SqlDialect(dialect) == SqlDialect.POSTGRES:
        set_statements = _generate_set_statements(primary_key_columns, columns)
        return (
             f"INSERT INTO {table_name}({', '.join(columns)}) VALUES({', '.join(query_param_columns)}) "
             f"ON CONFLICT ({', '.join(primary_key_columns)}) "
             f"DO UPDATE SET {', '.join(set_statements)}"
         )

    elif SqlDialect(dialect) == SqlDialect.MYSQL:
        set_statements = _generate_set_statements(primary_key_columns, columns)
        return (
             f"INSERT INTO {table_name}({', '.join(columns)}) VALUES({', '.join(query_param_columns)}) "
             "ON DUPLICATE KEY UPDATE "
             f"{', '.join(set_statements)}"
         )

    else:
        raise Exception("Invalid or unsupported sql dialect")

def _generate_set_statements(primary_key_columns: List[str], columns: List[str]):
    set_statements = []
    for col in columns:
        if col not in primary_key_columns:
            set_statements.append(f"{col} = :{col}")
    return set_statements

async def create_index_if_not_exists(database: Database, query: str):
    if SqlDialect(database.url.dialect) == SqlDialect.MYSQL:
        try:
            await database.execute(query.replace(' IF NOT EXISTS', '').split('WHERE')[0].split('where')[0])
        except pymysql.err.InternalError as e:
            if 'Duplicate key name' not in str(e):
                raise e 
    else:
        await database.execute(query)

async def drop_index_if_exists(database: Database, query: str, table: str):
    if SqlDialect(database.url.dialect) == SqlDialect.MYSQL:
        try:
            await database.execute(f"{query.replace(' IF EXISTS', '')} on {table}")
        except pymysql.err.InternalError as e:
            if 'check that column/key exists' not in str(e):
                raise e 
    else:
        await database.execute(query)