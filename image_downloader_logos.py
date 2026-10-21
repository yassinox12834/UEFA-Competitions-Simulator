"""This is the code I used to download the clubs' logos using the `requests` module and the club IDs within the API."""



import os
import tkinter as tk
from requests import get


class App(tk.Tk):                           

    def __init__(self):
        super().__init__()
        self.title("Club Logo Downloader")
        self.geometry("500x160")
        self.minsize(500, 160)
        self.maxsize(500, 160)

        # Dossier de sauvegarde
        self.save_dir = os.path.join("assets", "images", "optional", "Eustral")

        # Interface graphique
        self.label = tk.Label(self, text="Enter club ID:")
        self.label.pack(pady=(15, 2))

        self.text_box = tk.Entry(self, width=40)
        self.text_box.pack(pady=5)
        self.text_box.bind("<Return>", self.download_logo)
        self.text_box.focus()

        self.button = tk.Button(
            self, text="Download logo", command=self.download_logo
        )
        self.button.pack(pady=5)

        self.status = tk.Label(self, text="", fg="gray")
        self.status.pack(pady=5)

    def download_logo(self, event=None):
        club_ids = self.text_box.get().strip()

        club_ids = [club_id.strip() for club_id in club_ids.split(";")]

        for club_id in club_ids:
            if not club_id.isdigit():
                self.status.config(
                    text=f"Invalid club ID     :     {club_id}",
                    fg="red"
                )
                return

        self.status.config(text="Downloading...", fg="orange")
        self.update_idletasks()

        os.makedirs(self.save_dir, exist_ok=True)

        for club_id in club_ids:

            url = f"https://media.api-sports.io/football/teams/{club_id}.png"

            try:
                response = get(url, timeout=5)

                if response.status_code != 200 or "image" not in response.headers.get(
                    "Content-Type", ""
                ):
                    self.status.config(
                        text=f"No logo found for ID {club_id}.",
                        fg="red"
                    )
                    continue

                filepath = os.path.join(
                    self.save_dir,
                    f"{club_id}.png"
                )

                with open(filepath, "wb") as f:
                    f.write(response.content)

            except Exception as e:
                self.status.config(
                    text=f"Network error for {club_id}: {e}",
                    fg="red"
                )
                continue

        self.status.config(
            text=f"Downloaded {len(club_ids)} logo(s).",
            fg="green"
        )

# 52 ; 
if __name__ == "__main__":
    App().mainloop()
