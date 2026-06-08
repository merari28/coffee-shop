# Coffee Shop — E2E Portfolio Walkthrough

End-to-end browser walkthrough of the **Coffee Shop** Django app, built with
[Playwright](https://playwright.dev/python/). The script
[`run_e2e.py`](./run_e2e.py) drives a real Chromium browser through every screen
— public, authenticated customer and admin panel — running the real flows
(login, add-to-cart, checkout, confirmation) and saving one **full-page,
retina-quality** screenshot per screen into [`screenshots/`](./screenshots).

> Screenshots are taken at a 1440 px viewport with `device_scale_factor=2`
> (≈2880 px wide PNGs).

## Demo credentials

| Role     | User      | Password       |
|----------|-----------|----------------|
| Admin    | `admin`   | `admin1234`    |
| Customer | `cliente` | `cliente1234`  |

Both users are active. The customer ships with one confirmed order and a live
cart (Latte + Mocha) so the screens are never empty.

## Screen index

| #  | File                              | Screen                                            |
|----|-----------------------------------|---------------------------------------------------|
| 01 | `01_menu_publico.png`             | Public landing / menu (hero + product grid)       |
| 02 | `02_registro.png`                 | Sign-up form                                       |
| 03 | `03_login.png`                    | Login form                                         |
| 04 | `04_menu_autenticado.png`         | Menu as a logged-in customer (avatar in navbar)   |
| 05 | `05_mi_pedido.png`                | Cart / "Mi pedido" with line items and total      |
| 06 | `06_producto_agregado.png`        | Cart after adding a product (success flash)        |
| 07 | `07_pedido_confirmado.png`        | Order confirmation screen                          |
| 08 | `08_admin_dashboard.png`          | Django admin dashboard                             |
| 09 | `09_admin_productos.png`          | Admin — product list                               |
| 10 | `10_admin_producto_detalle.png`   | Admin — product change form                        |
| 11 | `11_admin_pedidos.png`            | Admin — orders                                     |
| 12 | `12_admin_usuarios.png`           | Admin — users (with profile inline)                |
| 13 | `13_api_productos_json.png`       | REST API — `/productos/api/` (DRF browsable)       |

## Reproduce

From the project root:

```bash
# 1. Environment + dependencies (one-time)
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-dev.txt
venv\Scripts\python.exe -m playwright install chromium

# 2. Database + demo data (downloads real images; needs internet)
venv\Scripts\python.exe manage.py migrate
venv\Scripts\python.exe manage.py seed_demo --flush

# 3. Run the server (any free port)
venv\Scripts\python.exe manage.py runserver 127.0.0.1:8020

# 4. In another terminal: run the walkthrough
venv\Scripts\python.exe e2e_portfolio/run_e2e.py --base-url http://127.0.0.1:8020
```

The script re-creates all screenshots in `screenshots/` on every run.

> Note: running the walkthrough performs a real checkout, which empties the
> customer's cart. Re-run `manage.py seed_demo --flush` afterwards to restore the
> populated demo state.
