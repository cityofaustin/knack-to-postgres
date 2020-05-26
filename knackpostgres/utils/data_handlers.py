import json

class DataHandlers:
    """ Handlers for translating Knack record values to destination DB values """

    def __repr__(self):
        return f"<Handler type=`{self.type}` name=`{self.handler.__name__}`>"

    def __init__(self, field_type):

        self.type = field_type

        try:
            self.handler = getattr(self, "_" + self.type + "_handler")
        except AttributeError:
            self.handler = getattr(self, "_default_handler")

    def handle(self, val):

        return self.handler(val)

    def _link_handler(self, val):

        return val.get("url")

    def _default_handler(self, val):
        """
        Handles these fieldtypes:
            connection
            auto_increment
            paragraph_text
            multiple_choice
            short_text
            number
            boolean
            user_roles
            name
            address
        """
        if val == "":
            return None

        return val

    def _connection_handler(self, val):
        return val

    def _phone_handler(self, val):
        if val == "":
            return None

        return val.get("full")

    def _currency_handler(self, val):
        return float(val)

    def _file_handler(self, val):
        return val.get("url")

    def _image_handler(self, val):
        # image will be a url or key/val pair
        if val == []:
            return None

        try:
            return val.get(
                "url"
            ).strip()  # noticed some leading white space in data tracker

        except AttributeError:
            return val.strip()

    def _date_time_handler(self, val):
        if val == "":
            return None

        return val.get("iso_timestamp")

    def _timer_handler(self, val):
        if val == "":
            return None
            
        return val["times"][0]["from"]["iso_timestamp"]

    def _email_handler(self, val):
        return val.get("email")
