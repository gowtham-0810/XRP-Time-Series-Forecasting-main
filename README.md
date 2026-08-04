# XRP-Time-Series-Forecasting

## 🚀 Deployed Link

1. [Streamlit Community Cloud](https://xrp-forecast.streamlit.app/)
2. [FastAPI hosting the ML Model](https://fastapi-25548684-at3-latest.onrender.com/)

---

## Overview

This project is a **Streamlit web application** which predicts the high prices for the Cryptocurrency Ripple (XRP) for users interested in investing in cryptocurrencies. It uses Python 3.11.4 (managed via `pyenv`), Streamlit, Plotly, and other dependencies managed via Poetry.

---

## Prerequisites

- [pyenv](https://github.com/pyenv/pyenv) for managing Python versions
- Python 3.11.4 (installed via pyenv)
- [Poetry](https://python-poetry.org/) for dependency management
- Docker (optional, for containerized deployment)

---

## Setup (Local Environment with Poetry)

1. **Clone the GitHub Repo**

```bash
git clone https://github.com/Sidsuresh/XRP-Time-Series-Forecasting.git
cd XRP_Forecast
```

2. **Install the correct Python version with pyenv**

```bash
pyenv install 3.11.4
pyenv local 3.11.4
```

3. **Install Poetry and the dependencies provided**

```bash
poetry install
```

4. **Run the Streamlit app inside Poetry**

```bash
poetry run streamlit run app/main.py
```

The app will start locally [here](http://localhost:8501)

---

