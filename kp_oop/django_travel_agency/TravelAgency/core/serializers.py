import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from django.core.serializers.python import Serializer as PythonSerializer
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Model, FileField, ImageField, ForeignKey, DateTimeField
from datetime import datetime
from django.core.files import File

class UniversalSerializer:
    """
    Универсальный сериализатор для Django моделей с поддержкой JSON и XML
    """
    
    @staticmethod
    def serialize(instance, format='json', pretty=True):
        """
        Сериализация объекта Django в указанный формат
        :param instance: Экземпляр модели Django
        :param format: 'json' или 'xml'
        :param pretty: Форматировать вывод для читаемости
        :return: Строка в выбранном формате
        """
        if not isinstance(instance, Model):
            raise ValueError("Можно сериализовать только Django модели")

        # Получаем словарь с данными модели
        data_dict = UniversalSerializer._model_to_dict(instance)
        
        if format == 'json':
            indent = 4 if pretty else None
            return json.dumps(data_dict, cls=DjangoJSONEncoder, indent=indent, ensure_ascii=False)
        elif format == 'xml':
            root = ET.Element(instance._meta.model_name)
            UniversalSerializer._dict_to_xml(data_dict, root)
            xml_str = ET.tostring(root, encoding='utf-8')
            return minidom.parseString(xml_str).toprettyxml(indent="  ") if pretty else xml_str.decode()
        else:
            raise ValueError(f"Неподдерживаемый формат: {format}")

    @staticmethod
    def deserialize(model_class, data, format='json'):
        """
        Десериализация данных в объект Django
        :param model_class: Класс модели Django
        :param data: Строка данных для десериализации
        :param format: 'json' или 'xml'
        :return: Экземпляр модели
        """
        if format == 'json':
            data_dict = json.loads(data)
        elif format == 'xml':
            data_dict = UniversalSerializer._xml_to_dict(data)
        else:
            raise ValueError(f"Неподдерживаемый формат: {format}")

        return UniversalSerializer._dict_to_model(model_class, data_dict)

    @staticmethod
    def _model_to_dict(instance):
        """Конвертирует модель Django в словарь"""
        data = {'id': instance.pk}
        
        for field in instance._meta.get_fields():
            if field.is_relation and not field.many_to_one:
                continue  # Пропускаем ManyToMany и обратные связи
            
            field_name = field.name
            field_value = getattr(instance, field_name)
            
            # Специальная обработка для разных типов полей
            if isinstance(field, (FileField, ImageField)):
                data[field_name] = field_value.url if field_value else None
            elif isinstance(field, DateTimeField):
                data[field_name] = field_value.isoformat() if field_value else None
            elif isinstance(field, ForeignKey):
                data[f"{field_name}_id"] = field_value.pk if field_value else None
            else:
                data[field_name] = field_value
        
        return data

    @staticmethod
    def _dict_to_model(model_class, data_dict):
        """Создает или обновляет модель из словаря"""
        instance_id = data_dict.pop('id', None)
        instance = model_class.objects.get_or_create(id=instance_id)[0]
        
        for field_name, value in data_dict.items():
            # Пропускаем поля, которых нет в модели
            if not hasattr(model_class, field_name):
                continue
                
            field = model_class._meta.get_field(field_name)
            
            # Обработка ForeignKey
            if isinstance(field, ForeignKey) and value is not None:
                related_model = field.remote_field.model
                setattr(instance, field_name, related_model.objects.get(pk=value))
            else:
                setattr(instance, field_name, value)
        
        instance.save()
        return instance

    @staticmethod
    def _dict_to_xml(data_dict, parent):
        """Рекурсивно конвертирует словарь в XML элементы"""
        for key, value in data_dict.items():
            if isinstance(value, dict):
                element = ET.SubElement(parent, key)
                UniversalSerializer._dict_to_xml(value, element)
            elif isinstance(value, (list, tuple)):
                for item in value:
                    element = ET.SubElement(parent, key)
                    if isinstance(item, dict):
                        UniversalSerializer._dict_to_xml(item, element)
                    else:
                        element.text = str(item)
            else:
                element = ET.SubElement(parent, key)
                element.text = str(value) if value is not None else ''

    @staticmethod
    def _xml_to_dict(xml_str):
        """Конвертирует XML в словарь"""
        def parse_node(node):
            if len(node) == 0:
                return node.text
            result = {}
            for child in node:
                child_data = parse_node(child)
                if child.tag in result:
                    if not isinstance(result[child.tag], list):
                        result[child.tag] = [result[child.tag]]
                    result[child.tag].append(child_data)
                else:
                    result[child.tag] = child_data
            return result
        
        root = ET.fromstring(xml_str)
        return parse_node(root)


class JsonCountrySerializer:
    """Специализированный сериализатор для модели Country (JSON)"""
    
    @staticmethod
    def serialize(country):
        return UniversalSerializer.serialize(country, 'json')
    
    @staticmethod
    def deserialize(json_data):
        from .models import Country
        return UniversalSerializer.deserialize(Country, json_data, 'json')


class XmlCountrySerializer:
    """Специализированный сериализатор для модели Country (XML)"""
    
    @staticmethod
    def serialize(country):
        return UniversalSerializer.serialize(country, 'xml')
    
    @staticmethod
    def deserialize(xml_data):
        from .models import Country
        return UniversalSerializer.deserialize(Country, xml_data, 'xml')