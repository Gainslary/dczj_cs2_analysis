import mysql.connector
from mysql.connector import Error, pooling
import pandas as pd
from typing import Optional, Dict, List, Any, Union
import logging
from contextlib import contextmanager
import time

class MySQLConnector:
    """
    MySQL数据库连接工具类
    提供数据库连接、查询、插入、更新等基本操作
    """
    
    def __init__(self, 
                 host: str = "106.14.121.148",
                 port: int = 3306,
                 database: str = "dczj_cs_analysis",
                 username: str = "root",
                 password: str = "9AkWaqCsrd12",
                 charset: str = "utf8mb4",
                 use_unicode: bool = True,
                 pool_name: str = "mypool",
                 pool_size: int = 5,
                 pool_reset_session: bool = True,
                 autocommit: bool = False):
        """
        初始化MySQL连接器
        
        Args:
            host: 数据库主机地址
            port: 数据库端口
            database: 数据库名称
            username: 用户名
            password: 密码
            charset: 字符编码
            use_unicode: 是否使用Unicode
            pool_name: 连接池名称
            pool_size: 连接池大小
            pool_reset_session: 是否重置会话
            autocommit: 是否自动提交
        """
        self.config = {
            'host': host,
            'port': port,
            'database': database,
            'user': username,
            'password': password,
            'charset': charset,
            'use_unicode': use_unicode,
            'autocommit': autocommit,
            'time_zone': '+08:00',
            'sql_mode': 'STRICT_TRANS_TABLES,NO_ZERO_DATE,NO_ZERO_IN_DATE,ERROR_FOR_DIVISION_BY_ZERO',
            'raise_on_warnings': True
        }
        
        # 连接池配置
        self.pool_config = {
            **self.config,
            'pool_name': pool_name,
            'pool_size': pool_size,
            'pool_reset_session': pool_reset_session
        }
        
        self.connection_pool = None
        self._setup_logging()
        self._create_connection_pool()
    
    def _setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def _create_connection_pool(self):
        """创建连接池"""
        try:
            self.connection_pool = pooling.MySQLConnectionPool(**self.pool_config)
            self.logger.info(f"MySQL连接池创建成功，池大小: {self.pool_config['pool_size']}")
        except Error as e:
            self.logger.error(f"创建MySQL连接池失败: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """
        获取数据库连接的上下文管理器
        
        Yields:
            mysql.connector.connection: 数据库连接对象
        """
        connection = None
        try:
            connection = self.connection_pool.get_connection()
            yield connection
        except Error as e:
            self.logger.error(f"获取数据库连接失败: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection and connection.is_connected():
                connection.close()
    
    def test_connection(self) -> bool:
        """
        测试数据库连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                cursor.close()
                self.logger.info("数据库连接测试成功")
                return True
        except Error as e:
            self.logger.error(f"数据库连接测试失败: {e}")
            return False
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """
        执行查询语句
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            List[Dict[str, Any]]: 查询结果列表
        """
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor(dictionary=True)
                cursor.execute(query, params)
                results = cursor.fetchall()
                cursor.close()
                self.logger.info(f"查询执行成功，返回 {len(results)} 条记录")
                return results
        except Error as e:
            self.logger.error(f"查询执行失败: {e}")
            raise
    
    def execute_query_to_dataframe(self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """
        执行查询并返回DataFrame
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            pd.DataFrame: 查询结果DataFrame
        """
        try:
            with self.get_connection() as connection:
                df = pd.read_sql(query, connection, params=params)
                self.logger.info(f"查询执行成功，返回 {len(df)} 行数据")
                return df
        except Error as e:
            self.logger.error(f"查询执行失败: {e}")
            raise
    
    def execute_non_query(self, query: str, params: Optional[tuple] = None) -> int:
        """
        执行非查询语句（INSERT, UPDATE, DELETE）
        
        Args:
            query: SQL语句
            params: 参数
            
        Returns:
            int: 受影响的行数
        """
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                cursor.execute(query, params)
                connection.commit()
                affected_rows = cursor.rowcount
                cursor.close()
                self.logger.info(f"语句执行成功，影响 {affected_rows} 行")
                return affected_rows
        except Error as e:
            self.logger.error(f"语句执行失败: {e}")
            raise
    
    def execute_many(self, query: str, params_list: List[tuple]) -> int:
        """
        批量执行语句
        
        Args:
            query: SQL语句
            params_list: 参数列表
            
        Returns:
            int: 受影响的行数
        """
        try:
            with self.get_connection() as connection:
                cursor = connection.cursor()
                cursor.executemany(query, params_list)
                connection.commit()
                affected_rows = cursor.rowcount
                cursor.close()
                self.logger.info(f"批量执行成功，影响 {affected_rows} 行")
                return affected_rows
        except Error as e:
            self.logger.error(f"批量执行失败: {e}")
            raise
    
    def insert_dataframe(self, df: pd.DataFrame, table_name: str, 
                        if_exists: str = 'append', index: bool = False) -> int:
        """
        将DataFrame插入到数据库表
        
        Args:
            df: 要插入的DataFrame
            table_name: 目标表名
            if_exists: 如果表存在的处理方式 ('fail', 'replace', 'append')
            index: 是否包含索引
            
        Returns:
            int: 插入的行数
        """
        try:
            with self.get_connection() as connection:
                rows_inserted = df.to_sql(
                    name=table_name,
                    con=connection,
                    if_exists=if_exists,
                    index=index,
                    method='multi'
                )
                self.logger.info(f"DataFrame插入成功，插入 {len(df)} 行到表 {table_name}")
                return len(df)
        except Error as e:
            self.logger.error(f"DataFrame插入失败: {e}")
            raise
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        获取表信息
        
        Args:
            table_name: 表名
            
        Returns:
            Dict[str, Any]: 表信息
        """
        try:
            # 获取表结构
            columns_query = """
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_COMMENT
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
            """
            columns = self.execute_query(columns_query, (self.config['database'], table_name))
            
            # 获取表行数
            count_query = f"SELECT COUNT(*) as row_count FROM `{table_name}`"
            count_result = self.execute_query(count_query)
            row_count = count_result[0]['row_count'] if count_result else 0
            
            return {
                'table_name': table_name,
                'columns': columns,
                'row_count': row_count
            }
        except Error as e:
            self.logger.error(f"获取表信息失败: {e}")
            raise
    
    def list_tables(self) -> List[str]:
        """
        获取数据库中所有表名
        
        Returns:
            List[str]: 表名列表
        """
        try:
            query = "SHOW TABLES"
            results = self.execute_query(query)
            tables = [list(row.values())[0] for row in results]
            self.logger.info(f"获取到 {len(tables)} 个表")
            return tables
        except Error as e:
            self.logger.error(f"获取表列表失败: {e}")
            raise
    
    def close_pool(self):
        """关闭连接池"""
        if self.connection_pool:
            # 注意：mysql-connector-python的连接池没有直接的close方法
            # 连接池会在程序结束时自动清理
            self.logger.info("连接池已标记为关闭")


# 便捷函数
def create_mysql_connector(host: str = "106.14.121.148",
                          port: int = 3306,
                          database: str = "dczj_cs_analysis",
                          username: str = "root",
                          password: str = "9AkWaqCsrd12") -> MySQLConnector:
    """
    创建MySQL连接器的便捷函数
    
    Args:
        host: 数据库主机地址
        port: 数据库端口
        database: 数据库名称
        username: 用户名
        password: 密码
        
    Returns:
        MySQLConnector: MySQL连接器实例
    """
    return MySQLConnector(
        host=host,
        port=port,
        database=database,
        username=username,
        password=password
    )


if __name__ == "__main__":
    # 测试代码
    try:
        # 创建连接器
        db = create_mysql_connector()
        
        # 测试连接
        if db.test_connection():
            print("✅ 数据库连接成功！")
            
            # 获取表列表
            tables = db.list_tables()
            print(f"📋 数据库中的表: {tables}")
            
            # 如果有表，获取第一个表的信息
            if tables:
                table_info = db.get_table_info(tables[0])
                print(f"📊 表 '{tables[0]}' 信息:")
                print(f"   行数: {table_info['row_count']}")
                print(f"   列数: {len(table_info['columns'])}")
                
        else:
            print("❌ 数据库连接失败！")
            
    except Exception as e:
        print(f"❌ 错误: {e}")