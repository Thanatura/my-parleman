# ParlemAN

# Setup du projet

1. Installer [uv](https://docs.astral.sh/uv/getting-started/installation/)
2. Synchroniser les dépendances avec `uv sync`
3. Installer le hook de pre-commit avec `uv run pre-commit install` et `uv run pre-commit autoupdate`

# Structure du projet


│
├── infra/                      # Terraform (infrastructure)
│   ├── main.tf
│   └── variables.tf
│  
├── flows/                      # Prefect flows
│   ├── api_to_gcs_flow.py
│   └── tasks/
│       ├── fetch_api.py
│       └── upload_gcs.py
│
├── config/
│   ├── settings.yaml
│   └── secrets.env
│
├── scripts/                    # scripts utilitaires
│   └── run_flow.py
│
├── lib/                    # librairies utilitaires
│   └── parse_xml.py
│
├── requirements.txt
├── .env
├── .gitignore
└── README.md