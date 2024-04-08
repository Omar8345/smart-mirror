# Imports.
from io import BytesIO
import tkinter as tk
from tkinter import font
from PIL import Image, ImageTk
import requests
import geocoder
import time
import json


# The SmartMirror class for the main application.
class SmartMirror(tk.Tk):
    def __init__(self) -> None:
        tk.Tk.__init__(self)

        self.debug = True
        self.attributes("-fullscreen", True)
        self.configure(background="black")
        self.wm_attributes("-alpha", 0.9)  # Adjust transparency for a modern look
        self.wm_attributes("-topmost", True)
        self.title("Smart Mirror")
        self.time = ""
        self.date = ""
        self.weather = ""
        self.weather_icon_url = ""
        self.latitude = geocoder.ip("me").latlng[0]
        self.longitude = geocoder.ip("me").latlng[1]
        self.city = geocoder.ip("me").city
        self.news = ""
        self.create_widgets()
        self.update_clock()
        self.update_weather()
        self.update_news()

    def create_widgets(self) -> None:
        """
        Create the widgets for the Smart Mirror
        """

        self.canvas = tk.Canvas(self, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        time_label_font = font.Font(family="Helvetica Neue", size=72, weight="bold")
        self.time_label = tk.Label(
            self.canvas, font=time_label_font, fg="white", bg="black"
        )
        self.time_label.pack(side="top", anchor="nw", padx=50, pady=50)

        self.date_label = tk.Label(
            self.canvas, font=("Helvetica Neue", 36), fg="white", bg="black"
        )
        self.date_label.pack(side="top", anchor="nw", padx=50)

        self.weather_frame = tk.Frame(self.canvas, bg="black")
        self.weather_frame.pack(side="top", anchor="ne", padx=50, pady=50)

        self.weather_icon_label = tk.Label(self.weather_frame, bg="black")
        self.weather_icon_label.pack(side="left", padx=10)

        self.weather_temp_label = tk.Label(
            self.weather_frame, font=("Helvetica Neue", 24), fg="white", bg="black"
        )
        self.weather_temp_label.pack(side="left")

        self.weather_desc_label = tk.Label(
            self.weather_frame, font=("Helvetica Neue", 24), fg="white", bg="black"
        )
        self.weather_desc_label.pack(side="left", padx=(0, 10))

        self.weather_table_frame = tk.Frame(self.canvas, bg="black")
        self.weather_table_frame.pack(side="top", anchor="ne", padx=50, pady=(0, 20))

        self.news_label = tk.Label(
            self.canvas,
            font=("Helvetica Neue", 22),
            fg="white",
            bg="black",
            wraplength=1000,
        )
        self.news_label.pack(side="top", anchor="nw", padx=50)

    def update_clock(self) -> None:
        """
        Updates the on-screen clock
        """

        now = time.localtime()
        self.time = time.strftime("%I:%M %p", now)
        self.date = time.strftime("%A, %B %d", now)
        self.time_label.config(text=self.time)
        self.date_label.config(text=self.date)
        self.after(1000, self.update_clock)

    def update_weather(self) -> None:
        """
        Updates the weather information
        """

        query = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "daily": "weather_code,temperature_2m_max,temperature_2m_min",
            "current": "temperature_2m,is_day,weather_code",
        }
        res = requests.get("https://api.open-meteo.com/v1/forecast", params=query)

        if res.ok:
            data = res.json()
            weather_code = data["current"]["weather_code"]
            is_day = data["current"]["is_day"] == 1
            current_temperature = round(data["current"]["temperature_2m"])

            weather_data = self.get_weather_data(weather_code, is_day)
            self.weather_icon_url = weather_data["icon"]
            self.weather_temp_label.config(text=f"{current_temperature}°C")
            self.weather_desc_label.config(text=weather_data["description"])
            self.display_weather_icons(data["daily"])

            if self.debug:
                print(f"Feels like: {current_temperature}°C")

        else:
            self.weather = "Unable to get weather information"
            if self.debug:
                print("Unable to get weather information")
                print(res.json())

            self.weather_temp_label.config(text=self.weather)
            self.after(60000, self.update_weather)

        self.after(60000, self.update_weather)

    def get_weather_data(self, weather_code: int, is_day: bool) -> dict:
        """
        Get weather description and icon URL based on weather code and day/night
        """

        with open("weather.json", "r") as f:
            weather_data = json.load(f)

        weather_code_str = str(weather_code)

        time_of_day = "night"
        if is_day:
            time_of_day = "day"            

        if weather_code_str in weather_data:
            return {
                "description": weather_data[weather_code_str][time_of_day][
                    "description"
                ],
                "icon": weather_data[weather_code_str][time_of_day]["image"],
            }
        else:
            print(f"Invalid weather code: {weather_code_str}")
            return {"description": "Unknown", "icon": ""}

    def display_weather_icons(self, daily_data: dict) -> None:
        """
        Display weather icons in the table for the next 6 days
        """

        for i, day_data in enumerate(
            daily_data["weather_code"][1:7]
        ):  # Skip the first day (today)
            icon_code = day_data
            avg_temperature = (
                daily_data["temperature_2m_max"][i + 1]
                + daily_data["temperature_2m_min"][i + 1]
            ) / 2

            icon_url = self.get_icon_url(icon_code)

            icon_label = tk.Label(self.weather_table_frame, bg="black")
            icon_label.grid(row=0, column=i, padx=(0, 10))
            self.load_weather_icon(icon_url, icon_label)

            temp_label = tk.Label(
                self.weather_table_frame,
                text=f"{round(avg_temperature)}°C",
                font=("Helvetica Neue", 12),
                fg="white",
                bg="black",
            )
            temp_label.grid(row=1, column=i, pady=(5, 0))

    def load_weather_icon(self, icon_url: str, label: tk.Label):
        """
        Load weather icon from URL and display it in the given label
        """

        try:
            response = requests.get(icon_url)
            response.raise_for_status()

            if response.status_code == 200:
                img = Image.open(BytesIO(response.content))
                img = img.resize((50, 50), Image.LANCZOS)
                img = ImageTk.PhotoImage(img)
                label.config(image=img)
                label.image = img
            else:
                print(
                    f"Failed to load weather icon from URL: {icon_url}. HTTP status code: {response.status_code}"
                )
        except requests.exceptions.RequestException as e:
            print(f"Error loading weather icon from URL: {icon_url}. Exception: {e}")

    def get_icon_url(self, icon_code: int) -> str:
        """
        Get the appropriate icon URL based on the weather code
        """

        with open("weather.json", "r") as f:
            weather_data = json.load(f)

        icon_code_str = str(icon_code)

        if icon_code_str in weather_data:
            return weather_data[icon_code_str]["day"]["image"]
        else:
            print(f"Invalid weather code: {icon_code_str}")
            return ""

    def update_news(self) -> None:
        """
        Fetches the latest news using an API.
        """

        self.news = "News: A new study finds that people who sleep longer live longer"
        self.news_label.config(text=self.news)
        self.after(60000, self.update_news)


# Create an instance of SmartMirror
app = SmartMirror()
# Start the application loop
app.mainloop()
