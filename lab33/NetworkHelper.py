import requests

class NetworkHelper:
    BASE_URL = "http://127.0.0.1:8001/api/clients/"

    AUTH = ('admin123', 'admin123')

    def get_list(self):
        """Отримати список клієнтів"""
        try:
            response = requests.get(self.BASE_URL, auth=self.AUTH)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error fetching list: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Connection Error: {e}")
        return []

    def get_by_id(self, item_id):
        """Отримати клієнта по ID"""
        try:
            response = requests.get(f"{self.BASE_URL}{item_id}/", auth=self.AUTH)
            if response.status_code == 200:
                return response.json()
        except requests.exceptions.RequestException:
            pass
        return None

    def delete_item(self, item_id):
        """Видалити клієнта по ID"""
        try:
            # Важливо: слеш в кінці URL для DRF
            response = requests.delete(f"{self.BASE_URL}{item_id}/", auth=self.AUTH)
            return response.status_code == 204
        except requests.exceptions.RequestException:
            return False

    def create_item(self, data):
        """Створити клієнта (data має бути словником)"""
        try:
            response = requests.post(self.BASE_URL, json=data, auth=self.AUTH)
            return response.status_code == 201
        except requests.exceptions.RequestException:
            return False

    def update_item(self, item_id, data):
        """Оновити клієнта"""
        try:
            response = requests.put(f"{self.BASE_URL}{item_id}/", json=data, auth=self.AUTH)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False