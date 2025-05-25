from xml.etree import ElementTree as ET
from xml.dom import minidom
from .serializer import BaseSerializer
from .exceptions import SerializationError, DeserializationError

class XmlSerializer(BaseSerializer):
    def serialize(self, data, file_path):
        try:
            path = self._validate_file_path(file_path)
            root = ET.Element('data')
            self._dict_to_xml(root, data)
            
            xml_str = ET.tostring(root, encoding='utf-8')
            xml_pretty = minidom.parseString(xml_str).toprettyxml(indent="  ")
            
            with open(path, 'w', encoding='utf-8') as f:
                f.write(xml_pretty)
        except Exception as e:
            raise SerializationError(f"XML serialization error: {str(e)}")

    def deserialize(self, file_path):
        try:
            path = self._validate_file_path(file_path)
            tree = ET.parse(path)
            root = tree.getroot()
            return self._xml_to_dict(root)
        except Exception as e:
            raise DeserializationError(f"XML deserialization error: {str(e)}")

    def _dict_to_xml(self, parent, data):
        if isinstance(data, dict):
            for key, value in data.items():
                element = ET.SubElement(parent, str(key))
                self._dict_to_xml(element, value)
        elif isinstance(data, (list, tuple)):
            for item in data:
                element = ET.SubElement(parent, 'item')
                self._dict_to_xml(element, item)
        else:
            parent.text = str(data)

    def _xml_to_dict(self, element):
        if len(element) == 0:
            return element.text
        
        result = {}
        for child in element:
            child_data = self._xml_to_dict(child)
            
            if child.tag == 'item':
                if 'items' not in result:
                    result['items'] = []
                result['items'].append(child_data)
            else:
                if child.tag in result:
                    if not isinstance(result[child.tag], list):
                        result[child.tag] = [result[child.tag]]
                    result[child.tag].append(child_data)
                else:
                    result[child.tag] = child_data
        
        return result