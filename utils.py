import pandas as pd
from pathlib import Path
from pandas import DataFrame
import requests
from requests.exceptions import RequestException, HTTPError, Timeout, ConnectionError
import json


def load_data(file_path: str):
    return pd.read_csv(file_path)

def save_data(file_path: str, csv_data: DataFrame):
    path = Path(file_path)
    if not path.exists():
        path.touch()
    csv_data.to_csv(file_path, index=False)

def call_api(method, url, headers=None, params=None, data=None, json=None, timeout=10):
    """
    Hàm gọi API tổng quát bằng requests
    :param method: GET, POST, PUT, DELETE
    :param url: Endpoint API
    :param headers: dict - Header gửi kèm
    :param params: dict - Query string (?key=value)
    :param data: dict - Form data
    :param json: dict - JSON body
    :param timeout: Thời gian chờ tối đa (giây)
    :return: dict - Response JSON hoặc thông báo lỗi
    """
    try:
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=headers,
            params=params,
            data=data,
            json=json,
            timeout=timeout
        )

        # Kiểm tra mã HTTP
        response.raise_for_status()

        # Nếu server trả về JSON
        try:
            return response
        except ValueError:
            return {"message": "Response is not valid JSON", "raw_text": response.text}

    except HTTPError as e:
        res = e.response
        return {"error": f"HTTP error occurred: {res.text}", "status_code": res.status_code}
    except ConnectionError:
        return {"error": "Connection error occurred"}
    except Timeout:
        return {"error": "Request timed out"}
    except RequestException as e:
        return {"error": f"Unexpected error: {e}"}

def load_config(file_path: str):
    config_path = Path(file_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file is not found: {file_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)