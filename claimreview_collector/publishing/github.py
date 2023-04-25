import os
import json
import mimetypes
import requests

# sources:
# https://gist.github.com/tomac4t/16dc1e91d95c94f60251e586672b6314
# https://docs.github.com/en/rest/reference/repos#upload-a-release-asset

REPO_FULL_NAME = os.environ.get("REPO_FULL_NAME", "MartinoMensio/claimreview-data")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", None)

DATA_PATH = "data"

auth_header = {"Authorization": f"token {GITHUB_TOKEN}"}


def _check_github_token(func):
    def wrapper(*args, **kwargs):
        if GITHUB_TOKEN is None:
            raise ValueError("GITHUB_TOKEN not set for write operations")
        return func(*args, **kwargs)

    return wrapper


@_check_github_token
def create_release(date, result_stats):
    print("creating release", date)
    GITHUB_API_URL = f"https://api.github.com/repos/{REPO_FULL_NAME}/releases"

    # tag_name = date
    description = f"Daily release from {date}"

    data = {
        "tag_name": date,
        # "target_commitish": 'master',
        "name": date,
        "body": description,
        "draft": False,
        "prerelease": False,
    }
    print(data)
    # create release
    res = requests.post(GITHUB_API_URL, headers=auth_header, json=data)
    res.raise_for_status()
    res_data = res.json()
    # release_id = res_data['id']
    # print('release_id', release_id)
    assets_url = res_data["upload_url"].replace("{?name,label}", "")
    print(assets_url)

    res = upload_stats(assets_url, result_stats)
    res = upload_zip(date, assets_url)

    return res


@_check_github_token
def upload_stats(assets_url, result_stats):
    # upload attachments
    print("uploading stats for", result_stats["date"])
    file_name = "stats.json"
    mime_type = mimetypes.guess_type(f"{DATA_PATH}/index.json")[0]
    headers = {**auth_header, "Content-Type": mime_type}
    res = requests.post(
        f"{assets_url}?name={file_name}", headers=headers, data=json.dumps(result_stats)
    )
    # requests.get(assets_url, headers=auth_header)
    res.raise_for_status()
    print(res.status_code)
    return res


@_check_github_token
def upload_zip(date, assets_url):
    file_name = f"{date}.zip"
    file_path = f"{DATA_PATH}/{date}.zip"
    mime_type = mimetypes.guess_type(file_path)[0]
    # GITHUB_RELEASE_URL = f'https://uploads.github.com/repos/{REPO_FULL_NAME}/releases/{release_id}'
    # GITHUB_FILE_URL = f'{GITHUB_RELEASE_URL}/assets?name={file_name}'
    headers = {**auth_header, "Content-Type": mime_type}
    print("uploading data")
    res = requests.post(
        f"{assets_url}?name={file_name}",
        headers=headers,
        data=open(file_path, "rb").read(),
    )
    # requests.get(assets_url, headers=auth_header)
    res.raise_for_status()
    print(res.status_code)
    # --upload-file ${ASSETS_PATH}/${file_name}
    print("data uploaded")
    return res


def get_release_asset_from_tag(tag, asset_name):
    # https://api.github.com/repos/MartinoMensio/claimreview-data/releases/tags/2021_02_01
    GITHUB_API_URL = f"https://api.github.com/repos/{REPO_FULL_NAME}/releases"
    res = requests.get(f"{GITHUB_API_URL}/tags/{tag}")
    res.raise_for_status()
    #
    data = res.json()
    match = None
    for asset in data["assets"]:
        if asset["name"] == asset_name:
            match = asset["id"]
    if not match:
        raise ValueError(f"asset {asset_name} not found")
    #
    # download asset
    headers = {"Accept": "application/octet-stream"}
    res = requests.get(f"{GITHUB_API_URL}/assets/{match}", headers=headers)
    res.raise_for_status()
    #
    content = res.content
    print(len(content))
    #
    return content


def add_stats_to_all_releases():
    with open(f"{DATA_PATH}/index.json") as f:
        index = json.load(f)
    for tag, v in index.items():
        if tag == "latest":
            continue
        GITHUB_API_URL = f"https://api.github.com/repos/{REPO_FULL_NAME}/releases"
        res = requests.get(f"{GITHUB_API_URL}/tags/{tag}")
        res.raise_for_status()
        res_data = res.json()
        assets_url = res_data["upload_url"].replace("{?name,label}", "")
        print(assets_url)
        v["date"] = tag
        #
        upload_stats(assets_url, v)
