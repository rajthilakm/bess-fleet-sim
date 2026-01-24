# Battery Fleet Simulator

A modular simulation engine for optimizing battery fleet dispatch, complete with an interactive dashboard and containerization support.

## Features
- **Core Engine**: Detailed battery physics, efficiency losses, and revenue tracking.
- **Optimization**: Threshold-based strategy (Charge at low prices, Discharge at peaks).
- **Interactive Dashboard**:
  - Fleet Overview & Financial Analysis.
  - Drill-down "Individual Analysis" for specific assets.
  - Visualizations: Dispatch logic, SoE curves, Revenue accumulation.
- **Project Structure**: Modular design (`sim_engine` package) with clear entry points (`app.py`, `cli.py`).
- **Deployment**: Dockerized for easy distribution.

## Setup

### Option A: Local Python Environment
1.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Configure**:
    -   Assets & Limits: `config/batteries.yaml`
    -   Env Vars: `config/.env`

### Option B: Docker
1.  **Build**:
    ```bash
    docker compose build
    ```

## Usage

### 1. Interactive Dashboard (Streamlit)
**Local**:
```bash
streamlit run app.py
```
**Docker**:
```bash
docker compose up
```
Access the dashboard at `http://localhost:8501`.

### 2. Command Line Simulation
Run the simulation headless and generate `results.csv`:
```bash
python cli.py
```

### 3. Running Tests
```bash
pytest tests/
```

## Configuration
**`config/batteries.yaml`**:
-   **`fleet_global`**: Set system-wide constraints (`max_charge_mw`).
-   **`batteries`**: Define individual assets (`capacity`, `efficiency`, `initial_soe`).

**`config/.env`**:
-   **`MARKET_RESOLUTION`**: Time step (e.g., `60min`).
-   **`TIMEZONE`**, `LOG_LEVEL`.
