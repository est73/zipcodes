import sqlite3
import time

class ConnectionManager(object):

    def __init__(self):
        self.db_location = 'zipcodes.db'
        conn = sqlite3.connect(self.db_location)
        conn.close()

    def query(self, sql, params=None):
        conn = None
        retry_count = 0
        while not conn and retry_count <= 10:
            try:
                conn = sqlite3.connect(self.db_location)
            except sqlite3.OperationalError:
                retry_count += 1
                time.sleep(0.001)

        if not conn and retry_count > 10:
            raise sqlite3.OperationalError(
                "Can't connect to sqlite database: '%s'." % self.db_location
            )

        cursor = conn.cursor()
        if params is not None:
            cursor.execute(sql, params)
        else:
            cursor.execute(sql)
        res = cursor.fetchall()
        conn.close()
        return res


ZIP_ID_QUERY = "SELECT * FROM ZipCodes WHERE id=?"
ZIP_QUERY = "SELECT * FROM ZipCodes WHERE city LIKE ? AND zip=? AND country LIKE ?"
ZIP_RANGE_QUERY = (
    "SELECT * FROM ZipCodes "
    "WHERE longitude >= ? "
    "  AND longitude <= ? "
    "  AND latitude >= ? "
    "  AND latitude <= ?"
)


class ZipCode(object):

    def __init__(self, data):
        self.id = data[0]
        self.country = data[1]
        self.zip = data[2]
        self.city = data[3]
        self.state = data[4]
        self.latitude = data[5]
        self.longitude = data[6]


def format_result(zips):
    if len(zips) > 0:
        return [ZipCode(zc) for zc in zips]
    else:
        return None


class ZipNotFoundException(Exception):
    pass


class ZipCodeDatabase(object):

    def __init__(self, conn_manager=None):
        if conn_manager is None:
            conn_manager = ConnectionManager()
        self.conn_manager = conn_manager

    def get_zipcodes_by_zip_id(self, zip_id, radius):
        zips = self.get_id(zip_id)
        zipcode = zips[0]

        radius = float(radius)

        long_range = (
            zipcode.longitude - (radius / 111.04),
            zipcode.longitude + (radius / 111.04),
        )
        lat_range = (
            zipcode.latitude - (radius / 78.85),
            zipcode.latitude + (radius / 78.85),
        )

        return format_result(
            self.conn_manager.query(
                ZIP_RANGE_QUERY,
                (long_range[0], long_range[1], lat_range[0], lat_range[1]),
            )
        )

    def get_id(self, zip_id):
        return format_result(self.conn_manager.query(ZIP_ID_QUERY, (zip_id,)))

    def get(self, city, zipcode, country):
        return format_result(self.conn_manager.query(ZIP_QUERY, (city, zipcode, country,)))

    def __getitem__(self, zipcode):
        zipcode = self.get(str(zipcode))
        if zipcode is None:
            raise IndexError("Couldn't find zipcode: '%s'" % zipcode)
        else:
            return zipcode[0]


zcdb = ZipCodeDatabase()
in_radius = list(z.id for z in zcdb.get_zipcodes_by_zip_id(1420623, 10))
print(in_radius)
