FROM python:3.11-slim

RUN apt-get update &&     apt-get install -y curl &&     curl -LsSf https://astral.sh/uv/install.sh | sh &&     mv /root/.local/bin/uv /usr/local/bin/ &&     mv /root/.local/bin/uvx /usr/local/bin/

CMD ["uv", "--version"]
