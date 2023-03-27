import datetime


def convert_datetime_type(dt_string):
    dt_formats = ['%Y.%m.%d %H:%M:%S', '%Y.%m.%d %H.%M.%S']
    for dt_format in dt_formats:
        try:
            dt_object = datetime.datetime.strptime(dt_string, dt_format)
            return dt_object.strftime('%Y.%m.%d %H:%M:%S')
        except ValueError:
            pass
    raise ValueError("Could not convert datetime string: {}".format(dt_string))

def convert_string_to_datetime(dt_string):
    return datetime.datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S')