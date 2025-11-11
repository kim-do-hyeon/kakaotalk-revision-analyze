## KakaoTalk Modified Messages Extractor

This tool scans KakaoTalk chat databases for modified messages and lists the original content and each revision.
It supports both Android and iOS database formats.

### Features
- iOS
  - Reads the `Message` table.
  - Decrypts `message` (original) and each `extraInfo.modifyHistory.message` (revisions).
- Android
  - Reads the `chat_logs` table.
  - Decrypts `v.message` (if present) and each entry inside `v.modifyLog` as revisions.

### Requirements
- Python 3.8+
- pycryptodome
  ```bash
  pip install pycryptodome
  ```

### Important: Set Keys Before Use
You must set encryption keys in the core modules before running.

- Android PKCS flow (encType-based):
  - Edit `resource/android_core.py` and replace values marked as `INPUT YOUR KEY/IV`:
    - `_KEY`
    - `_IV`
    - `_derive_aes_key.base_key`
    - `_derive_aes_key.iv`

- iOS HMAC flow:
  - Edit `resource/ios_core.py` and set:
    - `key`
    - `iv`

Without valid keys, decryption will fail or produce incorrect results.

### Usage
Run the unified CLI with `run.py`:

- iOS (Message DB):
  ```bash
  python run.py --platform ios --db /path/to/ios.sqlite
  ```

- Android (Chat DB):
  ```bash
  python run.py --platform android --db /path/to/android.sqlite
  ```

### Output Format
- iOS
```
id = <row-id> / 노출 메시지 : <decrypted original>

--------------------------------

수정 <n> : <decrypted revision n>

--------------------------------
```

- Android
```
id = <row-id> / 노출 메시지 : <decrypted original>

--------------------------------

수정 <n> : <decrypted revision n>

--------------------------------
```

### Examples

- iOS example:
```
id = 3 / 노출 메시지 : 나 1만원만 한국은행 1234-5678-90 으로 보내주라

--------------------------------

수정 1 : 나 10만원만 한국은행 1234-5678-90 으로 보내주라

수정 2 : 나 50만원만 한국은행 1234-5678-90 으로 보내주라

--------------------------------
```

- Android example:
```
id = 27 / 노출 메시지 : 1만원만 한국은행 1234-5678-90으로 보내줘

--------------------------------

수정 1 : 10만원만 한국은행 1234-5678-90으로 보내줘

--------------------------------
```

### Notes
- Some databases store `modifyLog` as a JSON-encoded string; the tool handles both string and array forms.
- For iOS, revisions are indicated by `extraInfo.modifyHistory` with `encrypted: true` when ciphertext is present.
- If decryption fails for an entry, it will be reported as `(decrypt failed)`.
