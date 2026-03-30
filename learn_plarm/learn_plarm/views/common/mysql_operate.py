import pymysql
from queue import Queue
import threading
from contextlib import contextmanager
from learn_plarm.views.config.config import MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB

# 创建连接池
class ConnectionPool:
    """线程安全的连接池"""

    def __init__(self, host, port, user, password, database, pool_size=5):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.pool_size = pool_size
        self._pool = Queue(maxsize=pool_size)
        self._lock = threading.Lock()
        self._init_pool()

    def _create_connection(self):
        """创建新连接"""
        return pymysql.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )

    def _init_pool(self):
        """初始化连接池"""
        for _ in range(self.pool_size):
            conn = self._create_connection()
            self._pool.put(conn)

    def get_connection(self):
        """获取连接"""
        try:
            conn = self._pool.get(timeout=5)
            # 检查连接是否有效
            try:
                conn.ping(reconnect=False)
                return conn
            except:
                # 连接无效，创建新连接
                return self._create_connection()
        except:
            return self._create_connection()

    def return_connection(self, conn):
        """归还连接"""
        try:
            # 检查连接是否有效
            conn.ping(reconnect=False)
            self._pool.put(conn)
        except:
            # 连接无效，不归还，创建新连接补充
            with self._lock:
                if self._pool.qsize() < self.pool_size:
                    new_conn = self._create_connection()
                    self._pool.put(new_conn)


# 创建数据库连接
class MYSQLDB:
    def __init__(self, host, port, user, password, database):
        self.pool = ConnectionPool(host, port, user, password, database)

    @contextmanager # 装饰器
    def get_cursor(self):
        """获取游标"""
        conn = None
        cursor = None
        try:
            conn = self.pool.get_connection()
            cursor = conn.cursor()
            yield cursor
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.pool.return_connection(conn)

    def select_db(self, sql, params=None):   # 查找
        with self.get_cursor() as cursor:   # 上下文管理器
            cursor.execute(sql, params or ())  # 执行SQL
            return cursor.fetchall()

    def execute_db(self, sql, params=None):     # 修改
        with self.get_cursor() as cursor:     # 上下文管理器
            cursor.execute(sql, params or ())
            return cursor.lastrowid


# 创建实例
db = MYSQLDB(MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB)