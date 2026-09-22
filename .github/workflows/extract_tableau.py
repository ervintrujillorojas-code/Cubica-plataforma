import json
import os
from pathlib import Path

import tableauserverclient as TSC

CONFIG_PATH = Path(__file__).parent / "config" / "tableau_config.json"

# Nombre del workbook y de la vista que se quiere extraer.
# Si se dejan vacíos, el script lista todas las vistas disponibles con su ID.
WORKBOOK_NAME = "Agenda picking plataforma / ERVIN"
VIEW_NAME = "Detalle"
VIEW_ID = "78416af1-88e5-411f-8611-eed016ced86e"  # visto en el workbook, evita ambiguedad de nombre

OUTPUT_DIR = Path(__file__).parent / "data"
OUTPUT_DIR.mkdir(exist_ok=True)


def load_config() -> dict:
    # En GitHub Actions el PAT llega por variables de entorno (GitHub Secrets);
    # en local se sigue leyendo config/tableau_config.json.
    if os.environ.get("TABLEAU_TOKEN_SECRET"):
        return {
            "server_url": os.environ.get("TABLEAU_SERVER_URL", "https://elena.mueblesjamar.com.co"),
            "site_name": os.environ.get("TABLEAU_SITE_NAME", ""),
            "token_name": os.environ["TABLEAU_TOKEN_NAME"],
            "token_secret": os.environ["TABLEAU_TOKEN_SECRET"],
        }
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    config = load_config()

    tableau_auth = TSC.PersonalAccessTokenAuth(
        token_name=config["token_name"],
        personal_access_token=config["token_secret"],
        site_id=config["site_name"],
    )
    server = TSC.Server(config["server_url"], use_server_version=True)

    with server.auth.sign_in(tableau_auth):
        if VIEW_ID:
            target_view = server.views.get_by_id(VIEW_ID)
        else:
            all_views, _ = server.views.get()

            if not WORKBOOK_NAME and not VIEW_NAME:
                print("Vistas disponibles en el servidor:")
                for view in all_views:
                    print(f"- workbook: {view.workbook_id} | vista: {view.name} (id: {view.id})")
                return

            target_view = None
            for view in all_views:
                if VIEW_NAME and view.name == VIEW_NAME:
                    target_view = view
                    break

        if target_view is None:
            raise SystemExit(f"No se encontró la vista '{VIEW_NAME}'. Revisa el nombre exacto.")

        server.views.populate_csv(target_view)
        csv_bytes = b"".join(target_view.csv)

        output_file = OUTPUT_DIR / f"{VIEW_NAME}.csv"
        with open(output_file, "wb") as f:
            f.write(csv_bytes)

        print(f"Datos extraídos correctamente en: {output_file}")


if __name__ == "__main__":
    main()
