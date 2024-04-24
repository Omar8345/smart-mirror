## Font used
- Futura

## Required environment variables

- `DEBUG` (bool): Enable debug mode. Default: `False`
- `USERNAME` (str): Username for the Smart Mirror. Default: `User`
- `ENABLE_ASSISTANT` (bool): Enable Google Assistant. Default: `True`
- `CREDENTIALS_PATH` (str): Path to the Google Assistant credentials file. Default: `~/.config/google-oauthlib-tool/credentials.json`
- `ASSISTANT_TRIGGER` (bool): Enable Google Assistant trigger word. Default: `True`

## Configuration

1. Setup Python virtual environment and install requirements:

```bash
# Create new environment file from existing .env.sample
$ cp .env.sample .env

# Setup python virtual environment and activate it
$ python -m venv venv
$ source venv/bin/activate

# Install requirements
$ pip install -r requirements.txt
$ sudo apt-get install portaudio19-dev libffi-dev libssl-dev # Optional for Google Assistant
```

2. Follow the steps to [configure the Actions Console project and the Google account](https://developers.google.com/assistant/sdk/guides/service/python/embed/config-dev-project-and-account). *(optional)*

3. Follow the steps to [register a new device model and download the client secrets file](https://developers.google.com/assistant/sdk/guides/service/python/embed/register-device). *(optional)*

4. Generate device credentials using `google-oauthlib-tool`: *(optional)*

```bash
google-oauthlib-tool --client-secrets path/to/client_secret<client-id>.json --scope https://www.googleapis.com/auth/assistant-sdk-prototype --save
```

5. Run the code:

```bash
python main.py
```

## Possible Issues

- `AttributeError: 'array.array' object has no attribute 'tostring'`:
  - Solution: Go to the file where you get this error, its called `audio_helpers` which is part of the Google Assistant SDK. Replace the `tostring()` method with `tobytes()` at line 57.

- `from tenacity.async import AsyncRetrying` *(`SyntaxError: invalid syntax`):*
    - Solution: Upgrade the `tenacity` package to the latest version.
        ```bash
        pip install --upgrade tenacity
        ```
    
- `TypeError: Descriptors cannot be created directly.`:
    ```
    If this call came from a _pb2.py file, your generated code is out of date and must be regenerated with protoc >= 3.19.0.
    If you cannot immediately regenerate your protos, some other possible workarounds are:
    1. Downgrade the protobuf package to 3.20.x or lower.
    2. Set PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python (but this will use pure-Python parsing and will be much slower).
   ```
   - Solution: Downgrade the `protobuf` package to version `3.20.x` or lower.
        ```bash
        pip install protobuf==3.20.0
        ```