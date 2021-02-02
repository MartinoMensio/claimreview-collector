import os
import mimetypes
import requests

# sources:
# https://gist.github.com/tomac4t/16dc1e91d95c94f60251e586672b6314
# https://docs.github.com/en/rest/reference/repos#upload-a-release-asset

REPO_FULL_NAME = os.environ.get('REPO_FULL_NAME', 'MartinoMensio/claimreview-data')
GITHUB_TOKEN = os.environ['GITHUB_TOKEN']

DATA_PATH = 'data'

auth_header = {
    'Authorization': f'token {GITHUB_TOKEN}'
}

def create_release(date):
    print('creating release', date)
    GITHUB_API_URL = f'https://api.github.com/repos/{REPO_FULL_NAME}/releases'

    # tag_name = date
    description = f'Daily release from {date}'

    data = {
        "tag_name": date,
        # "target_commitish": 'master',
        "name": date,
        "body": description,
        "draft": False,
        "prerelease": False
    }
    print(data)
    # create release
    res = requests.post(GITHUB_API_URL, headers=auth_header, json=data)
    res.raise_for_status()
    res_data = res.json()
    # release_id = res_data['id']
    # print('release_id', release_id)
    assets_url = res_data['upload_url'].replace('{?name,label}','')
    print(assets_url)

    # upload attachment
    file_name = f'{date}.zip'
    file_path = f'{DATA_PATH}/{date}.zip'
    mime_type = mimetypes.guess_type(file_path)[0]
    # GITHUB_RELEASE_URL = f'https://uploads.github.com/repos/{REPO_FULL_NAME}/releases/{release_id}'
    # GITHUB_FILE_URL = f'{GITHUB_RELEASE_URL}/assets?name={file_name}'
    headers = {**auth_header, 'Content-Type': mime_type}
    print('uploading data')
    res = requests.post(f'{assets_url}?name={file_name}', headers=headers, data=open(file_path, 'rb').read())
    # requests.get(assets_url, headers=auth_header)
    res.raise_for_status()
    print(res.status_code)
    # --upload-file ${ASSETS_PATH}/${file_name}
    print('data uploaded')
    return res


def get_release_asset_from_tag(tag, asset_name):
    # https://api.github.com/repos/MartinoMensio/claimreview-data/releases/tags/2021_02_01
    GITHUB_API_URL = f'https://api.github.com/repos/{REPO_FULL_NAME}/releases'
    res = requests.get(f'{GITHUB_API_URL}/tags/{tag}', headers=auth_header)
    res.raise_for_status()

    data = res.json()
    match = None
    for asset in data['assets']:
        if asset['name'] == asset_name:
            match = asset['id']
    if not match:
        raise ValueError(f'asset {asset_name} not found')
    
    # download asset
    headers = {**auth_header, 'Accept': 'application/octet-stream'}
    res = requests.get(f'{GITHUB_API_URL}/assets/{match}', headers=headers)
    res.raise_for_status()

    content = res.content
    print(len(content))

    return content
