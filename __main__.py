from src.rpg_game import PysoRealm

if __name__ == "__main__":
    with PysoRealm() as realm:
        realm.run_game_loop()
