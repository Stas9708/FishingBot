import config


class Database:

    def __init__(self):
        self.connection = config.DB_CONFIG

    def get_user(self, user_id: int) -> [str, None]:
        with self.connection.cursor() as cursor:
            sql = ("SELECT `user_name` "
                   "FROM `user` "
                   "WHERE `user_id` = %s")
            cursor.execute(sql, (user_id,))
            result = cursor.fetchone()
        if result:
            return result['user_name']
        else:
            return None

    def reg_user(self, user_name, user_id):
        with self.connection.cursor() as cursor:
            sql = "INSERT INTO `user` (`user_name`, `user_id`) VALUES(%s, %s)"
            cursor.execute(sql, (user_name, user_id))
        self.connection.commit()
