# <img src="https://raw.githubusercontent.com/rguixaro/rask-app/main/public/images/logo.svg" alt="Rask" height="28"> Rask API

Serverless REST API powering [rask.rguixaro.dev](https://rask.rguixaro.dev), a URL
shortener built on AWS Lambda and API Gateway.

## Tech Stack

[Python 3.11](https://python.org) |
[Serverless Framework v4](https://www.serverless.com/) |
[AWS Lambda](https://aws.amazon.com/lambda/) +
[API Gateway](https://aws.amazon.com/api-gateway/) |
[MongoDB](https://www.mongodb.com/) | [PyJWT](https://pyjwt.readthedocs.io/) |
[bcrypt](https://pypi.org/project/bcrypt/)

## Endpoints

| Method | Path                 | Description                              |
| ------ | -------------------- | ---------------------------------------- |
| `POST` | `/auth`              | Create or refresh a cookie-based session |
| `POST` | `/link-create`       | Create a new short link                  |
| `GET`  | `/link-check/{slug}` | Resolve a slug and increment visit count |
| `GET`  | `/links-list`        | List all links for the current session   |

## Getting Started

<details>
<summary>Prerequisites and setup</summary>

### Prerequisites

- Node.js 20+
- Python 3.11
- AWS account with appropriate IAM permissions
- MongoDB instance

### Setup

1. Clone the repository and install dependencies:

    ```bash
    git clone https://github.com/rguixaro/rask-api.git
    cd rask-api
    npm install
    pip install -r requirements.txt
    ```

2. Copy the environment template and fill in the values:

    ```bash
    cp .env.template .env.local
    ```

    | Variable         | Description                                        |
    | ---------------- | -------------------------------------------------- |
    | `DB_URL`         | MongoDB connection string                          |
    | `ENCRYPTION_KEY` | Secret key used for JWT signing                    |
    | `CORS_ORIGIN`    | Allowed CORS origin (e.g. `http://localhost:3000`) |
    | `COOKIE_DOMAIN`  | Cookie domain (e.g. `localhost`)                   |

3. Deploy to AWS:

    ```bash
    npm run deploy
    ```

</details>

## Testing

Unit tests run automatically on every push to `main` via
[GitHub Actions](.github/workflows/deploy.yml) and block deployment on failure.

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

## CI/CD

Deploys to AWS on every push to `main` using OIDC authentication, no stored AWS
credentials. Required GitHub Secrets:

| Secret           | Description               |
| ---------------- | ------------------------- |
| `AWS_ACCOUNT_ID` | AWS account ID            |
| `DB_URL`         | MongoDB connection string |
| `ENCRYPTION_KEY` | JWT signing key           |
| `CORS_ORIGIN`    | Allowed CORS origin       |
| `COOKIE_DOMAIN`  | Cookie domain             |

## License

[GPL-3.0](./LICENSE)
