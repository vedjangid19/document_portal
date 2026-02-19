from importlib.metadata import version, PackageNotFoundError

packages = [
    "langchain",
    "python-dotenv",
    "ipykernel",
    "langchain_groq",
    "langchain_google_genai",
    "langchain-community",
    "faiss-cpu",
    "structlog",
    "PyMuPDF",
    "pylint",
    "langchain-core",
    "pytest",
    "streamlit",
    "fastapi",
    "uvicorn",
    "python-multipart",
    "docx2txt"
]

for pkg in packages:
    try:
        pkg_version = version(pkg)
        print(f"{pkg}=={pkg_version}")
    except PackageNotFoundError:
        pkg_version = "not installed"
        print(f"{pkg} ({pkg_version})")