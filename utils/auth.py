import pandas as pd

USERS_PATH = "data/users.csv"

def authenticate(username, password):
    users = pd.read_csv(USERS_PATH)

    user = users[users["username"] == username]

    if user.empty:
        return None

    # Plain-text password check
    if user.iloc[0]["password"] == password:
        return {
            "user_id": user.iloc[0]["user_id"],
            "username": user.iloc[0]["username"],
            "role": user.iloc[0]["role"],
            "faculty_id": user.iloc[0]["faculty_id"],
            "section_id": user.iloc[0]["section_id"]
        }

    return None
