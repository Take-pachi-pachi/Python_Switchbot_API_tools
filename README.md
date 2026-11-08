# webhook_Switchbot.py の使い方

この Readme は、SwitchBot API を操作するコマンドラインツール [webhook_Switchbot.py](./webhook_Switchbot.py) 専用の説明です。

このツールでできること:

- SwitchBot デバイス一覧の取得
- 指定したデバイスの現在状態の取得
- Webhook URL の登録
- 現在登録されている Webhook URL / 詳細の確認
- Webhook 設定の更新・削除

Webhook イベントを受け取る GAS の設定・処理については [readme_webhook_receiver.md](./readme_webhook_receiver.md) を参照してください。

## 必要な環境

- Python 3.10 以上
- `requests`
- `python-dotenv`
- SwitchBot Open Token と Secret Key

### 仮想環境の作成と依存パッケージのインストール

プロジェクトのルートフォルダーで PowerShell を開いて実行します。

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install requests python-dotenv
```

この Readme の例は仮想環境を有効化せず、`.venv` 内の Python を直接実行します。PowerShell の実行ポリシーを変更する必要はありません。

## `.env` の準備

プロジェクトのルートフォルダーに `.env` ファイルを作成します。

```env
SWITCHBOT_TOKEN=your_switchbot_open_token
SWITCHBOT_SECRET=your_switchbot_secret_key
```

`.env` は `webhook_Switchbot.py` が `python-dotenv` で読み込みます。各行は `KEY=value` の形式で記述します。実際の Token / Secret を Readme やソースコードに書いたり、GitHub に公開したりしないでください。プロジェクトの `.gitignore` では `.env` を除外しています。

### 必要に応じて設定する値

```env
SWITCHBOT_Lock_DEVICEID=your_device_id
GAS_URL=https://script.google.com/macros/s/your_deployment_id/exec
```

- `SWITCHBOT_Lock_DEVICEID`: `status` コマンドの `--device-id` を省略した場合の対象 Device ID。`--device-id` を毎回指定するなら不要です。
- `GAS_URL`: `setup-webhook`、`update-webhook`、`delete-webhook` の `--url` を省略した場合の宛先 URL。`--url` を毎回指定するなら不要です。

Webhook URL も、実際のデプロイ URL をソースコードや公開 Readme に記載しないでください。

## 共通の実行形式

PowerShell でプロジェクトのルートフォルダーに移動して実行します。

```powershell
.\.venv\Scripts\python.exe .\webhook_Switchbot.py <action> [options]
```

使用できる action:

```text
list
status
setup-webhook
query-webhook
update-webhook
delete-webhook
```

引数を省略すると `status` が実行されます。ヘルプは次のコマンドで確認できます。

```powershell
.\.venv\Scripts\python.exe .\webhook_Switchbot.py --help
```

## コマンド

### デバイス一覧を取得

```powershell
.\.venv\Scripts\python.exe .\webhook_Switchbot.py list
```

SwitchBot API のデバイス一覧を JSON で表示し、プロジェクトの `deviceList.json` に保存します。このファイルには実デバイスの名前や ID が含まれるため、GitHub に公開しないでください。`.gitignore` で除外されています。

### デバイスの状態を取得

```powershell
.\.venv\Scripts\python.exe .\webhook_Switchbot.py status --device-id YOUR_DEVICE_ID
```

`--device-id` を省略する場合は `.env` の `SWITCHBOT_Lock_DEVICEID` を使用します。

```powershell
.\.venv\Scripts\python.exe .\webhook_Switchbot.py status
```

### Webhook を登録

```powershell
.\.venv\Scripts\python.exe .\webhook_Switchbot.py setup-webhook --url "YOUR_GAS_WEB_APP_URL"
```

このコマンドは全デバイス向け (`deviceList: "ALL"`) の Webhook を設定します。`--url` を省略した場合は `.env` の `GAS_URL` を使用します。

### Webhook URL 一覧を確認

```powershell
.\.venv\Scripts\python.exe .\webhook_Switchbot.py query-webhook
```

`queryUrl` を実行し、現在登録されている URL 一覧を表示します。

### 指定 URL の Webhook 詳細を確認

```powershell
.\.venv\Scripts\python.exe .\webhook_Switchbot.py query-webhook --url "YOUR_GAS_WEB_APP_URL"
```

`queryDetails` を実行します。正常時のレスポンス例:

```json
{
  "statusCode": 100,
  "body": [
    {
      "url": "https://example.com/webhook",
      "createTime": 1634567890,
      "lastUpdateTime": 1634567890,
      "deviceList": "ALL",
      "enable": true
    }
  ],
  "message": "success"
}
```

### Webhook 設定を更新

```powershell
.\.venv\Scripts\python.exe .\webhook_Switchbot.py update-webhook --url "YOUR_GAS_WEB_APP_URL"
```

指定 URL の Webhook を有効にする設定を SwitchBot API に送ります。`--url` を省略した場合は `.env` の `GAS_URL` を使用します。

### Webhook を削除

```powershell
.\.venv\Scripts\python.exe .\webhook_Switchbot.py delete-webhook --url "YOUR_GAS_WEB_APP_URL"
```

SwitchBot アカウントから指定 URL の Webhook 設定を削除します。削除後、その URL へイベントは送られません。意図した URL であることを確認してから実行してください。`--url` を省略した場合は `.env` の `GAS_URL` を使用します。

## レスポンスとエラー

SwitchBot API の正常レスポンスは通常、次の形式です。

```json
{
  "statusCode": 100,
  "body": {},
  "message": "success"
}
```

- `statusCode: 100`: API 操作成功
- `body`: 操作の結果。コマンドにより URL 一覧、Webhook 詳細、デバイス情報などが入ります
- `message`: API が返すメッセージ

API が `statusCode` 100 以外を返した場合、または HTTP 通信・JSON 解析に失敗した場合、スクリプトはエラーを表示して終了コード `1` で終了します。エラー時には Token / Secret の設定、ネットワーク、指定 URL / Device ID を確認してください。

`query-webhook` が `statusCode: 190` と空の `body` / `message` を返す場合は成功ではありません。その応答だけでは原因を特定できないため、Webhook URL の登録状態、SwitchBot API の状態を確認し、時間をおいて再試行してください。

## セキュリティ

- `.env` に実際の SwitchBot Open Token / Secret Key を設定し、公開しないでください。
- GAS の実デプロイ URL は公開しないでください。
- `deviceList.json` は実デバイス情報を含むため公開しないでください。
- `.gitignore` は今後の Git 追加を防ぐ設定です。過去に GitHub へ push 済みのファイルや履歴からは自動で削除されません。

## 参考

- [SwitchBot API 仕様](https://github.com/OpenWonderLabs/SwitchBotAPI)
