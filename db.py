import config
from utils import photo_count_per_user


class Database:

    def __init__(self):
        self.connection = config.DB_CONFIG

    def get_user_info(self, user_id: int) -> [str, None]:
        with self.connection.cursor() as cursor:
            sql = ("SELECT `id`, `user_name` "
                   "FROM `user` "
                   "WHERE `user_id` = %s")
            cursor.execute(sql, (user_id,))
            result = cursor.fetchone()
        if result:
            return result
        else:
            return None

    def reg_user(self, user_name, user_id):
        with self.connection.cursor() as cursor:
            sql = "INSERT INTO `user` (`user_name`, `user_id`) VALUES(%s, %s)"
            cursor.execute(sql, (user_name, user_id))
        self.connection.commit()

    def add_record_to_table(self, user_id, date, location, description, photo, weather, media_group_id):
        with self.connection.cursor() as cursor:
            if photo_count_per_user[media_group_id] > 1:
                sql = ("UPDATE `fishing_history` "
                       "SET `photos` = %s "
                       "WHERE `user_id` = %s")
                cursor.execute(sql, (photo, user_id))
            else:
                sql = ("INSERT INTO `fishing_history` (`user_id`, `date`, `location`, `description`, `photos`, "
                       "`weather`) "
                       "VALUES(%s, %s, %s, %s, %s, %s)")
                cursor.execute(sql, (user_id, date, location, description, photo, weather))
        self.connection.commit()
