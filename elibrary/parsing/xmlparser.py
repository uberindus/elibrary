import inspect
import xml.etree.ElementTree as ET

class AbstractParser:

    # xml_data = {<some string>, <some string>}
    external_data = set()
    internal_attr_data = set()

    # model_params = {<some string>, <some string>}

    # Model = ModelClass

    @staticmethod
    def __find_tag(root, rel_path):
        if rel_path == "":
            return root
        return root.find(rel_path)

    @staticmethod
    def __get_text(tag):
        # FIXME считается ли strip() ОБРАБОТКОЙ?
        return None if tag.text is None else tag.text.strip()

    @staticmethod
    def __get_attr(tag, attr):
        # FIXME применять ли strip() ?
        return tag.attrib.get(attr, None)

    @staticmethod
    def __default_handler(data_value):
        # FIXME применять ли strip() ?
        return data_value

    @staticmethod
    def __default_from(data_value):
        return data_value

    class OddArguments(TypeError):
        pass

    class OddPath(TypeError):
        pass

    class OddFromFunc(TypeError):
        pass

    class DataValidationError(ValueError):
        pass

    @classmethod
    def __validate_path(cls, data, data_path):
        pass
        # import re

        # FIXME check that we have tuple if we work with attr
        # if data in cls.internal_attr_data:
        #     if not re.match("\w+[/\w]*$", data_path[0]):
        #         raise cls.OddPath("Unvalid path - %s" % data_path[0])
        #
        #     if not re.match("\w+$", data_path[1]):
        #         raise cls.OddPath("Unvalid attribute name - %s" % data_path[1])
        #
        # elif data in cls.internal_data:
        #     if not re.match("\w+[/\w]*$", data_path):
        #         raise cls.OddPath("Unvalid path - %s" % data_path)

    @classmethod
    def __validate_args(cls, kwargs):
        _xml_data = cls.xml_data.copy()
        for k in kwargs:
            try:
                _xml_data.remove(k)
            except KeyError:
                raise cls.OddArguments(f" xml_data set in {cls.__name__} does not contain \"{k}\" argument")
        if _xml_data:
            raise cls.OddArguments(f"{_xml_data} pathes were not passed")

        for data, data_path in kwargs.items():
            cls.__validate_path(data, data_path)

    def __init__(self, root, **kwargs):

        cls = self.__class__

        if not hasattr(cls, 'xml_data'):
            cls.xml_data = cls.model_params.copy()
        if not hasattr(cls, 'internal_data'):
            cls.internal_data = cls.xml_data.difference(cls.external_data | cls.internal_attr_data)

        cls.__validate_args(kwargs)

        self.instance_xml_data = {}
        self.tag = root
        for data in cls.xml_data:
            if data in cls.external_data:
                self.instance_xml_data[data] = kwargs[data]
            if data in cls.internal_attr_data:
                path, attr = kwargs[data]
                tag = cls.__find_tag(root, path)

                self.instance_xml_data[data] = cls.__get_attr(tag, attr) if tag is not None else None

            if data in cls.internal_data:
                path = kwargs[data]
                tag = cls.__find_tag(root, path)
                self.instance_xml_data[data] = cls.__get_text(tag) if tag is not None else None

        static_methods = dict(inspect.getmembers(cls, inspect.isfunction))

        self.handled_xml_data = {}
        for data, data_value in self.instance_xml_data.items():
            handler = static_methods.get(data + "_handler", cls.__default_handler)
            self.handled_xml_data[data] = handler(data_value)

        self.instance_model_params = {}
        for param in cls.model_params:

            try:
                param_from = static_methods[param + "_from"]
            except KeyError:
                param_from = cls.__default_from
                self.instance_model_params[param] = param_from(self.handled_xml_data[param])
            else:
                args = inspect.getfullargspec(param_from)[0]
                args_values = []
                for a in args:
                    try:
                        args_values.append(self.handled_xml_data[a])
                    except KeyError:
                        raise cls.OddFromFunc(f"{param}_from function has argument {a} not included in xml_data")
                self.instance_model_params[param] = param_from(*args_values)

        for param in cls.model_params:
            try:
                validate = static_methods["validate_" + param]
                validate(self.instance_model_params[param])
            except KeyError:
                pass

        try:
            validate_all = static_methods["validate"]
        except KeyError:
            pass
        else:
            args = inspect.getfullargspec(validate_all)[0]
            args_values = []
            for a in args:
                try:
                    args_values.append(self.instance_model_params[a])
                except KeyError:
                    raise cls.OddFromFunc(f"validate function has argument {a} not included in model_params")
            validate_all(*args_values)

    def save(self):
        self.model = self.Model(**self.instance_model_params)
        return self.model.save()

    def get_model(self):
        return self.model

    def get_tag(self):
        return self.tag

    def _get_raw_data(self, data):
        return self.instance_xml_data[data]

    def _get_handled_data(self, data):
        return self.handled_xml_data[data]

    def _get_model_param(self, param):
        return self.instance_model_params[param]


class AbstractDjangoParser(AbstractParser):
    exclude_model_params = {"id"}

    def __init__(self, root, **kwargs):

        cls = self.__class__
        if not hasattr(cls, "model_params"):
            from django.db.models.fields.related import ForeignKey
            model_fileds = set()
            for f in cls.Model._meta.fields:
                if isinstance(f, ForeignKey):
                    model_fileds.add(f.attname[:-3])  # get rid of "_id" in field_name
                else:
                    model_fileds.add(f.attname)
            cls.model_params = model_fileds - cls.exclude_model_params

        super().__init__(root, **kwargs)