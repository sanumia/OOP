import json
from .serializer import BaseSerializer
from .exceptions import SerializationError, DeserializationError

class JsonSerializer(BaseSerializer):
    def serialize(self, data, file_path):
        try:
            path = self._validate_file_path(file_path)
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except (TypeError, ValueError) as e:
            raise SerializationError(f"JSON serialization error: {str(e)}")
        except Exception as e:
            raise SerializationError(f"Unexpected error: {str(e)}")

    def deserialize(self, file_path):
        try:
            path = self._validate_file_path(file_path)
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise DeserializationError(f"JSON decode error: {str(e)}")
        except Exception as e:
            raise DeserializationError(f"Unexpected error: {str(e)}")