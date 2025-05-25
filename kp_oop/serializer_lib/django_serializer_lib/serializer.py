from abc import ABC, abstractmethod
from pathlib import Path
from .exceptions import SerializationError, DeserializationError
import json
import xml.etree.ElementTree as ET
from xml.dom import minidom

class BaseSerializer(ABC):
    @abstractmethod
    def serialize(self, data, file_path):
        pass
    
    @abstractmethod
    def deserialize(self, file_path):
        pass
    
    def _validate_file_path(self, file_path):
        path = Path(file_path)
        if not path.parent.exists():
            raise ValueError(f"Directory does not exist: {path.parent}")
        return path

class SerializerFactory:
    @staticmethod
    def get_serializer(format_type):
        if format_type == 'json':
            from .json_serializer import JsonSerializer
            return JsonSerializer()
        elif format_type == 'xml':
            from .xml_serializer import XmlSerializer
            return XmlSerializer()
        else:
            raise ValueError(f"Unsupported format: {format_type}")