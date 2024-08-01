from db.locale_config import default as locale

def get_locale(entry: str) -> str:
    try:
        return locale[entry]
    except KeyError:
        print(f"No entry: {entry}")
        return ''